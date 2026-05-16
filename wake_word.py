"""
Edward Wake Word Detection
Free, offline-friendly approach: continuously listens in background using
speech_recognition + Google STT. Triggers when speech contains a wake word.

Optional upgrade: set PORCUPINE_ACCESS_KEY in .env for ultra-low-latency
Porcupine-based detection (uses built-in "jarvis" keyword as proxy).

Callback signature: on_wake_callback(command: Optional[str])
  - command is any text AFTER the wake word in the same utterance
  - command is None if nothing followed the wake word
"""

import os
import re
import threading
import time
from typing import Callable, Optional

from config import WAKE_WORD_ENABLED, WAKE_WORDS
from logger import get_logger

logger = get_logger(__name__)


class WakeWordDetector:
    """
    Background wake-word listener.
    Works without any API key using Google STT polling.
    Hot-swap to Porcupine by setting PORCUPINE_ACCESS_KEY.
    """

    def __init__(
        self,
        on_wake_callback: Optional[Callable[[Optional[str]], None]] = None,
        access_key: Optional[str] = None,
    ):
        self.on_wake_callback = on_wake_callback
        self.is_enabled       = WAKE_WORD_ENABLED
        self.is_running       = False
        self._suppressed      = False   # set True while overlay is open
        self._thread: Optional[threading.Thread] = None

        self._porcupine_key = (
            access_key or os.getenv("PORCUPINE_ACCESS_KEY", "")
        ).strip()
        self._use_porcupine = bool(self._porcupine_key)

        mode = "Porcupine" if self._use_porcupine else "STT-polling"
        logger.info(
            f"WakeWordDetector — mode: {mode}, enabled: {self.is_enabled}, "
            f"words: {WAKE_WORDS}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        if not self.is_enabled or self.is_running:
            return
        self.is_running = True
        target = self._porcupine_loop if self._use_porcupine else self._stt_loop
        self._thread = threading.Thread(target=target, daemon=True, name="WakeWord")
        self._thread.start()
        logger.info("Wake word detection started")

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=4.0)
        logger.info("Wake word detection stopped")

    def suppress(self):
        """Pause detection while the overlay is open (avoids re-triggering)."""
        self._suppressed = True

    def resume(self):
        """Resume detection after the overlay closes."""
        self._suppressed = False

    # ── STT polling loop (no API key needed) ──────────────────────────────────

    def _stt_loop(self):
        try:
            import speech_recognition as sr
        except ImportError:
            logger.error("speech_recognition not installed — wake word disabled")
            return

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.7

        try:
            mic = sr.Microphone()
            with mic as source:
                logger.info("Calibrating microphone for wake word detection…")
                recognizer.adjust_for_ambient_noise(source, duration=0.8)
        except Exception as e:
            logger.error(f"Microphone init failed: {e}")
            return

        def _callback(r: sr.Recognizer, audio: sr.AudioData):
            if not self.is_running or self._suppressed:
                return
            try:
                text = r.recognize_google(audio).lower().strip()
                logger.info(f"Wake poll heard: {text!r}")  # visible so user can see what's heard
                self._check_and_fire(text)
            except sr.UnknownValueError:
                pass  # silence / unintelligible
            except sr.RequestError as e:
                logger.warning(f"STT request error: {e}")

        stop_fn = recognizer.listen_in_background(mic, _callback, phrase_time_limit=4)
        logger.info(f"STT wake word loop active. Say one of: {WAKE_WORDS}")

        while self.is_running:
            time.sleep(0.3)

        stop_fn(wait_for_stop=False)

    # ── Porcupine loop (requires PORCUPINE_ACCESS_KEY) ────────────────────────

    def _porcupine_loop(self):
        try:
            import pvporcupine
            import pyaudio
            import struct
        except ImportError as e:
            logger.warning(f"Porcupine deps missing ({e}) — falling back to STT")
            self._stt_loop()
            return

        porcupine = stream = pa = None
        try:
            porcupine = pvporcupine.create(
                access_key=self._porcupine_key,
                keywords=["jarvis"],
                sensitivities=[0.5],
            )
            pa     = pyaudio.PyAudio()
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
            )
            logger.info("Porcupine active — say 'Jarvis' to wake Edward")

            while self.is_running:
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
                if porcupine.process(pcm) >= 0 and not self._suppressed:
                    logger.info("Porcupine: wake word detected")
                    if self.on_wake_callback:
                        self.on_wake_callback(None)

        except Exception as e:
            logger.error(f"Porcupine loop error: {e}")
        finally:
            for obj, close in [(stream, "close"), (pa, "terminate"), (porcupine, "delete")]:
                try:
                    if obj:
                        getattr(obj, close)()
                except Exception:
                    pass

    # ── Shared: check text and fire callback ──────────────────────────────────

    # Google STT mishears "hey ed" in many ways — cast a wide net
    _PHONETIC_ALIASES = [
        r"hey\s+ed\b",
        r"hey\s+add\b",
        r"hey\s+at\b",
        r"hey\s+ahead\b",
        r"hey\s+a\b",
        r"hey\s+head\b",
        r"hey\s+dead\b",
        r"hey\s+red\b",
        r"hey\s+edward\b",
        r"hey\s+edwood\b",
        r"\bedward\b",
        r"\bed\b(?!\s+(?:a|an|the|is|was|has|have|to|in|on|at|of))",  # "ed" not in sentence
        r"ok\s+ed\b",
        r"okay\s+ed\b",
    ]
    _WAKE_RE = re.compile(
        r"(?:" + "|".join(_PHONETIC_ALIASES) + r")[,\.\s]*(.*)$",
        re.I,
    )

    def _check_and_fire(self, text: str):
        """Check if text contains a wake word, extract trailing command."""
        m = self._WAKE_RE.search(text)
        if m:
            command = m.group(1).strip() or None
            logger.info(f"Wake word matched in {text!r} — command: {command!r}")
            if self.on_wake_callback:
                try:
                    self.on_wake_callback(command)
                except Exception as e:
                    logger.error(f"Wake callback error: {e}")
            return
        # also check config WAKE_WORDS as fallback
        for wake in WAKE_WORDS:
            pattern = re.compile(
                r"(?:^|\b)" + re.escape(wake.lower()) + r"[,\s]*(.*)$",
                re.I,
            )
            m = pattern.search(text)
            if m:
                command = m.group(1).strip() or None
                logger.info(f"Wake word '{wake}' matched — command: {command!r}")
                if self.on_wake_callback:
                    try:
                        self.on_wake_callback(command)
                    except Exception as e:
                        logger.error(f"Wake callback error: {e}")
                return
