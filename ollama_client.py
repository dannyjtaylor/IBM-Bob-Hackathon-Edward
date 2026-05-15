"""
Ollama Vision Client for Local AI Computer Control
Handles screenshot analysis and AI decision making using Ollama with LLaVA models
"""

import base64
import json
import requests
from typing import Optional, Dict, Any, List

from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class OllamaVisionClient:
    """
    Client for Ollama vision and language models.
    Analyzes screenshots and generates computer control decisions locally.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llava:13b",
        temperature: float = 0.7
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API URL
            model: Vision model to use (llava:13b, llava:7b, llava-llama3:8b)
            temperature: Model temperature (0.0-1.0)
        """
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        
        logger.info(f"Ollama Vision Client initialized with model: {model}")
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama is running")
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                if model in model_names:
                    logger.info(f"✅ Model {model} is available")
                else:
                    logger.warning(f"⚠️ Model {model} not found. Available: {model_names}")
                    logger.warning(f"Run: ollama pull {model}")
            else:
                logger.error("❌ Ollama is not responding correctly")
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            logger.error("Make sure Ollama is installed and running")
    
    def analyze_screenshot(
        self,
        screenshot_base64: str,
        task_description: str,
        screen_width: int,
        screen_height: int
    ) -> Dict[str, Any]:
        """
        Analyze screenshot and generate computer control decision.
        
        Args:
            screenshot_base64: Base64-encoded screenshot
            task_description: Description of what the AI should do
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            
        Returns:
            Dictionary with action decision
        """
        try:
            # Create prompt for vision model
            prompt = self._create_control_prompt(
                task_description,
                screen_width,
                screen_height
            )
            
            logger.info(f"Analyzing screenshot for task: {task_description[:50]}...")
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [screenshot_base64],
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 500
                    }
                },
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse response into action
            action = self._parse_action_response(result.get("response", ""))
            
            logger.info(f"Generated action: {action.get('action_type', 'none')}")
            
            return action
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            return {
                "action_type": "error",
                "error": f"Ollama API error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return {
                "action_type": "error",
                "error": str(e)
            }
    
    def _create_control_prompt(
        self,
        task_description: str,
        screen_width: int,
        screen_height: int
    ) -> str:
        """
        Create prompt for the vision model.
        
        Args:
            task_description: What the AI should accomplish
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are an AI assistant controlling a computer through vision and actions.

SCREEN INFORMATION:
- Screen size: {screen_width}x{screen_height} pixels
- Coordinate system: (0,0) is top-left corner

TASK:
{task_description}

Analyze the screenshot and decide what action to take next. You can perform these actions:

1. MOVE_MOUSE: Move cursor to specific coordinates
   Format: {{"action": "move_mouse", "x": <int>, "y": <int>}}

2. CLICK: Click at specific coordinates or current position
   Format: {{"action": "click", "x": <int>, "y": <int>, "button": "left"}}

3. TYPE: Type text
   Format: {{"action": "type", "text": "<string>"}}

4. PRESS_KEY: Press a specific key
   Format: {{"action": "press_key", "key": "<key_name>"}}

5. HOTKEY: Press key combination
   Format: {{"action": "hotkey", "keys": ["ctrl", "c"]}}

6. SCROLL: Scroll up or down
   Format: {{"action": "scroll", "clicks": <int>}}

7. WAIT: Wait before next action
   Format: {{"action": "wait", "seconds": <float>}}

8. COMPLETE: Task is complete
   Format: {{"action": "complete", "message": "<string>"}}

Respond with ONLY a valid JSON object containing your decision. Include a "reasoning" field explaining why you chose this action.

Example response:
{{"action": "click", "x": 500, "y": 300, "button": "left", "reasoning": "Clicking the search button to proceed with the task"}}"""
        
        return prompt
    
    def _parse_action_response(self, response: str) -> Dict[str, Any]:
        """
        Parse AI response into action dictionary.
        
        Args:
            response: Raw response from model
            
        Returns:
            Parsed action dictionary
        """
        try:
            # Try to extract JSON from response
            # Look for JSON object in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                action = json.loads(json_str)
                
                # Validate action has required fields
                if "action" not in action:
                    raise ValueError("Action field missing from response")
                
                return {
                    "action_type": action.get("action"),
                    "parameters": action,
                    "reasoning": action.get("reasoning", "No reasoning provided")
                }
            else:
                raise ValueError("No JSON object found in response")
                
        except Exception as e:
            logger.error(f"Failed to parse action response: {e}")
            logger.debug(f"Raw response: {response}")
            
            return {
                "action_type": "error",
                "error": f"Failed to parse response: {str(e)}",
                "raw_response": response
            }
    
    def generate_task_plan(
        self,
        screenshot_base64: str,
        goal: str,
        screen_width: int,
        screen_height: int
    ) -> List[Dict[str, Any]]:
        """
        Generate a multi-step plan for accomplishing a goal.
        
        Args:
            screenshot_base64: Base64-encoded screenshot
            goal: High-level goal to accomplish
            screen_width: Screen width
            screen_height: Screen height
            
        Returns:
            List of planned actions
        """
        try:
            prompt = f"""You are an AI assistant planning computer control actions.

SCREEN INFORMATION:
- Screen size: {screen_width}x{screen_height} pixels

GOAL:
{goal}

Analyze the screenshot and create a step-by-step plan to accomplish this goal.
Return a JSON array of actions in sequence.

Example:
[
  {{"action": "click", "x": 100, "y": 200, "reasoning": "Open menu"}},
  {{"action": "type", "text": "search query", "reasoning": "Enter search"}},
  {{"action": "press_key", "key": "enter", "reasoning": "Submit search"}}
]

Respond with ONLY the JSON array."""
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [screenshot_base64],
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": 1000
                    }
                },
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")
            
            # Parse response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                plan = json.loads(json_str)
                
                logger.info(f"Generated plan with {len(plan)} steps")
                return plan
            else:
                raise ValueError("No JSON array found in response")
                
        except Exception as e:
            logger.error(f"Failed to generate task plan: {e}")
            return []
    
    def check_model_available(self) -> bool:
        """
        Check if the configured model is available.
        
        Returns:
            True if model is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                return self.model in model_names
            return False
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False


# Singleton instance
_ollama_client: Optional[OllamaVisionClient] = None


def get_ollama_client(
    base_url: str = "http://localhost:11434",
    model: str = "llava:13b",
    temperature: float = 0.7
) -> OllamaVisionClient:
    """
    Get or create singleton Ollama client.
    
    Args:
        base_url: Ollama API URL
        model: Vision model to use
        temperature: Model temperature
        
    Returns:
        OllamaVisionClient instance
    """
    global _ollama_client
    
    if _ollama_client is None:
        _ollama_client = OllamaVisionClient(
            base_url=base_url,
            model=model,
            temperature=temperature
        )
    
    return _ollama_client


# Made with Bob