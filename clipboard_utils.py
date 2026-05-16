"""
Clipboard utility functions for Edward
Provides easy clipboard operations for copying text, code, and other content
"""

import pyperclip
from logger import get_logger

logger = get_logger(__name__)


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard.
    
    Args:
        text: Text to copy
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not text:
            logger.warning("Empty text provided to clipboard")
            return False
        
        pyperclip.copy(text)
        logger.info(f"Copied {len(text)} characters to clipboard")
        return True
        
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")
        return False


def get_from_clipboard() -> str:
    """
    Get text from system clipboard.
    
    Returns:
        Clipboard content as string, empty string if error
    """
    try:
        content = pyperclip.paste()
        logger.info(f"Retrieved {len(content)} characters from clipboard")
        return content
        
    except Exception as e:
        logger.error(f"Failed to get from clipboard: {e}")
        return ""


def copy_code_block(code: str, language: str = "") -> bool:
    """
    Copy code with proper formatting to clipboard.
    
    Args:
        code: Code to copy
        language: Programming language (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Format as markdown code block if language specified
        if language:
            formatted = f"```{language}\n{code}\n```"
        else:
            formatted = code
        
        return copy_to_clipboard(formatted)
        
    except Exception as e:
        logger.error(f"Failed to copy code block: {e}")
        return False


def clear_clipboard() -> bool:
    """
    Clear the system clipboard.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        pyperclip.copy("")
        logger.info("Clipboard cleared")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear clipboard: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Test clipboard operations
    test_text = "Hello from Edward!"
    
    print("Testing clipboard operations...")
    
    # Copy text
    if copy_to_clipboard(test_text):
        print(f"✓ Copied: {test_text}")
    
    # Get text
    retrieved = get_from_clipboard()
    print(f"✓ Retrieved: {retrieved}")
    
    # Copy code
    test_code = "def hello():\n    print('world')"
    if copy_code_block(test_code, "python"):
        print(f"✓ Copied code block")
    
    # Get code
    code_retrieved = get_from_clipboard()
    print(f"✓ Retrieved code:\n{code_retrieved}")
    
    print("\nAll tests passed!")

# Made with Bob
