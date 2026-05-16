"""
Edward Context Enhancer
Combines multiple context sources (screenshot, clipboard, history) 
to create rich prompts for IBM Bob
"""

from typing import Optional, Dict, Any
from clipboard_assistant import get_clipboard_assistant
from logger import get_logger

logger = get_logger(__name__)


class ContextEnhancer:
    """
    Enhances user questions with contextual information
    to help IBM Bob provide better responses.
    """
    
    def __init__(self):
        """Initialize context enhancer"""
        self.clipboard = get_clipboard_assistant()
        self.last_context = {}
        logger.info("Context Enhancer initialized")
    
    def build_enhanced_prompt(
        self,
        user_question: str,
        screenshot_base64: Optional[str] = None,
        include_clipboard: bool = True,
        conversation_history: Optional[list] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build an enhanced prompt with all available context.
        
        Args:
            user_question: User's original question
            screenshot_base64: Base64-encoded screenshot (optional)
            include_clipboard: Whether to include clipboard content
            conversation_history: Recent conversation history
            
        Returns:
            Tuple of (enhanced_prompt, context_metadata)
        """
        context_parts = []
        metadata: Dict[str, Any] = {
            'has_screenshot': bool(screenshot_base64),
            'has_clipboard': False,
            'has_history': bool(conversation_history),
            'clipboard_type': None,
            'clipboard_included': False,
            'screenshot_included': bool(screenshot_base64)
        }
        
        # Add screenshot context
        if screenshot_base64:
            context_parts.append("I can see your screen.")
        
        # Add clipboard context if relevant
        if include_clipboard:
            clipboard_content = self.clipboard.get_clipboard_content()
            if clipboard_content and self._is_clipboard_relevant(user_question, clipboard_content):
                clipboard_type = self.clipboard.analyze_content_type(clipboard_content)
                metadata['has_clipboard'] = True
                metadata['clipboard_type'] = clipboard_type
                metadata['clipboard_included'] = True
                
                # Add clipboard context
                context_parts.append(f"\nYou recently copied this {clipboard_type}:")
                context_parts.append(f"```\n{clipboard_content[:500]}\n```")  # Limit to 500 chars
        
        # Add conversation history context
        if conversation_history and len(conversation_history) > 0:
            context_parts.append("\nRecent conversation context:")
            for entry in conversation_history[-3:]:  # Last 3 exchanges
                context_parts.append(f"User: {entry.get('user', '')[:100]}")
                context_parts.append(f"You: {entry.get('assistant', '')[:100]}")
        
        # Build final prompt
        if context_parts:
            enhanced_prompt = f"""Context:
{chr(10).join(context_parts)}

User Question: {user_question}

Please provide a helpful response based on all available context."""
        else:
            enhanced_prompt = user_question
        
        # Store context for reference
        self.last_context = metadata
        
        return enhanced_prompt, metadata
    
    def _is_clipboard_relevant(self, question: str, clipboard_content: str) -> bool:
        """
        Determine if clipboard content is relevant to the question.
        
        Args:
            question: User's question
            clipboard_content: Current clipboard content
            
        Returns:
            True if clipboard should be included in context
        """
        question_lower = question.lower()
        
        # Keywords that suggest clipboard relevance
        clipboard_keywords = [
            'this', 'it', 'code', 'error', 'explain', 'debug',
            'fix', 'what', 'why', 'how', 'copied', 'clipboard'
        ]
        
        # Check if question references clipboard
        if any(keyword in question_lower for keyword in clipboard_keywords):
            return True
        
        # Check if clipboard is code/error (usually relevant)
        clipboard_type = self.clipboard.analyze_content_type(clipboard_content)
        if clipboard_type in ['code', 'error', 'json', 'sql']:
            return True
        
        # Don't include if clipboard is very long text (likely not relevant)
        if len(clipboard_content) > 1000 and clipboard_type == 'text':
            return False
        
        return False
    
    def suggest_follow_up_questions(self, context_metadata: Dict[str, Any]) -> list[str]:
        """
        Suggest relevant follow-up questions based on context.
        
        Args:
            context_metadata: Metadata from build_enhanced_prompt
            
        Returns:
            List of suggested follow-up questions
        """
        suggestions = []
        
        if context_metadata.get('has_screenshot'):
            suggestions.extend([
                "What else do you see on my screen?",
                "Is there anything wrong with what's displayed?",
                "Can you help me with what's on screen?"
            ])
        
        clipboard_type = context_metadata.get('clipboard_type')
        if clipboard_type == 'code':
            suggestions.extend([
                "Explain this code",
                "Find bugs in this code",
                "How can I improve this?"
            ])
        elif clipboard_type == 'error':
            suggestions.extend([
                "How do I fix this error?",
                "What caused this error?",
                "Debug this for me"
            ])
        
        return suggestions[:5]  # Return top 5
    
    def get_smart_action_suggestions(
        self,
        user_question: str,
        bob_response: str,
        context_metadata: Dict[str, Any]
    ) -> list[Dict[str, str]]:
        """
        Suggest actions Edward can take based on the conversation.
        
        Args:
            user_question: User's question
            bob_response: Bob's response
            context_metadata: Context metadata
            
        Returns:
            List of action suggestions with type and description
        """
        actions = []
        question_lower = user_question.lower()
        response_lower = bob_response.lower()
        
        # Suggest file operations
        if any(word in question_lower for word in ['save', 'create', 'write']):
            actions.append({
                'type': 'file_operation',
                'action': 'save_to_file',
                'description': 'Save this to a file'
            })
        
        # Suggest opening applications
        if any(word in question_lower for word in ['open', 'launch', 'start']):
            actions.append({
                'type': 'app_launch',
                'action': 'open_application',
                'description': 'Open the mentioned application'
            })
        
        # Suggest clipboard operations
        if 'copy' in question_lower or 'clipboard' in question_lower:
            actions.append({
                'type': 'clipboard',
                'action': 'copy_to_clipboard',
                'description': 'Copy response to clipboard'
            })
        
        # Suggest code execution
        if context_metadata.get('clipboard_type') == 'code':
            actions.append({
                'type': 'code_execution',
                'action': 'run_code',
                'description': 'Run this code'
            })
        
        return actions


# Singleton instance
_context_enhancer: Optional[ContextEnhancer] = None


def get_context_enhancer() -> ContextEnhancer:
    """
    Get or create singleton context enhancer instance.
    
    Returns:
        ContextEnhancer instance
    """
    global _context_enhancer
    if _context_enhancer is None:
        _context_enhancer = ContextEnhancer()
    return _context_enhancer


# Example usage
if __name__ == "__main__":
    enhancer = ContextEnhancer()
    
    # Test with a question
    question = "What's wrong with this code?"
    enhanced, metadata = enhancer.build_enhanced_prompt(
        question,
        screenshot_base64="fake_screenshot_data",
        include_clipboard=True
    )
    
    print("Enhanced Prompt:")
    print(enhanced)
    print("\nMetadata:")
    print(metadata)
    print("\nSuggested follow-ups:")
    print(enhancer.suggest_follow_up_questions(metadata))

# Made with Bob