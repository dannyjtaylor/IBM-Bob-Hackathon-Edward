# Edward Computer Control System

This guide explains how to use Edward's new computer control capabilities through the FastAPI backend.

## Overview

Edward now has a local FastAPI server that provides direct mouse and keyboard control using `pyautogui`. This eliminates the need for external APIs for basic computer control tasks.

## Architecture

```
┌─────────────────┐
│  Edward Main    │
│  Application    │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
┌────────▼────────┐  ┌────▼──────────────┐
│  Control Client │  │  Computer Control │
│  (HTTP Client)  │──│  API (FastAPI)    │
└─────────────────┘  └────┬──────────────┘
                          │
                     ┌────▼────────┐
                     │  PyAutoGUI  │
                     │  (OS Level) │
                     └─────────────┘
```

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify pyautogui is installed:**
   ```bash
   python -c "import pyautogui; print(pyautogui.__version__)"
   ```

## Starting the Control API

### Option 1: Run as standalone server
```bash
python computer_control_api.py
```

The API will start on `http://127.0.0.1:8000`

### Option 2: Run with uvicorn
```bash
uvicorn computer_control_api:app --host 127.0.0.1 --port 8000
```

### Option 3: Run in background (Windows)
```powershell
Start-Process python -ArgumentList "computer_control_api.py" -WindowStyle Hidden
```

## API Documentation

Once the server is running, visit:
- **Interactive docs:** http://127.0.0.1:8000/docs
- **Alternative docs:** http://127.0.0.1:8000/redoc

## Using the Control Client

### Basic Usage

```python
from control_client import get_control_client

# Get the client
client = get_control_client()

# Move mouse
client.move_mouse(x=500, y=300, duration=0.5)

# Click
client.click_mouse(x=500, y=300, button="left", clicks=1)

# Type text
client.type_text("Hello, World!")

# Press keys
client.press_key("enter")

# Hotkeys
client.press_hotkey("ctrl", "c")  # Copy
client.press_hotkey("ctrl", "v")  # Paste
```

### Context Manager

```python
from control_client import ComputerControlClient

with ComputerControlClient() as client:
    client.move_mouse(100, 100)
    client.click_mouse()
```

## Available Endpoints

### Mouse Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mouse/move` | POST | Move mouse to coordinates |
| `/mouse/click` | POST | Click mouse button |
| `/mouse/drag` | POST | Drag mouse to coordinates |
| `/mouse/scroll` | POST | Scroll mouse wheel |
| `/mouse/position` | GET | Get current mouse position |

### Keyboard Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/keyboard/type` | POST | Type text |
| `/keyboard/press` | POST | Press a key |
| `/keyboard/hotkey` | POST | Press key combination |
| `/keyboard/keys` | GET | List available keys |

### Screen Control

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/screen/screenshot` | POST | Take screenshot |
| `/screen/size` | GET | Get screen dimensions |

## Examples

### Example 1: Open Notepad and Type

```python
from control_client import get_control_client
import time

client = get_control_client()

# Open Run dialog
client.press_hotkey("win", "r")
time.sleep(0.5)

# Type notepad
client.type_text("notepad")
time.sleep(0.3)

# Press Enter
client.press_key("enter")
time.sleep(1)

# Type some text
client.type_text("Hello from Edward!\nThis is automated typing.")
```

### Example 2: Take Screenshot of Region

```python
from control_client import get_control_client
import base64

client = get_control_client()

# Take screenshot of region (x, y, width, height)
result = client.take_screenshot(region=[100, 100, 800, 600])

# Get base64 image
img_base64 = result["image"]

# Save to file
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(img_base64))
```

### Example 3: Automated Form Filling

```python
from control_client import get_control_client
import time

client = get_control_client()

# Click on first field
client.click_mouse(x=300, y=200)
time.sleep(0.2)

# Type name
client.type_text("John Doe")

# Tab to next field
client.press_key("tab")
time.sleep(0.2)

# Type email
client.type_text("john@example.com")

