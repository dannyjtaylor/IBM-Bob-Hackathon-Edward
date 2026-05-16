"""
Edward Text-to-Speech
Primary:  ElevenLabs API (high quality, configured via .env)
Fallback: pyttsx3 (free, offline, no key needed)
"""

import io
import re
import threading
from typing import Optional

from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, TTS_ENABLED
from logger import get_logger

logger = get_logger(__name__)


# ── Text cleaning ─────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "[code block]", text)
    text = re.sub(r"`[^`]+`", "[code]", text)
    text = re.sub(r"https?://\S+", "[link]", text)
    text = re.sub(r"[A-Za-z]:\\\S+", "[path]", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


# ── ElevenLabs backend ────────────────────────────────────────────────────────

class _ElevenLabsBackend:
    """Wraps the installed elevenlabs SDK (supports both 0.2.x and 1.x)."""

    def __init__(self, api_key: str, voice_id: str):
        self._api_key  = api_key
        self._voice_id = voice_id
        self._version  = self._detect_version()
        logger.info(f"ElevenLabs backend — SDK v{self._version}")

    def _detect_version(self) -> str:
        try:
            import elevenlabs
            return getattr(elevenlabs, "__version__", "0.2.x")
        except Exception:
            return "unknown"

    def speak(self, text: str) -> bool:
        try:
            if self._version.startswith("1.") or self._version.startswith("2."):
                return self._speak_v1(text)
            else:
                return self._speak_v0(text)
        except Exception as e:
            logger.error(f"ElevenLabs speak error: {e}")
            return False

    def _speak_v0(self, text: str) -> bool:
        """elevenlabs 0.2.x API"""
        from elevenlabs import generate, stream as el_stream, Voice, VoiceSettings
        import pygame

        audio_gen = generate(
            text=text,
            voice=Voice(
                voice_id=self._voice_id,
                settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True,
                ),
            ),
            model="eleven_monolingual_v1",
            stream=True,
            api_key=self._api_key,
        )
        el_stream(audio_gen)
        return True

    def _speak_v1(self, text: str) -> bool:
        """elevenlabs 1.x / 2.x API"""
        from elevenlabs.client import ElevenLabs
        import pygame

        client = ElevenLabs(api_key=self._api_key)
        audio  = client.generate(
            text=text,
            voice=self._voice_id,
            model="eleven_monolingual_v1",
        )
        # audio is a generator of bytes
        buf = io.BytesIO(b"".join(audio))
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        pygame.mixer.music.load(buf)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            import pygame as _pg
            _pg.time.Clock().tick(10)
        return True


# ── pyttsx3 backend (free, offline) ──────────────────────────────────────────

class _Pyttsx3Backend:
    def __init__(self):
        self._engine = None
        self._lock   = threading.Lock()
        self._setup()

    def _setup(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 185)
            self._engine.setProperty("volume", 0.95)
            # Pick a decent voice if available
            voices = self._engine.getProperty("voices")
            for v in voices:
                if "zira" in v.name.lower() or "david" in v.name.lower():
                    self._engine.setProperty("voice", v.id)
                    break
            logger.info("pyttsx3 backend ready")
        except ImportError:
            logger.info("pyttsx3 not installed — TTS fully disabled")
        except Exception as e:
            logger.warning(f"pyttsx3 init failed: {e}")
            self._engine = None

    @property
    def available(self) -> bool:
        return self._engine is not None

    def speak(self, text: str) -> bool:
        if not self._engine:
            return False
        try:
            with self._lock:
                self._engine.say(text)
                self._engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"pyttsx3 speak error: {e}")
            return False


# ── Main TTS class ────────────────────────────────────────────────────────────

class EdwardTTS:
    """
    Orchestrates TTS backends.
    Prefers ElevenLabs (high quality) → falls back to pyttsx3 (free, offline).
    """

    def __init__(
        self,
        api_key:  Optional[str] = None,
        voice_id: Optional[str] = None,
    ):
        self.api_key  = api_key  or ELEVENLABS_API_KEY
        self.voice_id = voice_id or ELEVENLABS_VOICE_ID
        self.is_enabled = TTS_ENABLED

        self._el_backend: Optional[_ElevenLabsBackend]  = None
        self._py_backend: Optional[_Pyttsx3Backend]     = None
        self._speaking   = False

        if self.api_key and self.voice_id:
            self._el_backend = _ElevenLabsBackend(self.api_key, self.voice_id)
            logger.info("TTS: ElevenLabs primary backend ready")
        else:
            logger.info("TTS: ElevenLabs credentials missing — using pyttsx3 fallback")

        self._py_backend = _Pyttsx3Backend()

        if not self.is_enabled:
            logger.info("TTS disabled in config (TTS_ENABLED=false)")

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str, stream_audio: bool = True, clean_text: bool = True) -> bool:
        if not self.is_enabled or not text.strip():
            return False
        if clean_text:
            text = _clean(text)
        if not text.strip():
            return False

        self._speaking = True
        try:
            # Try ElevenLabs first
            if self._el_backend:
                try:
                    return self._el_backend.speak(text)
                except Exception as e:
                    logger.warning(f"ElevenLabs failed ({e}) — falling back to pyttsx3")

            # Fall back to pyttsx3
            if self._py_backend and self._py_backend.available:
                return self._py_backend.speak(text)

            return False
        finally:
            self._speaking = False

    def speak_async(self, text: str, stream_audio: bool = True, clean_text: bool = True):
        t = threading.Thread(
            target=self.speak,
            args=(text, stream_audio, clean_text),
            daemon=True,
        )
        t.start()

    def stop(self):
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self._speaking = False

    def is_busy(self) -> bool:
        return self._speaking

    def cleanup(self):
        self.stop()
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass


# ── Singleton ─────────────────────────────────────────────────────────────────

_tts_instance: Optional[EdwardTTS] = None


def get_tts() -> EdwardTTS:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = EdwardTTS()
    return _tts_instance


def speak(text: str) -> bool:
    return get_tts().speak(text)


def speak_async(text: str):
    get_tts().speak_async(text)
