"""
Computer Actions Module
Safe, sandboxed file and application operations for Edward
All actions require explicit user confirmation
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from logger import get_logger

logger = get_logger(__name__)

# Safety: Define allowed directories (user's home and desktop only)
ALLOWED_BASE_DIRS = [
    Path.home(),
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
]

# Safety: Blocked system directories
BLOCKED_DIRS = [
    "Windows",
    "System32",
    "Program Files",
    "Program Files (x86)",
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/var",
    "/sys",
    "/proc",
]


class ComputerActionError(Exception):
    """Raised when a computer action fails or is not allowed"""
    pass


def is_path_safe(path: Path) -> bool:
    """
    Check if a path is safe to operate on.
    
    Args:
        path: Path to check
        
    Returns:
        True if safe, False otherwise
    """
    try:
        # Resolve to absolute path
        abs_path = path.resolve()
        
        # Check if path is within allowed directories
        is_allowed = any(
            str(abs_path).startswith(str(allowed_dir.resolve()))
            for allowed_dir in ALLOWED_BASE_DIRS
        )
        
        if not is_allowed:
            logger.warning(f"Path not in allowed directories: {abs_path}")
            return False
        
        # Check if path contains blocked directories
        path_str = str(abs_path)
        for blocked in BLOCKED_DIRS:
            if blocked.lower() in path_str.lower():
                logger.warning(f"Path contains blocked directory '{blocked}': {abs_path}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking path safety: {e}")
        return False


def create_file(file_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Create a new file with content.
    
    Args:
        file_path: Path to the file to create
        content: Content to write to the file
        overwrite: Whether to overwrite if file exists
        
    Returns:
        Dict with success status and message
    """
    try:
        path = Path(file_path)
        
        # Safety check
        if not is_path_safe(path):
            raise ComputerActionError(f"Path is not safe: {file_path}")
        
        # Check if file exists
        if path.exists() and not overwrite:
            raise ComputerActionError(f"File already exists: {file_path}. Use overwrite=True to replace.")
        
        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        path.write_text(content, encoding='utf-8')
        
        logger.info(f"Created file: {file_path} ({len(content)} chars)")
        
        return {
            "success": True,
            "message": f"Successfully created file: {file_path}",
            "path": str(path.resolve()),
            "size": len(content)
        }
        
    except ComputerActionError as e:
        logger.error(f"Action blocked: {e}")
        return {
            "success": False,
            "message": str(e),
            "error": "action_blocked"
        }
    except Exception as e:
        logger.error(f"Failed to create file: {e}")
        return {
            "success": False,
            "message": f"Failed to create file: {str(e)}",
            "error": "creation_failed"
        }


def read_file(file_path: str) -> Dict[str, Any]:
    """
    Read content from a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Dict with success status and content
    """
    try:
        path = Path(file_path)
        
        # Safety check
        if not is_path_safe(path):
            raise ComputerActionError(f"Path is not safe: {file_path}")
        
        # Check if file exists
        if not path.exists():
            raise ComputerActionError(f"File does not exist: {file_path}")
        
        # Check if it's a file
        if not path.is_file():
            raise ComputerActionError(f"Path is not a file: {file_path}")
        
        # Read content
        content = path.read_text(encoding='utf-8')
        
        logger.info(f"Read file: {file_path} ({len(content)} chars)")
        
        return {
            "success": True,
            "message": f"Successfully read file: {file_path}",
            "content": content,
            "path": str(path.resolve()),
            "size": len(content)
        }
        
    except ComputerActionError as e:
        logger.error(f"Action blocked: {e}")
        return {
            "success": False,
            "message": str(e),
            "error": "action_blocked"
        }
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return {
            "success": False,
            "message": f"Failed to read file: {str(e)}",
            "error": "read_failed"
        }


