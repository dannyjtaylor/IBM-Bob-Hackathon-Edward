# Tasks for Claude in Cursor

Hey Claude! I need your help building UI enhancements for Edward, our AI desktop assistant. Here's what needs to be done:

## 🎨 Priority 1: Visual Indicators

### Task 1: "Listening" Indicator
Create an animated visual indicator that shows when Edward is listening for speech.

**Requirements:**
- Pulsing orb or waveform animation
- Appears in overlay when microphone is active
- Colors: Use gold (#DAA520) for active, silver (#A8A9AD) for idle
- Smooth fade in/out transitions
- Should be subtle but noticeable

**Files to modify:**
- `overlay.py` - Add listening indicator widget
- Create new file: `widgets/listening_indicator.py`

**Example implementation:**
```python
# In overlay.py, add:
from widgets.listening_indicator import ListeningIndicator

class EdwardOverlay:
    def __init__(self):
        # ... existing code ...
        self.listening_indicator = ListeningIndicator(self)
        self.listening_indicator.hide()  # Hidden by default
    
    def show_listening(self):
        """Show listening indicator when mic is active"""
        self.listening_indicator.show()
        self.listening_indicator.start_animation()
    
    def hide_listening(self):
        """Hide listening indicator"""
        self.listening_indicator.stop_animation()
        self.listening_indicator.hide()
```

### Task 2: "Acting" Indicator
Create a corner widget that shows when Edward is performing an action.

**Requirements:**
- Small widget in bottom-right corner of screen
- Shows spinning icon or progress indicator
- Text: "Edward is acting..."
- Auto-hides when action completes
- Colors: Red (#B22222) for active state

**Files to create:**
- `widgets/acting_indicator.py`

**Integration:**
- Add to `main.py` to show during API calls or actions
- Should appear when Edward is executing commands

## 🔐 Priority 2: Password Manager UI

### Task 3: Master Password Dialog
Create a dialog for unlocking the password vault.

**Requirements:**
- Modal dialog with password input field
- "Unlock" and "Cancel" buttons
- Show/hide password toggle
- Error message if password is wrong
- Dark theme matching Edward's aesthetic

**Files to create:**
- `ui/password_unlock_dialog.py`

**Integration with existing vault.py:**
```python
from vault import PasswordVault

vault = PasswordVault()
# When user enters password:
if vault.unlock(master_password):
    # Show password manager
else:
    # Show error
```

### Task 4: Password Manager Main UI
Create the main password manager interface.

**Requirements:**
- List view of all stored credentials
- Columns: Service, Username, (Password hidden)
- Buttons: Add, Edit, Delete, Copy Password
- Search/filter functionality
- Double-click to copy password to clipboard

**Files to create:**
- `ui/password_manager.py`

**Integration:**
```python
# Use existing vault.py methods:
vault.store_password(service, username, password)
vault.retrieve_password(service, username)
vault.list_passwords()
vault.delete_password(service, username)
```

## ⚙️ Priority 3: Settings Dialog

### Task 5: Settings UI
Create a settings dialog for configuring Edward.

**Requirements:**
- Tabs: General, Voice, Hotkeys, Advanced
- **General Tab:**
  - User name input
  - Theme selection (if implementing multiple themes)
- **Voice Tab:**
  - Enable/disable TTS checkbox
  - Enable/disable wake word checkbox
  - Wake word sensitivity slider (0.0 - 1.0)
  - Voice selection dropdown (ElevenLabs voices)
- **Hotkeys Tab:**
  - Hotkey configuration (currently Win+Shift+E)
  - Enable/disable hotkey checkbox
- **Advanced Tab:**
  - API endpoint configuration
  - Debug mode toggle
  - Clear history button

**Files to create:**
- `ui/settings_dialog.py`

**Integration:**
- Save settings to `.env` or config file
- Apply changes without restart when possible

## 🎨 Design Guidelines

**Color Palette (from config.py):**
```python
COLORS = {
    "background": "#111111",
    "panel": "#1A1A1A",
    "red": "#B22222",
    "gold": "#DAA520",
    "silver": "#A8A9AD",
    "text": "#F0EAD6",
}
```

**Style:**
- Dark, sleek, minimal (Iron Man inspired)
- Smooth animations (300ms duration)
- No harsh transitions
- Use PySide6 for consistency with existing code

## 📁 Project Structure

```
IBM-Bob-Hackathon-Edward/
├── overlay.py          # Main overlay (already exists)
├── main.py            # Main app (already exists)
├── config.py          # Configuration (already exists)
├── ui/                # New directory for UI components
│   ├── __init__.py
│   ├── password_unlock_dialog.py
│   ├── password_manager.py
│   └── settings_dialog.py
└── widgets/           # New directory for widgets
    ├── __init__.py
    ├── listening_indicator.py
    └── acting_indicator.py
```

## 🧪 Testing

For each component, create a simple test:

```python
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Test your widget/dialog here
    widget = YourWidget()
    widget.show()
    
    sys.exit(app.exec())
```

## 📝 Notes

- All existing code uses PySide6 (not PyQt6)
- Follow the existing code style in `overlay.py`
- Use the logger from `logger.py` for debugging
- Keep UI responsive - use threads for long operations
- Test on Windows 11 (target platform)

## 🚀 Priority Order

1. Listening indicator (most visible, needed for demo)
2. Acting indicator (shows Edward is working)
3. Settings dialog (user configuration)
4. Password manager UI (nice to have)

## 💡 Tips

- Look at `overlay.py` for examples of PySide6 usage
- Use `config.COLORS` for consistent theming
- Keep animations smooth with QPropertyAnimation
- Test each component standalone before integrating

---

**Questions?** Check the existing code in `overlay.py` and `main.py` for patterns and style. Good luck! 🎨