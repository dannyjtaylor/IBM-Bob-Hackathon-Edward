# How to Test Edward Computer Control

Follow these simple steps to test the computer control system:

## Step 1: Install Dependencies

Open PowerShell in the project directory and run:

```powershell
pip install pyautogui fastapi uvicorn httpx
```

Or install everything:

```powershell
pip install -r requirements.txt
```

## Step 2: Start the Control API

**Open a NEW terminal window** (keep it separate) and run:

```powershell
python start_control_api.py
```

You should see:
```
✓ All dependencies installed
Starting Edward Computer Control API on port 8000...
API URL: http://127.0.0.1:8000
Documentation: http://127.0.0.1:8000/docs
```

**⚠️ IMPORTANT: Keep this terminal window open!** The API needs to stay running.

## Step 3: Run the Interactive Demo

**In your ORIGINAL terminal** (not the API terminal), run:

```powershell
python demo_computer_control.py
```

This will:
1. ✅ Check if the API is running
2. 📺 Show your screen size and mouse position
3. 🖱️ Move your mouse in a square pattern
4. 🖱️ Perform a test click
5. ⌨️ Open Notepad and type a message
6. ⌨️ Test keyboard hotkeys (Ctrl+A, Ctrl+C, Ctrl+V)
7. 📸 Take a screenshot and save it
8. 🧹 Close Notepad

**The demo is interactive** - it will wait for you to press Enter between each step so you can see what's happening!

## Alternative: Quick Manual Test

If you want to test manually, here's a simple script:

```python
# test_quick.py
from control_client import get_control_client
import time

# Connect to API
client = get_control_client()

# Test 1: Get screen size
print("Screen size:", client.get_screen_size())

# Test 2: Get mouse position
print("Mouse position:", client.get_mouse_position())

# Test 3: Move mouse to center
screen = client.get_screen_size()
center_x = screen['width'] // 2
center_y = screen['height'] // 2
print(f"Moving mouse to center: ({center_x}, {center_y})")
client.move_mouse(center_x, center_y, duration=1.0)

print("✓ All tests passed!")
```

Save this as `test_quick.py` and run:
```powershell
python test_quick.py
```

## Troubleshooting

### "API is not running" error

**Solution:** Make sure you started the API in Step 2. You should have TWO terminal windows:
- Terminal 1: Running `python start_control_api.py` (API server)
- Terminal 2: Running `python demo_computer_control.py` (demo script)

### "Module not found" error

**Solution:** Install dependencies:
```powershell
pip install pyautogui fastapi uvicorn httpx
```

### Mouse/keyboard not responding

**Solution:** 
1. Make sure you're running as administrator (right-click PowerShell → Run as Administrator)
2. Check Windows permissions for accessibility
3. Try the emergency stop: Move mouse to top-left corner

### Port 8000 already in use

**Solution:** 
1. Close any other programs using port 8000
2. Or edit `computer_control_api.py` and change the port number

## What to Expect

When you run the demo, you'll see:

1. **Mouse Movement**: Your mouse will move in a square pattern automatically
2. **Notepad Opens**: Windows Run dialog opens, types "notepad", and presses Enter
3. **Text Appears**: A message will be typed into Notepad automatically
4. **Text Manipulation**: Text will be selected, copied, and pasted
5. **Screenshot Saved**: A PNG file will be created in your project folder
6. **Notepad Closes**: Notepad will close without saving

**This is all automated!** Just press Enter between steps and watch it happen.

## Safety Features

- **Failsafe**: Move your mouse to the top-left corner to abort
- **Interactive**: Demo waits for your confirmation between steps
- **Ctrl+C**: Press Ctrl+C in the terminal to stop immediately

## Next Steps

After testing:

1. ✅ Verify the API works
2. 📖 Read `COMPUTER_CONTROL_GUIDE.md` for more examples
3. 🔧 Integrate with Edward's main application
4. 🚀 Create your own automation scripts

## Need Help?

- Check API docs: http://127.0.0.1:8000/docs
- Review logs: `logs/control_api.log`
- Read the full guide: `COMPUTER_CONTROL_GUIDE.md`

---

**Ready to test!** 🚀