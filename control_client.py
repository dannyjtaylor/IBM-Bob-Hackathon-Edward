"""
Edward Computer Control Client
Client for interacting with the Computer Control API
"""

import httpx
from typing import Optional, List, Dict, Any
from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class ComputerControlClient:
    """
    Client for controlling mouse and keyboard through the Computer Control API.
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        """
        Initialize the control client.
        
        Args:
            base_url: Base URL of the Computer Control API
        """
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
        logger.info(f"Computer Control Client initialized: {self.base_url}")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for the request
            
        Returns:
            Response JSON
        """
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    # Mouse Control Methods
    def move_mouse(self, x: int, y: int, duration: float = 0.2) -> Dict[str, Any]:
        """
        Move mouse to specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Duration of movement in seconds
            
        Returns:
            Response data
        """
        logger.info(f"Moving mouse to ({x}, {y})")
        return self._request("POST", "/mouse/move", json={
            "x": x,
            "y": y,
            "duration": duration
        })
    
    def click_mouse(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.0
    ) -> Dict[str, Any]:
        """
        Click mouse at specified coordinates or current position.
        
        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            button: Mouse button ('left', 'right', or 'middle')
            clicks: Number of clicks
            interval: Interval between clicks
            
        Returns:
            Response data
        """
        logger.info(f"Clicking {button} button at ({x}, {y})")
        return self._request("POST", "/mouse/click", json={
            "x": x,
            "y": y,
            "button": button,
            "clicks": clicks,
            "interval": interval
        })
    
    def drag_mouse(
        self,
        x: int,
        y: int,
        duration: float = 0.5,
        button: str = "left"
    ) -> Dict[str, Any]:
        """
        Drag mouse to specified coordinates.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Duration of drag in seconds
            button: Mouse button to hold
            
        Returns:
            Response data
        """
        logger.info(f"Dragging to ({x}, {y})")
        return self._request("POST", "/mouse/drag", json={
            "x": x,
            "y": y,
            "duration": duration,
            "button": button
        })
    
    def scroll_mouse(
        self,
        clicks: int,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scroll mouse wheel.
        
        Args:
            clicks: Number of scroll clicks (positive=up, negative=down)
            x: X coordinate to scroll at (None for current position)
            y: Y coordinate to scroll at (None for current position)
            
        Returns:
            Response data
        """
        logger.info(f"Scrolling {clicks} clicks")
        return self._request("POST", "/mouse/scroll", json={
            "clicks": clicks,
            "x": x,
            "y": y
        })
    
    def get_mouse_position(self) -> Dict[str, Any]:
        """
        Get current mouse position.
        
        Returns:
            Response data with position
        """
        return self._request("GET", "/mouse/position")
    
    # Keyboard Control Methods
    def type_text(self, text: str, interval: float = 0.0) -> Dict[str, Any]:
        """
        Type text using keyboard.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
            
        Returns:
            Response data
        """
        logger.info(f"Typing text: {text[:50]}...")
        return self._request("POST", "/keyboard/type", json={
            "text": text,
            "interval": interval
        })
    
    def press_key(
        self,
        key: str,
        presses: int = 1,
        interval: float = 0.0
    ) -> Dict[str, Any]:
        """
        Press a specific key.
        
        Args:
            key: Key to press (e.g., 'enter', 'tab', 'ctrl')
            presses: Number of times to press
            interval: Interval between presses
            
        Returns:
            Response data
        """
        logger.info(f"Pressing key: {key}")
        return self._request("POST", "/keyboard/press", json={
            "key": key,
            "presses": presses,
            "interval": interval
        })
    
    def press_hotkey(self, *keys: str) -> Dict[str, Any]:
        """
        Press a combination of keys (hotkey).
        
        Args:
            *keys: Keys to press together (e.g., 'ctrl', 'c')
            
        Returns:
            Response data
        """
        logger.info(f"Pressing hotkey: {'+'.join(keys)}")
        return self._request("POST", "/keyboard/hotkey", json={
            "keys": list(keys)
        })
    
    # Screen Control Methods
    def take_screenshot(
        self,
        region: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Take a screenshot.
        
        Args:
            region: Region to capture [x, y, width, height] (None for full screen)
            
        Returns:
            Response data with base64-encoded image
        """
        logger.info("Taking screenshot")
        payload = {}
        if region:
            payload["region"] = region
        return self._request("POST", "/screen/screenshot", json=payload)
    
    def get_screen_size(self) -> Dict[str, Any]:
        """
        Get screen size.
        
        Returns:
            Response data with width and height
        """
        return self._request("GET", "/screen/size")
    
    # Utility Methods
    def get_available_keys(self) -> Dict[str, Any]:
        """
        Get list of available keyboard keys.
        
        Returns:
            Response data with list of keys
        """
        return self._request("GET", "/keyboard/keys")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the API is running.
        
        Returns:
            Health status
        """
        return self._request("GET", "/health")
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()
        logger.info("Control client closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Singleton instance
_control_client: Optional[ComputerControlClient] = None


def get_control_client(base_url: str = "http://127.0.0.1:8001") -> ComputerControlClient:
    """
    Get or create singleton control client instance.
    
    Args:
        base_url: Base URL of the Computer Control API
        
    Returns:
        ComputerControlClient instance
    """
    global _control_client
    if _control_client is None:
        _control_client = ComputerControlClient(base_url)
    return _control_client


# Example usage
if __name__ == "__main__":
    # Test the control client
    with ComputerControlClient() as client:
        # Check health
        print("Health check:", client.health_check())
        
        # Get screen size
        print("Screen size:", client.get_screen_size())
        
        # Get mouse position
        print("Mouse position:", client.get_mouse_position())
        
        # Move mouse
        print("Moving mouse...")
        client.move_mouse(500, 500)
        
        # Type text
        print("Typing text...")
        client.type_text("Hello from Edward!")

# Made with Bob