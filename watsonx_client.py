"""
IBM Watsonx Client for Vision-Based Computer Control
Handles screenshot analysis and AI decision making using IBM Watsonx
"""

import base64
import json
from typing import Optional, Dict, Any, List
from ibm_watsonx_ai.foundation_models import Model
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from ibm_watsonx_ai import Credentials

from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class WatsonxVisionClient:
    """
    Client for IBM Watsonx vision and language models.
    Analyzes screenshots and generates computer control decisions.
    """
    
    def __init__(
        self,
        api_key: str,
        project_id: str,
        url: str = "https://us-south.ml.cloud.ibm.com",
        model_id: str = "meta-llama/llama-3-2-90b-vision-instruct"
    ):
        """
        Initialize Watsonx client.
        
        Args:
            api_key: IBM Cloud API key
            project_id: Watsonx project ID
            url: Watsonx API URL
            model_id: Vision-language model ID
        """
        self.api_key = api_key
        self.project_id = project_id
        self.url = url
        self.model_id = model_id
        
        # Initialize credentials
        self.credentials = Credentials(
            api_key=api_key,
            url=url
        )
        
        # Initialize model
        self.model = Model(
            model_id=model_id,
            credentials=self.credentials,
            project_id=project_id,
            params={
                GenParams.MAX_NEW_TOKENS: 1000,
                GenParams.TEMPERATURE: 0.7,
                GenParams.TOP_P: 0.9,
            }
        )
        
        logger.info(f"Watsonx Vision Client initialized with model: {model_id}")
    
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
            
            # Prepare input with image
            input_data = {
                "input": prompt,
                "image": screenshot_base64
            }
            
            logger.info(f"Analyzing screenshot for task: {task_description[:50]}...")
            
            # Generate response
            response = self.model.generate_text(prompt=prompt)
            
            # Parse response into action
            action = self._parse_action_response(response)
            
            logger.info(f"Generated action: {action.get('action_type', 'none')}")
            
            return action
            
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
   Format: {{"action": "click", "x": <int>, "y": <int>, "button": "left|right|middle"}}

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
            
            response = self.model.generate_text(prompt=prompt)
            
            # Parse response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                plan = json.loads(json_str)
                
                logger.info(f"Generated plan with {len(plan)} steps")
                return plan
            else:
                raise ValueError("No JSON array found in response")
                
        except Exception as e:
            logger.error(f"Failed to generate task plan: {e}")
            return []


# Singleton instance
_watsonx_client: Optional[WatsonxVisionClient] = None


def get_watsonx_client(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    url: Optional[str] = None
) -> WatsonxVisionClient:
    """
    Get or create singleton Watsonx client.
    
    Args:
        api_key: IBM Cloud API key
        project_id: Watsonx project ID
        url: Watsonx API URL
        
    Returns:
        WatsonxVisionClient instance
    """
    global _watsonx_client
    
    if _watsonx_client is None:
        if not api_key or not project_id:
            raise ValueError("API key and project ID required for first initialization")
        
        _watsonx_client = WatsonxVisionClient(
            api_key=api_key,
            project_id=project_id,
            url=url or "https://us-south.ml.cloud.ibm.com"
        )
    
    return _watsonx_client


# Made with Bob