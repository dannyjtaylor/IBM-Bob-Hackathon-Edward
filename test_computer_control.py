"""
Test script for Edward Computer Control API
Tests all endpoints and functionality
"""

import time
import sys
from control_client import ComputerControlClient


def test_health_check(client: ComputerControlClient):
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        result = client.health_check()
        print(f"✓ Health check passed: {result}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_screen_size(client: ComputerControlClient):
    """Test screen size endpoint"""
    print("\n=== Testing Screen Size ===")
    try:
        result = client.get_screen_size()
        print(f"✓ Screen size: {result['width']}x{result['height']}")
        return True
    except Exception as e:
        print(f"✗ Screen size failed: {e}")
        return False


def test_mouse_position(client: ComputerControlClient):
    """Test mouse position endpoint"""
    print("\n=== Testing Mouse Position ===")
    try:
        result = client.get_mouse_position()
        pos = result['position']
        print(f"✓ Current mouse position: ({pos['x']}, {pos['y']})")
        return True
    except Exception as e:
        print(f"✗ Mouse position failed: {e}")
        return False


def test_mouse_movement(client: ComputerControlClient):
    """Test mouse movement"""
    print("\n=== Testing Mouse Movement ===")
    try:
        # Get current position
        start_pos = client.get_mouse_position()['position']
        print(f"Starting position: ({start_pos['x']}, {start_pos['y']})")
        
        # Move to center of screen
        screen = client.get_screen_size()
        center_x = screen['width'] // 2
        center_y = screen['height'] // 2
        
        print(f"Moving to center: ({center_x}, {center_y})")
        result = client.move_mouse(center_x, center_y, duration=0.5)
        time.sleep(0.6)
        
        # Verify position
        new_pos = client.get_mouse_position()['position']
        print(f"New position: ({new_pos['x']}, {new_pos['y']})")
        
        # Move back
        print(f"Moving back to: ({start_pos['x']}, {start_pos['y']})")
        client.move_mouse(start_pos['x'], start_pos['y'], duration=0.5)
        
        print("✓ Mouse movement test passed")
        return True
    except Exception as e:
        print(f"✗ Mouse movement failed: {e}")
        return False


def test_keyboard_keys(client: ComputerControlClient):
    """Test keyboard keys listing"""
    print("\n=== Testing Keyboard Keys ===")
    try:
        result = client.get_available_keys()
        keys = result['keys']
        print(f"✓ Available keys: {len(keys)} keys")
        print(f"Sample keys: {keys[:10]}")
        return True
    except Exception as e:
        print(f"✗ Keyboard keys failed: {e}")
        return False


def test_screenshot(client: ComputerControlClient):
    """Test screenshot capture"""
    print("\n=== Testing Screenshot ===")
    try:
        result = client.take_screenshot()
        size = result['size']
        img_len = len(result['image'])
        print(f"✓ Screenshot captured: {size['width']}x{size['height']}")
        print(f"  Base64 length: {img_len} characters")
        return True
    except Exception as e:
        print(f"✗ Screenshot failed: {e}")
        return False


def test_interactive_typing(client: ComputerControlClient):
    """Test typing (requires user to open a text editor)"""
    print("\n=== Testing Keyboard Typing (Interactive) ===")
    print("This test will type text. Please:")
    print("1. Open Notepad or any text editor")
    print("2. Click in the text area")
    print("3. Press Enter to continue...")
    
    try:
        input()  # Wait for user
        
        print("Typing test message in 2 seconds...")
        time.sleep(2)
        
        # Type test message
        test_text = "Hello from Edward Computer Control API!\nThis is a test message."
        client.type_text(test_text, interval=0.05)
        
        print("✓ Typing test completed")
        print("  Check your text editor for the message")
        return True
    except Exception as e:
        print(f"✗ Typing test failed: {e}")
        return False


def test_hotkey(client: ComputerControlClient):
    """Test hotkey press"""
    print("\n=== Testing Hotkey (Interactive) ===")
    print("This test will press Ctrl+A (select all).")
    print("Make sure you have text in a text editor.")
    print("Press Enter to continue...")
    
    try:
        input()  # Wait for user
        
        print("Pressing Ctrl+A in 2 seconds...")
        time.sleep(2)
        
        client.press_hotkey("ctrl", "a")
        
        print("✓ Hotkey test completed")
        print("  Text should be selected in your editor")
        return True
    except Exception as e:
        print(f"✗ Hotkey test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Edward Computer Control API - Test Suite")
    print("=" * 60)
    
    # Check if API is running
    print("\nChecking if API is running...")
    try:
        client = ComputerControlClient()
        client.health_check()
        print("✓ API is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"\n✗ ERROR: API is not running!")
        print(f"  {e}")
        print("\nPlease start the API first:")
        print("  python computer_control_api.py")
        return False
    
    # Run tests
    results = []
    
    # Non-interactive tests
    results.append(("Health Check", test_health_check(client)))
    results.append(("Screen Size", test_screen_size(client)))
    results.append(("Mouse Position", test_mouse_position(client)))
    results.append(("Mouse Movement", test_mouse_movement(client)))
    results.append(("Keyboard Keys", test_keyboard_keys(client)))
    results.append(("Screenshot", test_screenshot(client)))
    
    # Interactive tests (optional)
    print("\n" + "=" * 60)
    print("Interactive Tests (Optional)")
    print("=" * 60)
    print("\nWould you like to run interactive tests?")
    print("These tests will control your keyboard and mouse.")
    response = input("Run interactive tests? (y/n): ").lower()
    
    if response == 'y':
        results.append(("Typing Test", test_interactive_typing(client)))
        results.append(("Hotkey Test", test_hotkey(client)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob