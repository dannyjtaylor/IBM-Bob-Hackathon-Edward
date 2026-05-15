"""
Edward Text-to-Speech Module
ElevenLabs TTS with streaming support for faster audio playback
"""

import io
from typing import Iterator, Optional
from elevenlabs import generate, stream, Voice, VoiceSettings
import pygame

from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, TTS_ENABLED
from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class EdwardTTS:
    """
    Text-to-Speech engine using ElevenLabs API.
    Supports streaming for faster audio playback.
    """
    
    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        """
        Initialize the TTS engine.
        
        Args:
            api_key: ElevenLabs API key (defaults to config)
            voice_id: ElevenLabs voice ID (defaults to config)
        """
        self.api_key = api_key or ELEVENLABS_API_KEY
        self.voice_id = voice_id or ELEVENLABS_VOICE_ID
        self.is_enabled = TTS_ENABLED
        self.is_speaking = False
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        
        # Validate configuration
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
            self.is_enabled = False
        
        if not self.voice_id:
            logger.warning("ElevenLabs voice ID not configured")
            self.is_enabled = False
        
        logger.info(f"Edward TTS initialized (enabled: {self.is_enabled})")
    
    def speak(self, text: str, stream_audio: bool = True) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            stream_audio: If True, stream audio for faster playback
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled:
            logger.warning("TTS is disabled")
            return False
        
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return False
        
        try:
            self.is_speaking = True
            logger.info(f"Speaking: {text[:50]}...")
            
            if stream_audio:
                self._speak_streaming(text)
            else:
                self._speak_complete(text)
            
            self.is_speaking = False
            logger.info("Speech completed")
            return True
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            self.is_speaking = False
            return False
    
    def _speak_streaming(self, text: str):
        """
        Stream audio for faster playback (audio starts before generation completes).
        
        Args:
            text: Text to speak
        """
        try:
            # Generate audio stream
            audio_stream = generate(
                text=text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.0,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_monolingual_v1",
                stream=True,
                api_key=self.api_key
            )
            
            # Stream and play audio chunks
            stream(audio_stream)
            
        except Exception as e:
            logger.error(f"Streaming TTS error: {e}")
            raise
    
    def _speak_complete(self, text: str):
        """
        Generate complete audio before playing (slower but more reliable).
        
        Args:
            text: Text to speak
        """
        try:
            # Generate complete audio
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=self.voice_id,
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.0,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_monolingual_v1",
                stream=False,
                api_key=self.api_key
            )
            
            # Play audio using pygame
            audio_io = io.BytesIO(audio)
            pygame.mixer.music.load(audio_io)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
        except Exception as e:
            logger.error(f"Complete TTS error: {e}")
            raise
    
    def speak_async(self, text: str, stream_audio: bool = True):
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: Text to speak
            stream_audio: If True, stream audio for faster playback
        """
        import threading
        
        def _speak_thread():
            self.speak(text, stream_audio)
        
        thread = threading.Thread(target=_speak_thread, daemon=True)
        thread.start()
        
        logger.info("Async speech started")
    
    def stop(self):
        """Stop current speech playback"""
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            self.is_speaking = False
            logger.info("Speech stopped")
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")
    
    def is_busy(self) -> bool:
        """
        Check if TTS is currently speaking.
        
        Returns:
            True if speaking, False otherwise
        """
        return self.is_speaking or pygame.mixer.music.get_busy()
    
    def set_voice(self, voice_id: str):
        """
        Change the voice ID.
        
        Args:
            voice_id: New ElevenLabs voice ID
        """
        self.voice_id = voice_id
        logger.info(f"Voice changed to: {voice_id}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop()
            pygame.mixer.quit()
            logger.info("TTS cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Singleton instance for easy access
_tts_instance: Optional[EdwardTTS] = None


def get_tts() -> EdwardTTS:
    """
    Get or create the singleton TTS instance.
    
    Returns:
        EdwardTTS instance
    """
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = EdwardTTS()
    return _tts_instance


def speak(text: str, stream_audio: bool = True) -> bool:
    """
    Convenience function to speak text using the singleton instance.
    
    Args:
        text: Text to speak
        stream_audio: If True, stream audio for faster playback
        
    Returns:
        True if successful, False otherwise
    """
    tts = get_tts()
    return tts.speak(text, stream_audio)


def speak_async(text: str, stream_audio: bool = True):
    """
    Convenience function to speak text asynchronously.
    
    Args:
        text: Text to speak
        stream_audio: If True, stream audio for faster playback
    """
    tts = get_tts()
    tts.speak_async(text, stream_audio)


# Example usage
if __name__ == "__main__":
    # Test TTS
    tts = EdwardTTS()
    
    if tts.is_enabled:
        print("Testing TTS with streaming...")
        tts.speak("Hello. I am Edward, your AI assistant. How may I help you today?", stream_audio=True)
        
        print("\nTesting async speech...")
        tts.speak_async("This is an asynchronous test. The program continues while I speak.")
        
        import time
        time.sleep(5)
        
        print("Done!")
    else:
        print("TTS is not enabled. Please configure API key and voice ID in .env file.")

# Made with Bob
