"""
Edward Speech-to-Text Module
Converts speech to text using speech_recognition library
"""

from typing import Optional, Callable
import threading
import speech_recognition as sr
from pathlib import Path
import tempfile
import wave

from config import STT_MODEL
from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class EdwardSTT:
    """
    Speech-to-Text engine using Google Speech Recognition.
    Converts audio to text for voice commands.
    """
    
    def __init__(self):
        """Initialize STT engine."""
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        
        # Adjust for ambient noise on first use
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                logger.info("Calibrating for ambient noise... Please wait.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Edward STT initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize microphone: {e}")
            self.microphone = None
    
    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listen for a single phrase and transcribe it.
        
        Args:
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for the phrase
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.microphone:
            logger.error("Microphone not available")
            return None
        
        try:
            logger.info("Listening for speech...")
            
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            logger.info("Processing speech...")
            
            # Transcribe using Google Speech Recognition
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Transcribed: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.warning("Listening timed out - no speech detected")
            return None
        except sr.UnknownValueError:
            logger.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def listen_once_async(self, callback: Callable[[Optional[str]], None],
                         timeout: int = 5, phrase_time_limit: int = 10):
        """
        Listen for speech asynchronously.
        
        Args:
            callback: Function to call with transcribed text
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Maximum seconds for the phrase
        """
        def _listen_thread():
            text = self.listen_once(timeout, phrase_time_limit)
            callback(text)
        
        thread = threading.Thread(target=_listen_thread, daemon=True)
        thread.start()
        logger.info("Async listening started")
    
    def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_path: Path to audio file (WAV format)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            logger.info(f"Transcribing audio file: {audio_path}")
            
            with sr.AudioFile(audio_path) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Transcription complete: {text[:50]}...")
            return text
            
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return None


# Singleton instance
_stt_instance: Optional[EdwardSTT] = None


def get_stt() -> EdwardSTT:
    """
    Get or create singleton STT instance.
    
    Returns:
        EdwardSTT instance
    """
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = EdwardSTT()
    return _stt_instance


# Example usage
if __name__ == "__main__":
    stt = EdwardSTT()
    
    print("Testing microphone... Speak something!")
    text = stt.listen_once(timeout=5, phrase_time_limit=10)
    
    if text:
        print(f"You said: {text}")
    else:
        print("No speech detected or error occurred")

# Made with Bob
