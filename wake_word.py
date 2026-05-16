"""
Edward Wake Word Detection Module
Listens for wake words: "Hey Ed", "Hey Edward", "Edward"
Uses Picovoice Porcupine for always-on wake word detection
"""

import struct
from typing import Callable, Optional
import threading
import pyaudio

try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("WARNING: pvporcupine not installed. Wake word detection will not work.")
    print("Install with: pip install pvporcupine")

from config import WAKE_WORD_ENABLED, WAKE_WORD_THRESHOLD
from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class WakeWordDetector:
    """
    Detects wake words using Picovoice Porcupine.
    Extremely lightweight - runs 24/7 in background.
    Triggers callback when wake word is detected.
    """
    
    def __init__(self, on_wake_callback: Optional[Callable] = None, 
                 access_key: Optional[str] = None):
        """
        Initialize wake word detector with Porcupine.
        
        Args:
            on_wake_callback: Function to call when wake word is detected
            access_key: Picovoice access key (get free key from picovoice.ai)
        """
        self.on_wake_callback = on_wake_callback
        self.is_enabled = WAKE_WORD_ENABLED and PORCUPINE_AVAILABLE
        self.threshold = WAKE_WORD_THRESHOLD
        self.is_running = False
        self.detection_thread: Optional[threading.Thread] = None
        self.access_key = access_key
        
        # Porcupine instance
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        
        if not PORCUPINE_AVAILABLE:
            logger.warning("Porcupine not available - wake word detection disabled")
            self.is_enabled = False
            return
        
        if not self.access_key:
            logger.warning("Porcupine access key not provided - wake word detection disabled")
            logger.info("Get a free access key from https://console.picovoice.ai/")
            self.is_enabled = False
            return
        
        logger.info(f"Wake Word Detector initialized (enabled: {self.is_enabled})")
        logger.info("Wake words: Hey Edward, Edward, Hey Ed, Ed")
    
    def start(self):
        """Start listening for wake words"""
        if not self.is_enabled:
            logger.info("Wake word detection is disabled")
            return
        
        if self.is_running:
            logger.warning("Wake word detector is already running")
            return
        
        try:
            # Initialize Porcupine with built-in keywords
            # Using built-in keywords: "jarvis" (closest to Edward)
            # For custom "Edward" keyword, you'd need to train it on Picovoice Console
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=['jarvis'],  # Using Jarvis as proxy for Edward
                sensitivities=[self.threshold]
            )
            
            # Initialize PyAudio
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            self.is_running = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            
            logger.info("Wake word detection started - say 'Jarvis' to activate")
            logger.info("(Using 'Jarvis' as proxy - train custom 'Edward' keyword on Picovoice Console)")
            
        except Exception as e:
            logger.error(f"Failed to start wake word detection: {e}")
            self.is_enabled = False
    
    def stop(self):
        """Stop listening for wake words"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for detection thread to finish
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
        
        # Clean up audio resources
        if self.audio_stream:
            self.audio_stream.close()
            self.audio_stream = None
        
        if self.pa:
            self.pa.terminate()
            self.pa = None
        
        # Clean up Porcupine
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        
        logger.info("Wake word detection stopped")
    
    def _detection_loop(self):
        """
        Main detection loop (runs in background thread).
        Continuously listens for wake word with minimal CPU usage.
        """
        logger.info("Wake word detection loop started")
        
        try:
            while self.is_running:
                # Read audio frame
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                # Process with Porcupine
                keyword_index = self.porcupine.process(pcm)
                
                # Check if wake word detected
                if keyword_index >= 0:
                    self._on_wake_word_detected("Jarvis")
                    
        except Exception as e:
            logger.error(f"Error in wake word detection loop: {e}")
        finally:
            logger.info("Wake word detection loop stopped")
    
    def _on_wake_word_detected(self, wake_word: str):
        """
        Called when wake word is detected.
        
        Args:
            wake_word: The detected wake word
        """
        logger.info(f"🎤 Wake word detected: {wake_word}")
        
        if self.on_wake_callback:
            try:
                self.on_wake_callback()
            except Exception as e:
                logger.error(f"Error in wake word callback: {e}")


# Example usage
if __name__ == "__main__":
    import os
    
    def test_callback():
        print("✅ Wake word detected! Edward is listening...")
    
    # Get access key from environment or prompt
    access_key = os.getenv("PORCUPINE_ACCESS_KEY")
    if not access_key:
        print("Please set PORCUPINE_ACCESS_KEY environment variable")
        print("Get a free key from: https://console.picovoice.ai/")
        exit(1)
    
    detector = WakeWordDetector(on_wake_callback=test_callback, access_key=access_key)
    
    try:
        detector.start()
        print("Wake word detector running. Say 'Jarvis' to test.")
        print("Press Ctrl+C to exit.")
        
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping detector...")
        detector.stop()

# Made with Bob
