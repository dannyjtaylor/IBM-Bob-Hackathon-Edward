"""
Edward Agent Module
Handles global hotkey listening and screenshot capture
"""

import io
import base64
from typing import Callable, Optional
from pynput import keyboard
from mss import mss
from PIL import Image

from config import HOTKEY_ENABLED, HOTKEY_COMBINATION
from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class EdwardAgent:
    """
    Main agent class that listens for hotkey triggers and captures screenshots.
    Triggers the overlay UI when activated.
    """
    
    def __init__(self, on_trigger_callback: Optional[Callable] = None):
        """
        Initialize the Edward agent.
        
        Args:
            on_trigger_callback: Function to call when hotkey is triggered
        """
        self.on_trigger_callback = on_trigger_callback
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self.is_running = False
        
        logger.info("Edward Agent initialized")
    
    def capture_screenshot(self) -> tuple[bytes, str]:
        """
        Capture a screenshot of all monitors and return as bytes and base64.
        
        Returns:
            Tuple of (image_bytes, base64_string)
        """
        try:
            with mss() as sct:
                # Capture all monitors as one screenshot
                monitor = sct.monitors[0]  # Monitor 0 is all monitors combined
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes(
                    "RGB",
                    (screenshot.width, screenshot.height),
                    screenshot.rgb
                )
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG', optimize=True)
                img_bytes = img_byte_arr.getvalue()
                
                # Convert to base64 for API transmission
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                logger.info(f"Screenshot captured: {screenshot.width}x{screenshot.height}")
                return img_bytes, img_base64
                
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            raise
    
    def _on_hotkey_pressed(self):
        """
        Internal callback when hotkey is pressed.
        Captures screenshot and triggers the overlay.
        """
        logger.info("Hotkey triggered: Win+Shift+E")
        
        try:
            # Capture screenshot
            img_bytes, img_base64 = self.capture_screenshot()
            
            # Call the user-provided callback with screenshot data
            if self.on_trigger_callback:
                self.on_trigger_callback(img_bytes, img_base64)
            else:
                logger.warning("No trigger callback registered")
                
        except Exception as e:
            logger.error(f"Error in hotkey handler: {e}")
    
    def start(self):
        """
        Start listening for the global hotkey.
        Non-blocking - runs in background thread.
        """
        if not HOTKEY_ENABLED:
            logger.info("Hotkey is disabled in configuration")
            return
        
        if self.is_running:
            logger.warning("Agent is already running")
            return
        
        try:
            # Create hotkey listener
            # Win+Shift+E = <cmd>+<shift>+e on Windows
            self.listener = keyboard.GlobalHotKeys({
                '<cmd>+<shift>+e': self._on_hotkey_pressed
            })
            
            # Start listening in background thread
            self.listener.start()
            self.is_running = True
            
            logger.info("Edward Agent started - listening for Win+Shift+E")
            
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            raise
    
    def stop(self):
        """
        Stop listening for the global hotkey.
        """
        if not self.is_running:
            return
        
        try:
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            self.is_running = False
            logger.info("Edward Agent stopped")
            
        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


# Example usage
if __name__ == "__main__":
    def test_callback(img_bytes: bytes, img_base64: str):
        """Test callback function"""
        print(f"Screenshot captured! Size: {len(img_bytes)} bytes")
        print(f"Base64 length: {len(img_base64)} characters")
    
    # Create and start agent
    agent = EdwardAgent(on_trigger_callback=test_callback)
    
    try:
        agent.start()
        print("Agent running. Press Win+Shift+E to test. Press Ctrl+C to exit.")
        
        # Keep running until interrupted
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping agent...")
        agent.stop()

# Made with Bob
