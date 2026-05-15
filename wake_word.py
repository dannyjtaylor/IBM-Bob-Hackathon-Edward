"""
Edward Wake Word Detection Module
Listens for wake words: "Hey Ed", "Hey Edward", "Edward"
"""

import logging
from typing import Callable, Optional
import threading

# TODO: Implement with openwakeword
# from openwakeword import Model

from config import WAKE_WORD_ENABLED, WAKE_WORDS, WAKE_WORD_THRESHOLD

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WakeWordDetector:
    """
    Detects wake words using OpenWakeWord.
    Triggers callback when wake word is detected.
    """
    
    def __init__(self, on_wake_callback: Optional[Callable] = None):
        """
        Initialize wake word detector.
        
        Args:
            on_wake_callback: Function to call when wake word is detected
        """
        self.on_wake_callback = on_wake_callback
        self.is_enabled = WAKE_WORD_ENABLED
        self.wake_words = WAKE_WORDS
        self.threshold = WAKE_WORD_THRESHOLD
        self.is_running = False
        self.detection_thread: Optional[threading.Thread] = None
        
        logger.info(f"Wake Word Detector initialized (enabled: {self.is_enabled})")
        logger.info(f"Wake words: {', '.join(self.wake_words)}")
    
    def start(self):
        """Start listening for wake words"""
        if not self.is_enabled:
            logger.info("Wake word detection is disabled")
            return
        
        if self.is_running:
            logger.warning("Wake word detector is already running")
            return
        
        self.is_running = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        
        logger.info("Wake word detection started")
    
    def stop(self):
        """Stop listening for wake words"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
        
        logger.info("Wake word detection stopped")
    
    def _detection_loop(self):
        """
        Main detection loop (runs in background thread).
        TODO: Implement actual wake word detection with OpenWakeWord.
        """
        logger.info("Wake word detection loop started")
        
        # TODO: Implement actual detection
        # For now, this is a placeholder
        while self.is_running:
            import time
            time.sleep(0.1)
            
            # Placeholder: Actual implementation would:
            # 1. Capture audio from microphone
            # 2. Process with OpenWakeWord model
            # 3. Check if wake word detected above threshold
            # 4. Call on_wake_callback if detected
        
        logger.info("Wake word detection loop stopped")
    
    def _on_wake_word_detected(self, wake_word: str):
        """
        Called when wake word is detected.
        
        Args:
            wake_word: The detected wake word
        """
        logger.info(f"Wake word detected: {wake_word}")
        
        if self.on_wake_callback:
            self.on_wake_callback()


# Example usage
if __name__ == "__main__":
    def test_callback():
        print("Wake word detected!")
    
    detector = WakeWordDetector(on_wake_callback=test_callback)
    
    try:
        detector.start()
        print("Wake word detector running. Press Ctrl+C to exit.")
        
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping detector...")
        detector.stop()

# Made with Bob
