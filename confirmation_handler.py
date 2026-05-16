"""
Confirmation Handler Module
Manages user confirmation for computer actions
Supports both UI dialogs and voice confirmation
"""

import re
from typing import Optional, Dict, Any, Callable
from enum import Enum
from logger import get_logger

logger = get_logger(__name__)


class ActionType(Enum):
    """Types of actions that require confirmation"""
    CREATE_FILE = "create_file"
    EDIT_FILE = "edit_file"
    DELETE_FILE = "delete_file"
    OPEN_FILE = "open_file"
    OPEN_APP = "open_app"
    RUN_COMMAND = "run_command"
    COPY_TO_CLIPBOARD = "copy_to_clipboard"


class ConfirmationResult(Enum):
    """Result of confirmation request"""
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    ERROR = "error"


class ActionRequest:
    """Represents a pending action that needs confirmation"""
    
    def __init__(
        self,
        action_type: ActionType,
        description: str,
        parameters: Dict[str, Any],
        callback: Optional[Callable] = None
    ):
        """
        Initialize an action request.
        
        Args:
            action_type: Type of action
            description: Human-readable description
            parameters: Action parameters
            callback: Function to call when confirmed
        """
        self.action_type = action_type
        self.description = description
        self.parameters = parameters
        self.callback = callback
        self.result: Optional[ConfirmationResult] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "action_type": self.action_type.value,
            "description": self.description,
            "parameters": self.parameters
        }