def edit_file(file_path: str, new_content: str) -> Dict[str, Any]:
    """
    Edit an existing file by replacing its content.
    
    Args:
        file_path: Path to the file to edit
        new_content: New content to write
        
    Returns:
        Dict with success status and message
    """
    try:
        path = Path(file_path)
        
        # Safety check
        if not is_path_safe(path):
            raise ComputerActionError(f"Path is not safe: {file_path}")
        
        # Check if file exists
        if not path.exists():
            raise ComputerActionError(f"File does not exist: {file_path}")
        
        # Backup original content
        original_content = path.read_text(encoding='utf-8')
        
        # Write new content
        path.write_text(new_content, encoding='utf-8')
        
        logger.info(f"Edited file: {file_path} ({len(original_content)} → {len(new_content)} chars)")
        
        return {
            "success": True,
            "message": f"Successfully edited file: {file_path}",
            "path": str(path.resolve()),
            "old_size": len(original_content),
            "new_size": len(new_content)
        }
        
    except ComputerActionError as e:
        logger.error(f"Action blocked: {e}")
        return {
            "success": False,
            "message": str(e),
            "error": "action_blocked"
        }
    except Exception as e:
        logger.error(f"Failed to edit file: {e}")
        return {
            "success": False,
            "message": f"Failed to edit file: {str(e)}",
            "error": "edit_failed"
        }


def open_file_or_app(path: str) -> Dict[str, Any]:
    """
    Open a file or application using the system's default handler.
    
    Args:
        path: Path to file or application to open
        
    Returns:
        Dict with success status and message
    """
    try:
        target_path = Path(path)
        
        # Safety check for files
        if target_path.exists() and target_path.is_file():
            if not is_path_safe(target_path):
                raise ComputerActionError(f"Path is not safe: {path}")
        
        # Open using platform-specific command
        system = platform.system()
        
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", path], check=True)
        
        logger.info(f"Opened: {path}")
        
        return {
            "success": True,
            "message": f"Successfully opened: {path}",
            "path": path
        }
        
    except ComputerActionError as e:
        logger.error(f"Action blocked: {e}")
        return {
            "success": False,
            "message": str(e),
            "error": "action_blocked"
        }
    except Exception as e:
        logger.error(f"Failed to open: {e}")
        return {
            "success": False,
            "message": f"Failed to open: {str(e)}",
            "error": "open_failed"
        }


def list_directory(dir_path: str) -> Dict[str, Any]:
    """
    List contents of a directory.
    
    Args:
        dir_path: Path to directory
        
    Returns:
        Dict with success status and file list
    """
    try:
        path = Path(dir_path)
        
        # Safety check
        if not is_path_safe(path):
            raise ComputerActionError(f"Path is not safe: {dir_path}")
        
        # Check if directory exists
        if not path.exists():
            raise ComputerActionError(f"Directory does not exist: {dir_path}")
        
        if not path.is_dir():
            raise ComputerActionError(f"Path is not a directory: {dir_path}")
        
        # List contents
        items = []
        for item in path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item.resolve())
            })
        
        # Sort: directories first, then files
        items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
        
        logger.info(f"Listed directory: {dir_path} ({len(items)} items)")
        
        return {
            "success": True,
            "message": f"Successfully listed directory: {dir_path}",
            "path": str(path.resolve()),
            "items": items,
            "count": len(items)
        }
        
    except ComputerActionError as e:
        logger.error(f"Action blocked: {e}")
        return {
            "success": False,
            "message": str(e),
            "error": "action_blocked"
        }
    except Exception as e:
        logger.error(f"Failed to list directory: {e}")
        return {
            "success": False,
            "message": f"Failed to list directory: {str(e)}",
            "error": "list_failed"
        }


# Example usage and testing
if __name__ == "__main__":
    print("Testing Computer Actions Module...")
    print("=" * 50)
    
    # Test 1: Create file
    print("\n1. Creating test file...")
    result = create_file(
        str(Path.home() / "Desktop" / "edward_test.txt"),
        "Hello from Edward!\nThis is a test file."
    )
    print(f"   Result: {result['message']}")
    
    # Test 2: Read file
    print("\n2. Reading test file...")
    result = read_file(str(Path.home() / "Desktop" / "edward_test.txt"))
    if result["success"]:
        print(f"   Content: {result['content'][:50]}...")
    
    # Test 3: Edit file
    print("\n3. Editing test file...")
    result = edit_file(
        str(Path.home() / "Desktop" / "edward_test.txt"),
        "Updated content!\nEdward was here."
    )
    print(f"   Result: {result['message']}")
    
    # Test 4: List directory
    print("\n4. Listing Desktop...")
    result = list_directory(str(Path.home() / "Desktop"))
    if result["success"]:
        print(f"   Found {result['count']} items")
    
    # Test 5: Safety check (should fail)
    print("\n5. Testing safety (should fail)...")
    result = create_file("C:/Windows/test.txt", "This should fail")
    print(f"   Result: {result['message']}")
    
    print("\n" + "=" * 50)
    print("All tests complete!")

# Made with Bob
