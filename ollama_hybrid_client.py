"""
Ollama Hybrid Client for Computer Control
Uses separate vision and text models for better performance
"""

import base64
import json
import requests
from typing import Optional, Dict, Any, List

from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class OllamaHybridClient:
    """
    Hybrid client using separate vision and text models.
    Vision model analyzes screenshots, text model generates actions.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        vision_model: str = "llava:7b",
        text_model: str = "llama3.2:3b",
        temperature: float = 0.7
    ):
        """
        Initialize hybrid Ollama client.
        
        Args:
            base_url: Ollama API URL
            vision_model: Vision model for screenshot analysis (llava:7b recommended)
            text_model: Text model for action generation (llama3.2:3b, phi3:mini)
            temperature: Model temperature (0.0-1.0)
        """
        self.base_url = base_url
        self.vision_model = vision_model
        self.text_model = text_model
        self.temperature = temperature
        
        logger.info(f"Ollama Hybrid Client initialized")
        logger.info(f"  Vision Model: {vision_model}")
        logger.info(f"  Text Model: {text_model}")
        
        # Check if Ollama is running and models are available
        self._check_setup()
    
    def _check_setup(self):
        """Check Ollama setup and model availability."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama is running")
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                # Check vision model
                if self.vision_model in model_names:
                    logger.info(f"✅ Vision model '{self.vision_model}' available")
                else:
                    logger.warning(f"⚠️ Vision model '{self.vision_model}' not found")
                    logger.warning(f"Run: ollama pull {self.vision_model}")
                
                # Check text model
                if self.text_model in model_names:
                    logger.info(f"✅ Text model '{self.text_model}' available")
                else:
                    logger.warning(f"⚠️ Text model '{self.text_model}' not found")
                    logger.warning(f"Run: ollama pull {self.text_model}")
            else:
                logger.error("❌ Ollama is not responding correctly")
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
    
    def analyze_screenshot(
        self,
        screenshot_base64: str,
        task_description: str,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """
        Analyze screenshot using hybrid approach.
        
        Step 1: Vision model describes what's on screen
        Step 2: Text model generates action based on description
        
        Args:
            screenshot_base64: Base64-encoded screenshot
            task_description: Description of what the AI should do
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            
        Returns:
            Dictionary with action decision
        """
        try:
            logger.info(f"Analyzing screenshot for task: {task_description[:50]}...")
            
            # Step 1: Vision model analyzes screenshot
            vision_description = self._analyze_with_vision(
                screenshot_base64,
                task_description,
                screen_width,
                screen_height
            )
            
            if not vision_description:
                return {
                    "action_type": "error",
                    "error": "Vision analysis failed"
                }
            
            logger.info(f"Vision analysis: {vision_description[:100]}...")
            
            # Step 2: Text model generates action
            action = self._generate_action_with_text(
                vision_description,
                task_description,
                screen_width,
                screen_height
            )
            
            logger.info(f"Generated action: {action.get('action_type', 'none')}")
            
            return action
            
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return {
                "action_type": "error",
                "error": str(e)
            }
    
    def _analyze_with_vision(
        self,
        screenshot_base64: str,
        task_description: str,
        screen_width: int,
        screen_height: int
    ) -> Optional[str]:
        """
        Use vision model to describe what's on screen.
        
        Returns:
            Description of screen contents
        """
        try:
            prompt = f"""Analyze this screenshot and describe what you see in detail.

Screen size: {screen_width}x{screen_height} pixels
Task context: {task_description}

Focus on:
1. What applications or windows are visible
2. UI elements (buttons, text fields, menus)
3. Their approximate positions on screen
4. Current state (what's selected, what's open)

Be specific about locations (top-left, center, bottom-right, etc.)."""

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.vision_model,
                    "prompt": prompt,
                    "images": [screenshot_base64],
                    "stream": False,
                    "options": {
                        "temperature": 0.5,  # Lower for more accurate descriptions
                        "num_predict": 300
                    }
                },
                timeout=120  # Increased timeout for vision model (first run can be slow)
            )
            
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return None
    
    def _generate_action_with_text(
        self,
        vision_description: str,
        task_description: str,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """
        Use text model to generate action based on vision description.
        
        Returns:
            Action dictionary
        """
        try:
            prompt = f"""You are an AI controlling a computer. Based on the screen description, decide what action to take.

SCREEN DESCRIPTION:
{vision_description}

SCREEN SIZE: {screen_width}x{screen_height} pixels

TASK: {task_description}

AVAILABLE ACTIONS:
1. move_mouse: {{"action": "move_mouse", "x": <int>, "y": <int>}}
2. click: {{"action": "click", "x": <int>, "y": <int>, "button": "left"}}
3. type: {{"action": "type", "text": "<string>"}}
4. press_key: {{"action": "press_key", "key": "<key_name>"}}
5. hotkey: {{"action": "hotkey", "keys": ["ctrl", "c"]}}
6. scroll: {{"action": "scroll", "clicks": <int>}}
7. wait: {{"action": "wait", "seconds": <float>}}
8. complete: {{"action": "complete", "message": "<string>"}}

Respond with ONLY a JSON object containing your decision and reasoning.

Example: {{"action": "click", "x": 500, "y": 300, "button": "left", "reasoning": "Clicking the search button"}}"""

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.text_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 200
                    }
                },
                timeout=60  # Increased timeout for text model
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse response
            return self._parse_action_response(result.get("response", ""))
            
        except Exception as e:
            logger.error(f"Action generation failed: {e}")
            return {
                "action_type": "error",
                "error": f"Action generation failed: {str(e)}"
            }
    
    def _parse_action_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into action dictionary."""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                action = json.loads(json_str)
                
                if "action" not in action:
                    raise ValueError("Action field missing")
                
                return {
                    "action_type": action.get("action"),
                    "parameters": action,
                    "reasoning": action.get("reasoning", "No reasoning provided")
                }
            else:
                raise ValueError("No JSON object found in response")
                
        except Exception as e:
            logger.error(f"Failed to parse action: {e}")
            logger.debug(f"Raw response: {response}")
            
            return {
                "action_type": "error",
                "error": f"Failed to parse response: {str(e)}",
                "raw_response": response
            }
    
    def check_model_available(self) -> bool:
        """
        Check if both models are available.
        
        Returns:
            True if both models are available
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                vision_ok = self.vision_model in model_names
                text_ok = self.text_model in model_names
                
                return vision_ok and text_ok
            return False
        except Exception as e:
            logger.error(f"Failed to check models: {e}")
            return False
    
    def check_models_available(self) -> Dict[str, bool]:
        """
        Check if both models are available.
        
        Returns:
            Dictionary with availability status
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                
                return {
                    "vision_model": self.vision_model in model_names,
                    "text_model": self.text_model in model_names
                }
            return {"vision_model": False, "text_model": False}
        except Exception as e:
            logger.error(f"Failed to check models: {e}")
            return {"vision_model": False, "text_model": False}


# Singleton instance
_hybrid_client: Optional[OllamaHybridClient] = None


def get_hybrid_client(
    base_url: str = "http://localhost:11434",
    vision_model: str = "llava:7b",
    text_model: str = "llama3.2:3b",
    temperature: float = 0.7
) -> OllamaHybridClient:
    """
    Get or create singleton hybrid client.
    
    Args:
        base_url: Ollama API URL
        vision_model: Vision model name
        text_model: Text model name
        temperature: Model temperature
        
    Returns:
        OllamaHybridClient instance
    """
    global _hybrid_client
    
    if _hybrid_client is None:
        _hybrid_client = OllamaHybridClient(
            base_url=base_url,
            vision_model=vision_model,
            text_model=text_model,
            temperature=temperature
        )
    
    return _hybrid_client


# Made with Bob