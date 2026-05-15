"""
Screenshot Capture Service
Periodically captures screenshots for AI analysis
"""

import asyncio
import base64
import io
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from PIL import Image
import pyautogui

from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class ScreenshotService:
    """
    Service for capturing screenshots at regular intervals.
    """
    
    def __init__(
        self,
        interval: float = 2.0,
        quality: int = 85,
        max_width: Optional[int] = 1920,
        max_height: Optional[int] = 1080
    ):
        """
        Initialize screenshot service.
        
        Args:
            interval: Time between screenshots in seconds
            quality: JPEG quality (1-100)
            max_width: Maximum width for resizing (None for no resize)
            max_height: Maximum height for resizing (None for no resize)
        """
        self.interval = interval
        self.quality = quality
        self.max_width = max_width
        self.max_height = max_height
        
        self.is_running = False
        self.callback: Optional[Callable] = None
        self.task: Optional[asyncio.Task] = None
        
        logger.info(f"Screenshot Service initialized (interval: {interval}s)")
    
    def capture_screenshot(self) -> Dict[str, Any]:
        """
        Capture a single screenshot.
        
        Returns:
            Dictionary with screenshot data
        """
        try:
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Get original dimensions
            original_width, original_height = screenshot.size
            
            # Resize if needed
            if self.max_width or self.max_height:
                screenshot = self._resize_image(screenshot)
            
            # Convert to base64
            buffered = io.BytesIO()
            screenshot.save(buffered, format="JPEG", quality=self.quality)
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            return {
                "success": True,
                "image": img_base64,
                "width": screenshot.width,
                "height": screenshot.height,
                "original_width": original_width,
                "original_height": original_height,
                "timestamp": datetime.utcnow().isoformat(),
                "format": "JPEG",
                "quality": self.quality
            }
            
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            image: PIL Image to resize
            
        Returns:
            Resized image
        """
        width, height = image.size
        
        # Calculate scaling factor
        scale_w = self.max_width / width if self.max_width else 1.0
        scale_h = self.max_height / height if self.max_height else 1.0
        scale = min(scale_w, scale_h, 1.0)  # Don't upscale
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            logger.debug(f"Resizing screenshot from {width}x{height} to {new_width}x{new_height}")
            
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    async def start(self, callback: Callable):
        """
        Start capturing screenshots periodically.
        
        Args:
            callback: Function (sync or async) to call with each screenshot
        """
        if self.is_running:
            logger.warning("Screenshot service already running")
            return
        
        self.is_running = True
        self.callback = callback
        
        logger.info("Starting screenshot capture service")
        
        # Start capture loop
        self.task = asyncio.create_task(self._capture_loop())
    
    async def stop(self):
        """Stop capturing screenshots."""
        if not self.is_running:
            return
        
        logger.info("Stopping screenshot capture service")
        
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
    
    async def _capture_loop(self):
        """Main capture loop."""
        try:
            while self.is_running:
                # Capture screenshot
                screenshot_data = await asyncio.to_thread(self.capture_screenshot)
                
                # Call callback if provided
                if self.callback and screenshot_data.get("success"):
                    try:
                        if asyncio.iscoroutinefunction(self.callback):
                            await self.callback(screenshot_data)
                        else:
                            self.callback(screenshot_data)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                # Wait for next interval
                await asyncio.sleep(self.interval)
                
        except asyncio.CancelledError:
            logger.info("Screenshot capture loop cancelled")
        except Exception as e:
            logger.error(f"Screenshot capture loop error: {e}")
            self.is_running = False
    
    def set_interval(self, interval: float):
        """
        Update capture interval.
        
        Args:
            interval: New interval in seconds
        """
        self.interval = interval
        logger.info(f"Screenshot interval updated to {interval}s")
    
    def set_quality(self, quality: int):
        """
        Update JPEG quality.
        
        Args:
            quality: Quality value (1-100)
        """
        self.quality = max(1, min(100, quality))
        logger.info(f"Screenshot quality updated to {self.quality}")


# Singleton instance
_screenshot_service: Optional[ScreenshotService] = None


def get_screenshot_service(
    interval: float = 2.0,
    quality: int = 85,
    max_width: Optional[int] = 1920,
    max_height: Optional[int] = 1080
) -> ScreenshotService:
    """
    Get or create singleton screenshot service.
    
    Args:
        interval: Time between screenshots in seconds
        quality: JPEG quality (1-100)
        max_width: Maximum width for resizing
        max_height: Maximum height for resizing
        
    Returns:
        ScreenshotService instance
    """
    global _screenshot_service
    
    if _screenshot_service is None:
        _screenshot_service = ScreenshotService(
            interval=interval,
            quality=quality,
            max_width=max_width,
            max_height=max_height
        )
    
    return _screenshot_service


# Made with Bob