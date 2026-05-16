"""
Edward Speech-to-Text
Primary:  faster-whisper (local, no network, low latency)
Fallback: Google STT via speech_recognition

Key latency improvement: custom silence detection stops recording after
~0.4 s of quiet instead of the default 0.8 s, halving perceived lag.
"""

import threading
from typing import Optional, Callable

from config import STT_MODEL
from logger import get_logger

logger = get_logger(__name__)

_RATE          = 16_000   # Hz — Whisper's native sample rate
_CHUNK         = 512      # ~32 ms per chunk
_SILENCE_SECS  = 0.40     # stop after this many seconds of silence
_MIN_SPEECH_MS = 200      # ignore clips shorter than this (ms)


# ── faster-whisper backend ────────────────────────────────────────────────────

class _WhisperBackend:
    """Local Whisper transcription — no network, lowest latency."""

    def __init__(self, model_size: str = "base"):
        self._model_size = model_size
        self._model      = None
        self._threshold  = None   # calibrated RMS noise floor

    def _load(self):
        if self._model is None:
            logger.info(f"Loading faster-whisper '{self._model_size}' (first run downloads ~150 MB)…")
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
            logger.info("faster-whisper ready")
        return self._model

    def _calibrate(self, pa) -> float:
        import pyaudio, numpy as np
        stream = pa.open(format=pyaudio.paInt16, channels=1,
                         rate=_RATE, input=True, frames_per_buffer=_CHUNK)
        frames = []
        for _ in range(int(_RATE / _CHUNK * 0.5)):   # 0.5 s sample
            frames.append(stream.read(_CHUNK, exception_on_overflow=False))
        stream.stop_stream(); stream.close()
        samples = np.frombuffer(b"".join(frames), dtype=np.int16).astype(float)
        rms = float(np.sqrt(np.mean(samples ** 2)))
        threshold = max(rms * 3.0, 150.0)
        logger.info(f"Noise floor RMS={rms:.1f} → threshold={threshold:.1f}")
        return threshold

    def listen_once(self, timeout: int = 8, phrase_time_limit: int = 15) -> Optional[str]:
        try:
            import pyaudio, numpy as np
        except ImportError:
            logger.error("pyaudio / numpy missing — cannot record")
            return None

        pa = pyaudio.PyAudio()
        try:
            if self._threshold is None:
                self._threshold = self._calibrate(pa)
            thr = self._threshold

            stream = pa.open(format=pyaudio.paInt16, channels=1,
                             rate=_RATE, input=True, frames_per_buffer=_CHUNK)

            frames: list[bytes] = []
            silence_chunks   = 0
            max_silence      = int(_RATE / _CHUNK * _SILENCE_SECS)
            max_speech       = int(_RATE / _CHUNK * phrase_time_limit)
            max_wait         = int(_RATE / _CHUNK * timeout)
            waited           = 0
            speech_started   = False

            logger.info("Listening…")
            while True:
                data    = stream.read(_CHUNK, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(float)
                rms     = float(np.sqrt(np.mean(samples ** 2)))

                if rms > thr:
                    speech_started = True
                    silence_chunks = 0
                    frames.append(data)
                    if len(frames) >= max_speech:
                        break
                elif speech_started:
                    frames.append(data)
                    silence_chunks += 1
                    if silence_chunks >= max_silence:
                        break
                else:
                    waited += 1
                    if waited >= max_wait:
                        logger.warning("Listen timeout — no speech detected")
                        return None

            stream.stop_stream(); stream.close()

            if not speech_started:
                return None

            audio = np.frombuffer(b"".join(frames), dtype=np.int16).astype(np.float32) / 32768.0

            # Reject clips that are too short to be a real utterance
            if len(audio) / _RATE * 1000 < _MIN_SPEECH_MS:
                return None

            model = self._load()
            segments, _ = model.transcribe(
                audio, language="en", beam_size=1, vad_filter=True
            )
            text = " ".join(s.text for s in segments).strip()
            logger.info(f"Whisper: {text!r}")
            return text or None

        except Exception as e:
            logger.error(f"WhisperBackend.listen_once: {e}")
            return None
        finally:
            try:
                pa.terminate()
            except Exception:
                pass


# ── Google STT fallback ───────────────────────────────────────────────────────

class _GoogleBackend:
    """Online Google STT via speech_recognition — used only if Whisper fails."""

    def __init__(self):
        import speech_recognition as sr
        self.rec = sr.Recognizer()
        self.rec.pause_threshold        = 0.4   # was default 0.8 — halves latency
        self.rec.non_speaking_duration  = 0.3
        self.rec.dynamic_energy_threshold = True
        self._mic = None
        try:
            self._mic = sr.Microphone()
            with self._mic as source:
                self.rec.adjust_for_ambient_noise(source, duration=0.5)
            logger.info("Google STT calibrated")
        except Exception as e:
            logger.warning(f"Google STT mic init: {e}")

    def listen_once(self, timeout: int = 8, phrase_time_limit: int = 15) -> Optional[str]:
        if not self._mic:
            return None
        import speech_recognition as sr
        try:
            with self._mic as src:
                audio = self.rec.listen(src, timeout=timeout,
                                        phrase_time_limit=phrase_time_limit)
            text = self.rec.recognize_google(audio)
            logger.info(f"Google STT: {text!r}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logger.error(f"Google STT error: {e}")
            return None


# ── Public EdwardSTT class ────────────────────────────────────────────────────

class EdwardSTT:
    """
    Orchestrates STT backends.
    Tries faster-whisper first (local, low-latency), falls back to Google.
    """

    def __init__(self):
        self._whisper: Optional[_WhisperBackend] = None
        self._google:  Optional[_GoogleBackend]  = None

        try:
            import faster_whisper  # noqa
            self._whisper = _WhisperBackend(STT_MODEL or "base")
            logger.info("STT: faster-whisper primary backend")
        except (ImportError, OSError, Exception) as e:
            logger.warning(f"faster-whisper unavailable ({type(e).__name__}) — falling back to Google STT")

        if self._whisper is None:
            try:
                self._google = _GoogleBackend()
            except Exception as e:
                logger.error(f"Google STT also failed: {e}")

    @property
    def microphone(self):
        return True   # kept for API compatibility

    def listen_once(self, timeout: int = 8, phrase_time_limit: int = 15) -> Optional[str]:
        if self._whisper:
            result = self._whisper.listen_once(timeout, phrase_time_limit)
            if result:
                return result
            # Whisper returned None but Google may still help
        if self._google:
            return self._google.listen_once(timeout, phrase_time_limit)
        return None

    def listen_once_async(self,
                          callback: Callable[[Optional[str]], None],
                          timeout: int = 8,
                          phrase_time_limit: int = 15):
        def _run():
            text = self.listen_once(timeout, phrase_time_limit)
            callback(text)
        threading.Thread(target=_run, daemon=True, name="STT").start()


# ── Singleton ─────────────────────────────────────────────────────────────────

_stt_instance: Optional[EdwardSTT] = None


def get_stt() -> EdwardSTT:
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = EdwardSTT()
    return _stt_instance
