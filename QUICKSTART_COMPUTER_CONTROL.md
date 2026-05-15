# Quick Start: Edward Computer Control

Get Edward's computer control system up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install pyautogui fastapi uvicorn
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Step 2: Start the Control API

Open a new terminal and run:

```bash
python start_control_api.py
```

You should see:
```
✓ All dependencies installed
Starting Edward Computer Control API on port 8000...
API URL: http://127.0.0.1:8000
Documentation: http://127.0.0.1:8000/docs
```

**Keep this terminal open!** The API needs to run in the background.

## Step 3: Test the API

In another terminal, run the test suite:

```bash
python test_computer_control.py
```

This will test:
- ✓ Health check
- ✓ Screen size detection
- ✓ Mouse position tracking
- ✓ Mouse movement
- ✓ Screenshot capture
- And more...

## Step 4: Try It Out!

### Example 1: Move Mouse and Click

```python
from control_client import get_control_client

client = get_control_client()

# Move mouse to center of screen
screen = client.get_screen_size()
center_x = screen['width'] // 2
center_y = screen['height'] // 2

client.move_mouse(center_x, center_y, duration=1.0)
client.click_mouse()
```

### Example 2: Type Text

```python
from control_client import get_control_client

client = get_control_client()

# Open Notepad
client.press_hotkey("win", "r")
import time
time.sleep(0.5)
client.type_text("notepad")
client.press_key("enter")
time.sleep(1)

# Type a message
client.type_text("Hello from Edward! 🤖")
```

### Example 3: Take Screenshot

```python
from control_client import get_control_client
import base64

client = get_control_client()

# Take full screenshot
result = client.take_screenshot()

# Save to file
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(result['image']))

print(f"Screenshot saved: {result['size']['width']}x{result['size']['height']}")
```

## Step 5: Explore the API

Visit the interactive documentation:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

Try out different endpoints directly in your browser!

## Common Commands

### Mouse Control
```python
client = get_control_client()

# Move
client.move_mouse(x=500, y=300, duration=0.5)

# Click
client.click_mouse(x=500, y=300, button="left", clicks=1)

# Double-click
client.click_mouse(x=500, y=300, clicks=2, interval=0.1)

# Right-click
client.click_mouse(x=500, y=300, button="right")

# Drag
client.drag_mouse(x=700, y=400, duration=1.0)

# Scroll
client.scroll_mouse(clicks=5)  # Scroll up
client.scroll_mouse(clicks=-5)  # Scroll down
```

### Keyboard Control
```python
client = get_control_client()

# Type text
client.type_text("Hello, World!")

# Press single key
client.press_key("enter")
client.press_key("tab")
client.press_key("escape")

# Press hotkeys
client.press_hotkey("ctrl", "c")  # Copy
client.press_hotkey("ctrl", "v")  # Paste
client.press_hotkey("ctrl", "s")  # Save
client.press_hotkey("alt", "f4")  # Close window
client.press_hotkey("win", "d")   # Show desktop
```

### Screen Control
```python
client = get_control_client()

# Get screen size
size = client.get_screen_size()
print(f"Screen: {size['width']}x{size['height']}")

# Take screenshot
screenshot = client.take_screenshot()

# Take screenshot of region (x, y, width, height)
region_screenshot = client.take_screenshot(region=[100, 100, 800, 600])
```

## Safety Tips

1. **Failsafe:** Move your mouse to the top-left corner to abort any automation
2. **Test First:** Always test commands in a safe environment
3. **Add Delays:** Use `time.sleep()` between actions for reliability
4. **Save Work:** Save your work before running automation scripts

## Troubleshooting

### API Won't Start
- Check if port 8000 is already in use
- Try: `python computer_control_api.py` directly
- Check logs in `logs/control_api.log`

### Commands Not Working
- Ensure the API is running
- Check if pyautogui is installed: `python -c "import pyautogui"`
- Test with: `python test_computer_control.py`

### Mouse/Keyboard Not Responding
- Check Windows permissions
- Disable display scaling if coordinates are off
- Try running as administrator

## Next Steps

1. Read the full guide: [COMPUTER_CONTROL_GUIDE.md](COMPUTER_CONTROL_GUIDE.md)
2. Integrate with Edward's main application
3. Create custom automation scripts
4. Build workflows for repetitive tasks

## Need Help?

- Check the API docs: http://127.0.0.1:8000/docs
- Review logs: `logs/control_api.log`
- Run tests: `python test_computer_control.py`

---

**Ready to automate!** 🚀