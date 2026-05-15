"""
AI Control Processor
Processes screenshots with AI and executes computer control actions
"""

import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime

from watsonx_client import WatsonxVisionClient, get_watsonx_client
from control_client import ComputerControlClient, get_control_client
from logger import get_logger

# Setup logging
logger = get_logger(__name__)


class AIControlProcessor:
    """
    Processes screenshots with AI and executes control actions.
    """
    
    def __init__(
        self,
        watsonx_client: WatsonxVisionClient,
        control_client: ComputerControlClient,
        task_description: str = "Assist the user with their computer tasks",
        auto_execute: bool = True,
        confirmation_callback: Optional[Callable] = None
    ):
        """
        Initialize AI control processor.
        
        Args:
            watsonx_client: Watsonx vision client
            control_client: Computer control client
            task_description: Description of the task to accomplish
            auto_execute: If True, automatically execute actions
            confirmation_callback: Optional callback for action confirmation
        """
        self.watsonx_client = watsonx_client
        self.control_client = control_client
        self.task_description = task_description
        self.auto_execute = auto_execute
        self.confirmation_callback = confirmation_callback
        
        self.is_processing = False
        self.last_action: Optional[Dict[str, Any]] = None
        self.action_history: list = []
        self.screen_size: Optional[Dict[str, int]] = None
        
        logger.info("AI Control Processor initialized")
    
    async def initialize(self):
        """Initialize processor and get screen size."""
        try:
            # Get screen size
            size_response = self.control_client.get_screen_size()
            self.screen_size = {
                "width": size_response["width"],
                "height": size_response["height"]
            }
            logger.info(f"Screen size: {self.screen_size['width']}x{self.screen_size['height']}")
        except Exception as e:
            logger.error(f"Failed to initialize processor: {e}")
            raise
    
    async def process_screenshot(self, screenshot_data: Dict[str, Any]):
        """
        Process a screenshot and execute AI decision.
        
        Args:
            screenshot_data: Screenshot data from screenshot service
        """
        if self.is_processing:
            logger.debug("Already processing, skipping this screenshot")
            return
        
        self.is_processing = True
        
        try:
            # Extract screenshot
            screenshot_base64 = screenshot_data.get("image")
            if not screenshot_base64:
                logger.error("No image in screenshot data")
                return
            
            # Get screen dimensions
            if self.screen_size:
                screen_width = screenshot_data.get("original_width") or self.screen_size["width"]
                screen_height = screenshot_data.get("original_height") or self.screen_size["height"]
            else:
                screen_width = screenshot_data.get("original_width", 1920)
                screen_height = screenshot_data.get("original_height", 1080)
            
            # Analyze screenshot with AI
            logger.info("Analyzing screenshot with AI...")
            action = await asyncio.to_thread(
                self.watsonx_client.analyze_screenshot,
                screenshot_base64,
                self.task_description,
                screen_width,
                screen_height
            )
            
            # Check for errors
            if action.get("action_type") == "error":
                logger.error(f"AI analysis error: {action.get('error')}")
                return
            
            # Log action
            logger.info(f"AI Decision: {action.get('action_type')}")
            logger.info(f"Reasoning: {action.get('reasoning', 'N/A')}")
            
            # Store action
            self.last_action = action
            self.action_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": action
            })
            
            # Execute action
            if self.auto_execute:
                await self._execute_action(action)
            elif self.confirmation_callback:
                # Request confirmation
                if asyncio.iscoroutinefunction(self.confirmation_callback):
                    confirmed = await self.confirmation_callback(action)
                else:
                    confirmed = self.confirmation_callback(action)
                
                if confirmed:
                    await self._execute_action(action)
            
        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
        finally:
            self.is_processing = False
    
    async def _execute_action(self, action: Dict[str, Any]):
        """
        Execute a control action.
        
        Args:
            action: Action dictionary from AI
        """
        try:
            action_type = action.get("action_type")
            params = action.get("parameters", {})
            
            logger.info(f"Executing action: {action_type}")
            
            if action_type == "move_mouse":
                await asyncio.to_thread(
                    self.control_client.move_mouse,
                    params.get("x"),
                    params.get("y"),
                    params.get("duration", 0.2)
                )
            
            elif action_type == "click":
                await asyncio.to_thread(
                    self.control_client.click_mouse,
                    params.get("x"),
                    params.get("y"),
                    params.get("button", "left"),
                    params.get("clicks", 1)
                )
            
            elif action_type == "type":
                await asyncio.to_thread(
                    self.control_client.type_text,
                    params.get("text", ""),
                    params.get("interval", 0.0)
                )
            
            elif action_type == "press_key":
                await asyncio.to_thread(
                    self.control_client.press_key,
                    params.get("key"),
                    params.get("presses", 1)
                )
            
            elif action_type == "hotkey":
                keys = params.get("keys", [])
                await asyncio.to_thread(
                    self.control_client.press_hotkey,
                    *keys
                )
            
            elif action_type == "scroll":
                await asyncio.to_thread(
                    self.control_client.scroll_mouse,
                    params.get("clicks", 0),
                    params.get("x"),
                    params.get("y")
                )
            
            elif action_type == "wait":
                wait_time = params.get("seconds", 1.0)
                logger.info(f"Waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            
            elif action_type == "complete":
                logger.info(f"Task complete: {params.get('message', 'Done')}")
            
            else:
                logger.warning(f"Unknown action type: {action_type}")
            
            logger.info(f"Action executed successfully: {action_type}")
            
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
    
    def set_task(self, task_description: str):
        """
        Update the task description.
        
        Args:
            task_description: New task description
        """
        self.task_description = task_description
        logger.info(f"Task updated: {task_description[:50]}...")
    
    def get_action_history(self, limit: int = 10) -> list:
        """
        Get recent action history.
        
        Args:
            limit: Maximum number of actions to return
            
        Returns:
            List of recent actions
        """
        return self.action_history[-limit:]
    
    def clear_history(self):
        """Clear action history."""
        self.action_history.clear()
        logger.info("Action history cleared")


class AutonomousControlLoop:
    """
    Main autonomous control loop that coordinates screenshot capture and AI processing.
    """
    
    def __init__(
        self,
        watsonx_api_key: str,
        watsonx_project_id: str,
        task_description: str,
        screenshot_interval: float = 2.0,
        watsonx_url: str = "https://us-south.ml.cloud.ibm.com",
        control_api_url: str = "http://127.0.0.1:8001",
        auto_execute: bool = True
    ):
        """
        Initialize autonomous control loop.
        
        Args:
            watsonx_api_key: IBM Watsonx API key
            watsonx_project_id: Watsonx project ID
            task_description: Task for AI to accomplish
            screenshot_interval: Seconds between screenshots
            watsonx_url: Watsonx API URL
            control_api_url: Computer control API URL
            auto_execute: Auto-execute actions without confirmation
        """
        # Initialize clients
        self.watsonx_client = get_watsonx_client(
            api_key=watsonx_api_key,
            project_id=watsonx_project_id,
            url=watsonx_url
        )
        
        self.control_client = get_control_client(base_url=control_api_url)
        
        # Initialize processor
        self.processor = AIControlProcessor(
            watsonx_client=self.watsonx_client,
            control_client=self.control_client,
            task_description=task_description,
            auto_execute=auto_execute
        )
        
        self.screenshot_interval = screenshot_interval
        self.is_running = False
        
        logger.info("Autonomous Control Loop initialized")
    
    async def start(self):
        """Start the autonomous control loop."""
        if self.is_running:
            logger.warning("Control loop already running")
            return
        
        logger.info("Starting autonomous control loop...")
        
        # Initialize processor
        await self.processor.initialize()
        
        self.is_running = True
        
        # Import here to avoid circular dependency
        from screenshot_service import get_screenshot_service
        
        # Start screenshot service
        screenshot_service = get_screenshot_service(interval=self.screenshot_interval)
        await screenshot_service.start(self.processor.process_screenshot)
        
        logger.info("Autonomous control loop started")
    
    async def stop(self):
        """Stop the autonomous control loop."""
        if not self.is_running:
            return
        
        logger.info("Stopping autonomous control loop...")
        
        self.is_running = False
        
        # Stop screenshot service
        from screenshot_service import get_screenshot_service
        screenshot_service = get_screenshot_service()
        await screenshot_service.stop()
        
        logger.info("Autonomous control loop stopped")
    
    def set_task(self, task_description: str):
        """Update the task description."""
        self.processor.set_task(task_description)


# Made with Bob