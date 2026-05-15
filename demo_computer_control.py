"""
Edward Computer Control - Interactive Demo
Run this to test the computer control system step-by-step
"""

import time
import sys
from control_client import ComputerControlClient


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def wait_for_user(message="Press Enter to continue..."):
    """Wait for user input"""
    input(f"\n{message}")


def demo_1_health_check():
    """Demo 1: Check if API is running"""
    print_header("Demo 1: Health Check")
    print("This will check if the Computer Control API is running.")
    
    try:
        client = ComputerControlClient()
        result = client.health_check()
        print(f"\n✓ API is running!")
        print(f"  Status: {result['status']}")
        return client
    except Exception as e:
        print(f"\n✗ ERROR: API is not running!")
        print(f"  {e}")
        print("\n📝 To fix this:")
        print("  1. Open a NEW terminal window")
        print("  2. Run: python start_control_api.py")
        print("  3. Wait for 'Application startup complete'")
        print("  4. Come back here and run this demo again")
        sys.exit(1)


def demo_2_screen_info(client):
    """Demo 2: Get screen information"""
    print_header("Demo 2: Screen Information")
    print("Getting your screen size and current mouse position...")
    
    # Get screen size
    screen = client.get_screen_size()
    print(f"\n📺 Screen Size: {screen['width']} x {screen['height']} pixels")
    
    # Get mouse position
    pos = client.get_mouse_position()['position']
    print(f"🖱️  Current Mouse Position: ({pos['x']}, {pos['y']})")
    
    wait_for_user()


def demo_3_mouse_movement(client):
    """Demo 3: Move the mouse"""
    print_header("Demo 3: Mouse Movement")
    print("This will move your mouse in a square pattern.")
    print("Watch your mouse cursor!")
    
    wait_for_user("Press Enter to start...")
    
    # Get screen size for calculations
    screen = client.get_screen_size()
    center_x = screen['width'] // 2
    center_y = screen['height'] // 2
    
    # Define square corners (200px from center)
    positions = [
        (center_x - 200, center_y - 200, "Top-Left"),
        (center_x + 200, center_y - 200, "Top-Right"),
        (center_x + 200, center_y + 200, "Bottom-Right"),
        (center_x - 200, center_y + 200, "Bottom-Left"),
        (center_x, center_y, "Center")
    ]
    
    print("\n🖱️  Moving mouse in a square pattern...")
    for x, y, label in positions:
        print(f"  → {label}: ({x}, {y})")
        client.move_mouse(x, y, duration=0.5)
        time.sleep(0.3)
    
    print("\n✓ Mouse movement complete!")
    wait_for_user()


