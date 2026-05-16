# Computer Actions System

## Overview

Edward now has the ability to perform safe, sandboxed computer actions based on IBM Bob's responses. All actions require explicit user confirmation before execution.

## Features

### Supported Actions

1. **Create File** - Create new files with content
2. **Edit File** - Modify existing files
3. **Open File/Application** - Open files or launch applications
4. **List Directory** - View directory contents

### Safety Features

- **Sandboxed Execution**: Only allowed in user directories (Desktop, Documents, Downloads)
- **System Protection**: Blocks access to Windows, System32, Program Files, etc.
- **User Confirmation**: Every action requires explicit approval via dialog
- **Action Logging**: All actions are logged for audit trail
- **Error Handling**: Graceful failure with helpful error messages

## How It Works

### 1. Action Detection

When Bob responds to your question, the system automatically detects action requests:

```
User: "Create a file called notes.txt with my meeting notes"
Bob: "I'll create a file called 'notes.txt' with the following content:
```
Meeting Notes
- Project timeline
- Budget review
```
"
```

The system detects:
- Action Type: `CREATE_FILE`
- Target: `notes.txt`
- Content: The text in the code block

### 2. Confirmation Dialog

A confirmation dialog appears showing:
- **Description**: "Create file 'notes.txt' with 150 characters"
- **Details**: File path, content preview
- **Buttons**: Approve or Deny

### 3. Execution

If approved:
- Action is executed safely
- Result is displayed in overlay
- Success/failure is spoken via TTS

If denied:
- Action is cancelled
- User is notified

## Usage Examples

### Creating a File

**User**: "Create a Python script that prints hello world"

**Bob**: "I'll create a file called 'hello.py' with this code:
```python
print('Hello, World!')
```
"

**System**:
1. Detects CREATE_FILE action
2. Shows confirmation dialog
3. If approved, creates `hello.py` on Desktop
4. Reports: "✓ Successfully created file: C:/Users/You/Desktop/hello.py"

### Editing a File

**User**: "Update my config.json file with the new API key"

**Bob**: "I'll edit the file 'config.json' with the updated settings..."

**System**:
1. Detects EDIT_FILE action
2. Shows confirmation with old/new content
3. If approved, updates the file
4. Reports success

### Opening Applications

**User**: "Open Notepad"

**Bob**: "I'll open the application 'notepad' for you."

**System**:
1. Detects OPEN_APP action
2. Shows confirmation
3. If approved, launches Notepad
4. Reports success

## Safety Boundaries

### Allowed Directories
- `C:/Users/[Username]/Desktop`
- `C:/Users/[Username]/Documents`
- `C:/Users/[Username]/Downloads`
- `C:/Users/[Username]` (Home directory)

### Blocked Directories
- `C:/Windows`
- `C:/Program Files`
- `C:/Program Files (x86)`
- `/etc`, `/usr`, `/bin`, `/sbin` (Linux)
- Any system directories

### Example Safety Check

```python
# This will be BLOCKED:
create_file("C:/Windows/test.txt", "content")
# Result: "Path is not safe: C:/Windows/test.txt"

# This will be ALLOWED (with confirmation):
create_file("C:/Users/You/Desktop/test.txt", "content")
# Result: Shows confirmation dialog
```

## Testing

Run the test script to verify everything works:

```bash
python test_actions.py
```

This tests:
- Action detection from responses
- File operations (create, edit, list)
- Safety checks
- Full integration flow

## Architecture

### Components

1. **confirmation_handler.py**
   - Parses Bob's responses for action requests
   - Creates ActionRequest objects
   - Manages confirmation flow

2. **computer_actions.py**
   - Executes file operations safely
   - Validates paths
   - Returns structured results

3. **ui/confirmation_dialog.py**
   - Shows confirmation UI
   - Handles user approval/denial
   - Displays action details

4. **main.py** (Integration)
   - Detects actions in responses
   - Triggers confirmation flow
   - Executes approved actions
   - Reports results

### Data Flow

```
Bob Response
    ↓
Action Detection (confirmation_handler)
    ↓
Confirmation Dialog (UI)
    ↓
User Approval/Denial
    ↓
Action Execution (computer_actions)
    ↓
Result Display (overlay + TTS)
```

## Configuration

No configuration needed! The system works out of the box with safe defaults.

## Troubleshooting

### Action Not Detected

**Problem**: Bob suggests an action but nothing happens

**Solution**: The action pattern might not be recognized. Supported patterns:
- "create a file called..."
- "edit the file..."
- "open the application..."

### Permission Denied

**Problem**: "Path is not safe" error

**Solution**: The path is outside allowed directories. Use Desktop, Documents, or Downloads.

### File Already Exists

**Problem**: "File already exists" error

**Solution**: The system won't overwrite files by default. Ask Bob to edit the existing file instead.

## Future Enhancements

Potential additions:
- Delete file action
- Move/rename file action
- Run command action (with strict sandboxing)
- Batch operations
- Undo functionality
- Voice confirmation support

## Security Notes

- All actions are logged in `logs/edward.log`
- No action executes without user approval
- System directories are completely blocked
- File operations are atomic (all-or-nothing)
- Errors are caught and reported safely

## Developer Notes

### Adding New Actions

1. Add action type to `ActionType` enum in `confirmation_handler.py`
2. Add detection pattern to `action_patterns` dict
3. Implement execution in `_execute_action()` in `main.py`
4. Add corresponding function in `computer_actions.py`
5. Test thoroughly!

### Example: Adding DELETE_FILE

```python
# In confirmation_handler.py
class ActionType(Enum):
    DELETE_FILE = "delete_file"  # Add this

# In computer_actions.py
def delete_file(file_path: str) -> Dict[str, Any]:
    # Implementation here
    pass

# In main.py _execute_action()
elif action_type == ActionType.DELETE_FILE:
    return delete_file(params.get('file_path', ''))
```

## Credits

Built with ❤️ for the IBM Bob Hackathon
- Computer actions: Safe and sandboxed
- Confirmation system: User-friendly and secure
- Integration: Seamless with Edward's workflow