class ConfirmationHandler:
    """
    Handles confirmation flow for computer actions.
    Parses Edward's responses, presents confirmation dialogs, and executes approved actions.
    """

    def __init__(self):
        """Initialize the confirmation handler"""
        self.pending_action: Optional[ActionRequest] = None
        self.confirmation_callback: Optional[Callable] = None

        # Patterns to detect action requests in Edward's responses
        self.action_patterns = {
            ActionType.CREATE_FILE: [
                r"(?:create|make|write)\s+(?:a\s+)?(?:new\s+)?file\s+(?:called\s+|named\s+)?['\"]?([^'\"]+)['\"]?",
                r"(?:save|write)\s+(?:this|the following)\s+(?:to|in)\s+['\"]?([^'\"]+)['\"]?",
            ],
            ActionType.EDIT_FILE: [
                r"(?:edit|modify|update|change)\s+(?:the\s+)?file\s+['\"]?([^'\"]+)['\"]?",
                r"(?:replace|update)\s+(?:the\s+)?content\s+(?:of|in)\s+['\"]?([^'\"]+)['\"]?",
            ],
            ActionType.OPEN_FILE: [
                r"(?:open|show|display)\s+(?:the\s+)?file\s+['\"]?([^'\"]+)['\"]?",
            ],
            ActionType.OPEN_APP: [
                r"(?:open|launch|start|run)\s+(?:the\s+)?(?:application|app|program)\s+['\"]?([^'\"]+)['\"]?",
            ],
        }
        
        logger.info("Confirmation handler initialized")
    
    def parse_response_for_actions(self, response: str) -> Optional[ActionRequest]:
        """
        Parse Edward's response to detect action requests.

        Args:
            response: Response text
            
        Returns:
            ActionRequest if action detected, None otherwise
        """
        response_lower = response.lower()
        
        # Check each action type
        for action_type, patterns in self.action_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, response_lower, re.IGNORECASE)
                if match:
                    # Extract parameters from match
                    target = match.group(1) if match.groups() else None
                    
                    # Create action request
                    action = self._create_action_request(
                        action_type,
                        response,
                        target
                    )
                    
                    if action:
                        logger.info(f"Detected action: {action_type.value} - {target}")
                        return action
        
        return None
    
    def _create_action_request(
        self,
        action_type: ActionType,
        full_response: str,
        target: Optional[str]
    ) -> Optional[ActionRequest]:
        """
        Create an ActionRequest from detected action.
        
        Args:
            action_type: Type of action
            full_response: Full response text
            target: Target file/app name
            
        Returns:
            ActionRequest or None
        """
        if action_type == ActionType.CREATE_FILE:
            # Extract content (look for code blocks or quoted text)
            content = self._extract_content(full_response)
            
            return ActionRequest(
                action_type=action_type,
                description=f"Create file '{target}' with {len(content)} characters",
                parameters={
                    "file_path": target or "",
                    "content": content
                }
            )
        
        elif action_type == ActionType.EDIT_FILE:
            content = self._extract_content(full_response)
            
            return ActionRequest(
                action_type=action_type,
                description=f"Edit file '{target}' (replace with {len(content)} characters)",
                parameters={
                    "file_path": target or "",
                    "new_content": content
                }
            )
        
        elif action_type == ActionType.OPEN_FILE:
            return ActionRequest(
                action_type=action_type,
                description=f"Open file '{target}'",
                parameters={
                    "path": target or ""
                }
            )
        
        elif action_type == ActionType.OPEN_APP:
            return ActionRequest(
                action_type=action_type,
                description=f"Open application '{target}'",
                parameters={
                    "path": target or ""
                }
            )
        
        return None
    
    def _extract_content(self, text: str) -> str:
        """
        Extract content from response (code blocks or quoted text).
        
        Args:
            text: Response text
            
        Returns:
            Extracted content
        """
        # Try to extract code block
        code_block_match = re.search(r'```(?:\w+)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # Try to extract quoted text
        quote_match = re.search(r'["\']([^"\']+)["\']', text)
        if quote_match:
            return quote_match.group(1).strip()
        
        # Return full text as fallback
        return text.strip()
    
    def request_confirmation(
        self,
        action: ActionRequest,
        callback: Callable[[ConfirmationResult, Optional[ActionRequest]], None]
    ):
        """
        Request user confirmation for an action.
        
        Args:
            action: Action to confirm
            callback: Function to call with result
        """
        self.pending_action = action
        self.confirmation_callback = callback
        
        logger.info(f"Requesting confirmation for: {action.description}")
        
        # The callback will be triggered by the UI dialog or voice confirmation
        # This is handled by the main application
    
    def handle_confirmation_response(self, approved: bool):
        """
        Handle user's confirmation response.
        
        Args:
            approved: Whether user approved the action
        """
        if not self.pending_action or not self.confirmation_callback:
            logger.warning("No pending action to confirm")
            return
        
        result = ConfirmationResult.APPROVED if approved else ConfirmationResult.DENIED
        self.pending_action.result = result
        
        logger.info(f"Action {result.value}: {self.pending_action.description}")
        
        # Call the callback with result
        self.confirmation_callback(result, self.pending_action)
        
        # Clear pending action
        self.pending_action = None
        self.confirmation_callback = None
    
    def handle_voice_confirmation(self, transcript: str) -> Optional[bool]:
        """
        Parse voice input for confirmation.
        
        Args:
            transcript: Voice transcript
            
        Returns:
            True if confirmed, False if denied, None if unclear
        """
        transcript_lower = transcript.lower().strip()
        
        # Positive responses
        positive = [
            "yes", "yeah", "yep", "sure", "ok", "okay", "confirm",
            "do it", "go ahead", "proceed", "approve", "affirmative"
        ]
        
        # Negative responses
        negative = [
            "no", "nope", "nah", "cancel", "stop", "don't", "deny",
            "negative", "abort"
        ]
        
        # Check for positive
        if any(word in transcript_lower for word in positive):
            logger.info(f"Voice confirmation: APPROVED ('{transcript}')")
            return True
        
        # Check for negative
        if any(word in transcript_lower for word in negative):
            logger.info(f"Voice confirmation: DENIED ('{transcript}')")
            return False
        
        # Unclear
        logger.warning(f"Voice confirmation unclear: '{transcript}'")
        return None
    
    def cancel_pending_action(self):
        """Cancel any pending action (timeout or user cancel)"""
        if self.pending_action:
            logger.info(f"Cancelled pending action: {self.pending_action.description}")
            
            if self.confirmation_callback:
                self.confirmation_callback(ConfirmationResult.TIMEOUT, self.pending_action)
            
            self.pending_action = None
            self.confirmation_callback = None


# Example usage
if __name__ == "__main__":
    print("Testing Confirmation Handler...")
    print("=" * 50)
    
    handler = ConfirmationHandler()
    
    # Test 1: Parse create file action
    print("\n1. Testing create file detection...")
    response1 = """I'll create a file called 'test.txt' with the following content:
    ```
    Hello World!
    This is a test.
    ```
    """
    action = handler.parse_response_for_actions(response1)
    if action:
        print(f"   ✓ Detected: {action.description}")
        print(f"   Parameters: {action.parameters}")
    
    # Test 2: Parse edit file action
    print("\n2. Testing edit file detection...")
    response2 = "Let me edit the file 'config.json' with the updated settings."
    action = handler.parse_response_for_actions(response2)
    if action:
        print(f"   ✓ Detected: {action.description}")
    
    # Test 3: Parse open app action
    print("\n3. Testing open app detection...")
    response3 = "I'll open the application 'notepad' for you."
    action = handler.parse_response_for_actions(response3)
    if action:
        print(f"   ✓ Detected: {action.description}")
    
    # Test 4: Voice confirmation
    print("\n4. Testing voice confirmation...")
    test_phrases = ["yes", "no", "yeah sure", "nope", "maybe"]
    for phrase in test_phrases:
        result = handler.handle_voice_confirmation(phrase)
        print(f"   '{phrase}' → {result}")
    
    print("\n" + "=" * 50)
    print("All tests complete!")

# Made with Bob