# Tab to next field
client.press_key("tab")
time.sleep(0.2)

# Type message
client.type_text("This is an automated message from Edward.")

# Submit form
client.press_key("tab")
client.press_key("enter")
```

### Example 4: Browser Automation

```python
from control_client import get_control_client
import time

client = get_control_client()

# Open browser with Ctrl+T (new tab)
client.press_hotkey("ctrl", "t")
time.sleep(0.5)

# Type URL
client.type_text("https://www.example.com")
client.press_key("enter")
time.sleep(2)

# Scroll down
client.scroll_mouse(clicks=-5)  # Negative = scroll down
time.sleep(1)

# Take screenshot
result = client.take_screenshot()
print(f"Screenshot taken: {result['size']}")
```

## Integration with Edward

### Using in Edward's Agent

You can integrate the control client into Edward's agent for autonomous actions:

```python
from control_client import get_control_client

class EdwardAgent:
    def __init__(self):
        self.control = get_control_client()
    
    def execute_action(self, action: str, params: dict):
        """Execute a computer control action"""
        if action == "click":
            self.control.click_mouse(**params)
        elif action == "type":
            self.control.type_text(**params)
        elif action == "move":
            self.control.move_mouse(**params)
        # ... more actions
```

### Using with Bob AI

When Bob AI needs to control the computer, it can send commands to Edward:

```python
# In your Bob integration
async def handle_bob_command(command: dict):
    client = get_control_client()
    
    if command["type"] == "click":
        client.click_mouse(
            x=command["x"],
            y=command["y"]
        )
    elif command["type"] == "type":
        client.type_text(command["text"])
```

## Safety Features

### PyAutoGUI Failsafe

PyAutoGUI has a built-in failsafe: **move your mouse to the top-left corner** of the screen to abort any running automation.

### Pause Between Actions

The API includes a 0.1-second pause between actions by default. You can adjust this in `computer_control_api.py`:

```python
pyautogui.PAUSE = 0.1  # Adjust as needed
```

### Timeouts

All API requests have a 30-second timeout to prevent hanging.

## Troubleshooting

### API Not Starting

1. Check if port 8000 is already in use:
   ```bash
   netstat -ano | findstr :8000
   ```

2. Try a different port:
   ```bash
   uvicorn computer_control_api:app --port 8001
   ```

### PyAutoGUI Not Working

1. **Windows:** Ensure you have proper permissions
2. **Check display scaling:** PyAutoGUI coordinates may be affected by display scaling
3. **Test manually:**
   ```python
   import pyautogui
   pyautogui.position()  # Should return current mouse position
   ```

### Connection Refused

Make sure the API server is running:
```bash
curl http://127.0.0.1:8000/health
```

## Advanced Usage

### Custom API Port

```python
from control_client import ComputerControlClient

client = ComputerControlClient(base_url="http://127.0.0.1:8001")
```

### Async Operations

For async code, use `httpx.AsyncClient`:

```python
import httpx
import asyncio

async def async_control():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/mouse/move",
            json={"x": 500, "y": 300, "duration": 0.5}
        )
        return response.json()

asyncio.run(async_control())
```

### Error Handling

```python
from control_client import get_control_client
import httpx

client = get_control_client()

try:
    client.move_mouse(1000, 1000)
except httpx.HTTPError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Local Only:** The API binds to `127.0.0.1` (localhost only) by default
2. **No Authentication:** Currently no authentication - only use locally
3. **Firewall:** Ensure your firewall blocks external access to port 8000
4. **Trusted Code:** Only run automation scripts from trusted sources

## Next Steps

1. **Start the API server** in a separate terminal
2. **Test basic commands** using the examples above
3. **Integrate with Edward** for autonomous actions
4. **Create custom automation scripts** for your workflows

## Support

For issues or questions:
- Check the logs in `logs/control_api.log`
- Review the API documentation at http://127.0.0.1:8000/docs
- Test individual endpoints using the interactive docs

---

**Made with Bob** 🤖