def demo_4_clicking(client):
    """Demo 4: Mouse clicking"""
    print_header("Demo 4: Mouse Clicking")
    print("This will click at the current mouse position.")
    print("Move your mouse over something safe to click (like empty desktop space).")
    
    wait_for_user("Press Enter when ready...")
    
    print("\n🖱️  Clicking in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    client.click_mouse()
    print("\n✓ Click complete!")
    
    wait_for_user()


def demo_5_typing(client):
    """Demo 5: Keyboard typing"""
    print_header("Demo 5: Keyboard Typing")
    print("This will open Notepad and type a message.")
    print("\n📝 Steps:")
    print("  1. Open Run dialog (Win+R)")
    print("  2. Type 'notepad'")
    print("  3. Press Enter")
    print("  4. Type a test message")
    
    wait_for_user("Press Enter to start...")
    
    print("\n⌨️  Opening Notepad...")
    
    # Open Run dialog
    print("  → Pressing Win+R...")
    client.press_hotkey("win", "r")
    time.sleep(0.8)
    
    # Type notepad
    print("  → Typing 'notepad'...")
    client.type_text("notepad")
    time.sleep(0.3)
    
    # Press Enter
    print("  → Pressing Enter...")
    client.press_key("enter")
    time.sleep(1.5)
    
    # Type message
    print("  → Typing test message...")
    message = """Hello from Edward Computer Control! 🤖

This message was typed automatically using:
- FastAPI backend
- PyAutoGUI library
- Edward's control client

The system is working perfectly!

Current time: """ + time.strftime("%Y-%m-%d %H:%M:%S")
    
    client.type_text(message, interval=0.02)
    
    print("\n✓ Typing complete!")
    print("\n📝 Check Notepad - you should see the message!")
    
    wait_for_user()


def demo_6_hotkeys(client):
    """Demo 6: Keyboard hotkeys"""
    print_header("Demo 6: Keyboard Hotkeys")
    print("This will demonstrate hotkey combinations.")
    print("Make sure Notepad is still open with the text from Demo 5.")
    
    wait_for_user("Press Enter to continue...")
    
    print("\n⌨️  Testing hotkeys...")
    
    # Select all
    print("  → Pressing Ctrl+A (Select All)...")
    client.press_hotkey("ctrl", "a")
    time.sleep(0.5)
    
    print("  → Text should now be selected!")
    time.sleep(1)
    
    # Copy
    print("  → Pressing Ctrl+C (Copy)...")
    client.press_hotkey("ctrl", "c")
    time.sleep(0.5)
    
    # Move to end
    print("  → Pressing End (Move to end)...")
    client.press_key("end")
    time.sleep(0.3)
    
    # New line and paste
    print("  → Pressing Enter (New line)...")
    client.press_key("enter")
    time.sleep(0.3)
    
    print("  → Pressing Ctrl+V (Paste)...")
    client.press_hotkey("ctrl", "v")
    time.sleep(0.5)
    
    print("\n✓ Hotkeys complete!")
    print("📝 The text should now be duplicated in Notepad!")
    
    wait_for_user()


def demo_7_screenshot(client):
    """Demo 7: Take screenshot"""
    print_header("Demo 7: Screenshot Capture")
    print("This will take a screenshot and save it to a file.")
    
    wait_for_user("Press Enter to take screenshot...")
    
    print("\n📸 Taking screenshot...")
    result = client.take_screenshot()
    
    # Save to file
    import base64
    filename = f"edward_screenshot_{int(time.time())}.png"
    with open(filename, "wb") as f:
        f.write(base64.b64decode(result['image']))
    
    size = result['size']
    print(f"\n✓ Screenshot saved!")
    print(f"  File: {filename}")
    print(f"  Size: {size['width']} x {size['height']} pixels")
    
    wait_for_user()


def demo_8_cleanup(client):
    """Demo 8: Cleanup"""
    print_header("Demo 8: Cleanup")
    print("Let's close Notepad (without saving).")
    
    wait_for_user("Press Enter to close Notepad...")
    
    print("\n🧹 Closing Notepad...")
    
    # Alt+F4 to close
    print("  → Pressing Alt+F4...")
    client.press_hotkey("alt", "f4")
    time.sleep(0.5)
    
    # Press N for "Don't Save"
    print("  → Pressing N (Don't Save)...")
    client.press_key("n")
    time.sleep(0.3)
    
    print("\n✓ Cleanup complete!")


def main():
    """Run the interactive demo"""
    print("=" * 60)
    print("  Edward Computer Control - Interactive Demo")
    print("=" * 60)
    print("\nThis demo will test all computer control features:")
    print("  1. Health Check")
    print("  2. Screen Information")
    print("  3. Mouse Movement")
    print("  4. Mouse Clicking")
    print("  5. Keyboard Typing")
    print("  6. Keyboard Hotkeys")
    print("  7. Screenshot Capture")
    print("  8. Cleanup")
    print("\n⚠️  IMPORTANT:")
    print("  - Make sure the Control API is running first!")
    print("  - Save any important work before starting")
    print("  - You can press Ctrl+C to abort at any time")
    print("  - Move mouse to top-left corner for emergency stop")
    
    wait_for_user("\nPress Enter to start the demo...")
    
    try:
        # Run all demos
        client = demo_1_health_check()
        demo_2_screen_info(client)
        demo_3_mouse_movement(client)
        demo_4_clicking(client)
        demo_5_typing(client)
        demo_6_hotkeys(client)
        demo_7_screenshot(client)
        demo_8_cleanup(client)
        
        # Success!
        print_header("Demo Complete! 🎉")
        print("\n✓ All tests passed successfully!")
        print("\nThe Edward Computer Control system is working perfectly!")
        print("\n📚 Next steps:")
        print("  - Read COMPUTER_CONTROL_GUIDE.md for more examples")
        print("  - Integrate with Edward's main application")
        print("  - Create custom automation scripts")
        print("\n🚀 Happy automating!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        print("Exiting...")
    except Exception as e:
        print(f"\n\n✗ Error during demo: {e}")
        print("\nCheck that:")
        print("  1. The Control API is running")
        print("  2. PyAutoGUI is installed")
        print("  3. You have proper permissions")
    finally:
        print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

# Made with Bob