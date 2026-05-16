"""
Edward Text-to-Speech — pyttsx3 (offline, no API key needed)
"""

import re
import threading
from typing import Optional

from config import TTS_ENABLED
from logger import get_logger

logger = get_logger(__name__)

# Prefer David (male) then Zira (female); falls back to whatever is first
_PREFERRED_VOICES = ["david", "zira"]


def _clean(text: str) -> str:
    """Strip markdown, action tags, URLs and code blocks before speaking."""
    text = re.sub(r'\[ACTION:[^\]]*\]', '', text)          # [ACTION:...] tags
    text = re.sub(r'```[\s\S]*?```', 'code block', text)   # fenced code
    text = re.sub(r'`[^`]+`', 'code', text)                # inline code
    text = re.sub(r'https?://\S+', 'link', text)           # URLs
    text = re.sub(r'[A-Za-z]:\\\S+', 'path', text)        # Windows paths
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


class EdwardTTS:
    """
    pyttsx3-based TTS — fully offline, no API key, speaks every response.
    Thread-safe: speak() blocks the calling thread; use speak_async() for background.
    """

    def __init__(self):
        self.is_enabled = TTS_ENABLED
        self._engine    = None
        self._lock      = threading.Lock()
        self._speaking  = False
        self._setup()

    def _setup(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate",   175)   # slightly slower = clearer
            engine.setProperty("volume", 1.0)

            voices = engine.getProperty("voices") or []
            chosen = None
            for pref in _PREFERRED_VOICES:
                for v in voices:
                    if pref in v.name.lower():
                        chosen = v
                        break
                if chosen:
                    break
            if chosen is None and voices:
                chosen = voices[0]
            if chosen:
                engine.setProperty("voice", chosen.id)
                logger.info(f"TTS ready — voice: {chosen.name}")
            else:
                logger.info("TTS ready — using system default voice")

            self._engine = engine
        except ImportError:
            logger.warning("pyttsx3 not installed — TTS disabled")
        except Exception as e:
            logger.warning(f"TTS init failed: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str, clean_text: bool = True) -> bool:
        """Speak text synchronously. Blocks until audio finishes."""
        if not self.is_enabled or not self._engine:
            return False
        if clean_text:
            text = _clean(text)
        if not text.strip():
            return False

        with self._lock:
            self._speaking = True
            try:
                self._engine.say(text)
                self._engine.runAndWait()
                return True
            except Exception as e:
                logger.error(f"TTS speak error: {e}")
                return False
            finally:
                self._speaking = False

    def speak_async(self, text: str, clean_text: bool = True, **_kwargs):
        """Speak in a background daemon thread — returns immediately."""
        threading.Thread(
            target=self.speak,
            args=(text,),
            kwargs={"clean_text": clean_text},
            daemon=True,
            name="TTS",
        ).start()

    def stop(self):
        try:
            if self._engine:
                self._engine.stop()
        except Exception:
            pass
        self._speaking = False

    def is_busy(self) -> bool:
        return self._speaking

    def cleanup(self):
        self.stop()


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
