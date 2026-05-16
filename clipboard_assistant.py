"""
Edward Clipboard Assistant
Analyzes clipboard content using IBM Bob
"""

import pyperclip
from typing import Optional
from logger import get_logger

logger = get_logger(__name__)


class ClipboardAssistant:
    """
    Monitors and analyzes clipboard content.
    Provides intelligent assistance based on what's copied.
    """
    
    def __init__(self):
        """Initialize clipboard assistant"""
        self.last_clipboard = ""
        logger.info("Clipboard Assistant initialized")
    
    def get_clipboard_content(self) -> Optional[str]:
        """
        Get current clipboard content.
        
        Returns:
            Clipboard text or None if empty/error
        """
        try:
            content = pyperclip.paste()
            if content and content.strip():
                return content.strip()
            return None
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
            return None
    
    def set_clipboard_content(self, text: str) -> bool:
        """
        Set clipboard content.
        
        Args:
            text: Text to copy to clipboard
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pyperclip.copy(text)
            logger.info("Content copied to clipboard")
            return True
        except Exception as e:
            logger.error(f"Error setting clipboard: {e}")
            return False
    
    def has_new_content(self) -> bool:
        """
        Check if clipboard has new content since last check.
        
        Returns:
            True if clipboard changed, False otherwise
        """
        current = self.get_clipboard_content()
        if current and current != self.last_clipboard:
            self.last_clipboard = current
            return True
        return False
    
    def analyze_content_type(self, content: str) -> str:
        """
        Determine what type of content is in clipboard.
        
        Args:
            content: Clipboard text
            
        Returns:
            Content type: 'code', 'url', 'email', 'text', 'error', 'json', 'sql'
        """
        content_lower = content.lower()
        
        # Check for code patterns
        code_indicators = ['def ', 'class ', 'import ', 'function', 'const ', 'var ', 'let ', '<?php', 'public class']
        if any(indicator in content for indicator in code_indicators):
            return 'code'
        
        # Check for URLs
        if content.startswith(('http://', 'https://', 'www.')):
            return 'url'
        
        # Check for email
        if '@' in content and '.' in content and len(content.split()) == 1:
            return 'email'
        
        # Check for error messages
        error_indicators = ['error:', 'exception:', 'traceback', 'failed', 'warning:']
        if any(indicator in content_lower for indicator in error_indicators):
            return 'error'
        
        # Check for JSON
        if content.strip().startswith(('{', '[')):
            return 'json'
        
        # Check for SQL
        sql_keywords = ['select ', 'insert ', 'update ', 'delete ', 'create table']
        if any(keyword in content_lower for keyword in sql_keywords):
            return 'sql'
        
        return 'text'
    
    def generate_context_prompt(self, content: str, user_question: str = "") -> str:
        """
        Generate a context-aware prompt for Bob based on clipboard content.
        
        Args:
            content: Clipboard content
            user_question: Optional user question
            
        Returns:
            Enhanced prompt for Bob
        """
        content_type = self.analyze_content_type(content)
        
        # Build context-aware prompt
        if user_question:
            base_prompt = user_question
        else:
            # Generate default question based on content type
            type_questions = {
                'code': "Explain what this code does and suggest improvements:",
                'error': "Help me debug this error:",
                'json': "Explain this JSON structure:",
                'sql': "Explain this SQL query:",
                'url': "Summarize what's at this URL:",
                'email': "This is an email address.",
                'text': "Summarize this text:"
            }
            base_prompt = type_questions.get(content_type, "Analyze this:")
        
        # Add clipboard content
        enhanced_prompt = f"""{base_prompt}

```
{content}
```

Please provide a clear, concise response."""
        
        return enhanced_prompt
    
    def get_smart_suggestions(self, content: str) -> list:
        """
        Get smart action suggestions based on clipboard content.
        
        Args:
            content: Clipboard content
            
        Returns:
            List of suggested actions
        """
        content_type = self.analyze_content_type(content)
        
        suggestions = {
            'code': [
                "Explain this code",
                "Find bugs in this code",
                "Optimize this code",
                "Add comments to this code"
            ],
            'error': [
                "Debug this error",
                "Explain what caused this",
                "Suggest a fix"
            ],
            'json': [
                "Explain this JSON",
                "Validate this JSON",
                "Convert to Python dict"
            ],
            'sql': [
                "Explain this query",
                "Optimize this query",
                "Find potential issues"
            ],
            'url': [
                "Open this URL",
                "Summarize this page",
                "Check if safe"
            ],
            'text': [
                "Summarize this",
                "Translate this",
                "Improve this writing"
            ]
        }
        
        return suggestions.get(content_type, ["Analyze this"])


# Singleton instance
_clipboard_assistant: Optional[ClipboardAssistant] = None


def get_clipboard_assistant() -> ClipboardAssistant:
    """
    Get or create singleton clipboard assistant instance.
    
    Returns:
        ClipboardAssistant instance
    """
    global _clipboard_assistant
    if _clipboard_assistant is None:
        _clipboard_assistant = ClipboardAssistant()
    return _clipboard_assistant


# Example usage
if __name__ == "__main__":
    assistant = ClipboardAssistant()
    
    # Test clipboard reading
    content = assistant.get_clipboard_content()
    if content:
        print(f"Clipboard content: {content[:100]}...")
        print(f"Content type: {assistant.analyze_content_type(content)}")
        print(f"Suggestions: {assistant.get_smart_suggestions(content)}")
        
        # Generate prompt
        prompt = assistant.generate_context_prompt(content)
        print(f"\nGenerated prompt:\n{prompt}")
    else:
        print("Clipboard is empty")

# Made with Bob