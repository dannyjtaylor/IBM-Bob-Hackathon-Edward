# Edward Quick Start Guide

Get Edward up and running in 5 minutes!

## Prerequisites

- ✅ Windows 10/11
- ✅ Python 3.11+
- ✅ Bob IDE running (for AI responses)
- ✅ ElevenLabs account (for voice, optional)

## Installation

### 1. Install Dependencies

```bash
# Run the setup script
python setup.py

# Or manually:
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.env` file:

```env
# Required: Your name
USER_NAME=Danny

# Required: Bob IDE API (already configured for localhost)
IBM_BOB_API_URL=http://localhost:8000
IBM_BOB_API_KEY=

# Optional: ElevenLabs for voice (can skip for now)
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

# Optional: Disable voice if you don't have ElevenLabs
TTS_ENABLED=false
```

### 3. Test Bob API Connection

```bash
python test_bob_api.py
```

This will:
- ✅ Check if Bob IDE's API is accessible
- ✅ Test different endpoint configurations
- ✅ Show you which endpoints work

### 4. Start Edward

```bash
python main.py
```

You should see:
- ✅ Edward icon in system tray
- ✅ "Edward is running" message
- ✅ Ready to accept hotkey

## Usage

### Hotkey Activation (Recommended)

1. **Press Win+Shift+E** anywhere in Windows
2. Edward captures your screen and shows overlay
3. Type your question in the text box
4. Click "Ask Edward" or press Ctrl+Enter
5. Edward responds with text (and voice if enabled)

### System Tray

Right-click Edward's tray icon:
- **Show Edward** - Open overlay manually
- **Exit** - Close Edward

## Troubleshooting

### "Connection refused" error

**Problem:** Edward can't connect to Bob IDE

**Solutions:**
1. Make sure Bob IDE is running
2. Check if Bob IDE uses a different port
3. Read `BOB_API_SETUP.md` for detailed instructions
4. Run `python test_bob_api.py` to diagnose

### "Module not found" error

**Problem:** Missing Python dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### Hotkey doesn't work

**Problem:** Win+Shift+E not triggering Edward

**Solutions:**
1. Make sure Edward is running (check system tray)
2. Check if another app is using Win+Shift+E
3. Try running as administrator
4. Check `HOTKEY_ENABLED=true` in `.env`

### No voice output

**Problem:** Edward responds but doesn't speak

**Solutions:**
1. This is normal if you haven't configured ElevenLabs
2. Set `TTS_ENABLED=false` in `.env` to disable voice
3. Or get ElevenLabs API key and configure it

### Overlay doesn't appear

**Problem:** Hotkey works but no overlay shows

**Solutions:**
1. Check if overlay is behind other windows
2. Try pressing Esc and triggering again
3. Check logs in `logs/edward.log`

## Getting ElevenLabs API Key (Optional)

If you want Edward to speak:

1. Go to https://elevenlabs.io/
2. Sign up for free account
3. Go to Profile → API Keys
4. Copy your API key
5. Choose a voice and copy its ID
6. Update `.env`:
   ```env
   ELEVENLABS_API_KEY=your_actual_key
   ELEVENLABS_VOICE_ID=your_voice_id
   TTS_ENABLED=true
   ```

## Getting Bob IDE API Key

See `BOB_API_SETUP.md` for detailed instructions.

**Quick version:**
1. Bob IDE is already configured for `localhost:8000`
2. Run `python test_bob_api.py` to verify
3. If it doesn't work, check Bob IDE's settings for API configuration
4. Update `IBM_BOB_API_URL` in `.env` if needed

## Next Steps

### Customize Edward

Edit `.env` to customize:
- Your name (`USER_NAME`)
- Enable/disable voice (`TTS_ENABLED`)
- Enable/disable wake word (`WAKE_WORD_ENABLED`)
- Change hotkey settings

### Use Password Vault

Edward includes an encrypted password manager:

```python
from vault import PasswordVault

# Create vault with master password
vault = PasswordVault(master_password="your_secure_password")

# Add password
vault.add_password("Gmail", "you@example.com", "password123", "Personal email")

# Retrieve password
entry = vault.get_password("Gmail", "you@example.com")
print(entry["password"])
```

**Important:** Passwords are encrypted and NEVER sent to any API!

### View Session History

Edward tracks all your interactions:

```python
from database import get_database

db = get_database()

# Get recent sessions
sessions = db.get_recent_sessions(limit=10)

# Search interactions
results = db.search_interactions("python")
```

## File Structure

```
Edward/
├── main.py              # Start here
├── agent.py             # Hotkey listener
├── overlay.py           # UI overlay
├── tts.py               # Text-to-speech
├── config.py            # Configuration
├── .env                 # Your settings (edit this!)
├── test_bob_api.py      # Test Bob connection
├── BOB_API_SETUP.md     # Detailed API setup
└── QUICKSTART.md        # This file
```

## Common Commands

```bash
# Start Edward
python main.py

# Test Bob API
python test_bob_api.py

# Run setup
python setup.py

# Test individual modules
python agent.py
python overlay.py
python tts.py
```

## Tips

1. **Start simple:** Get basic text responses working first, add voice later
2. **Check logs:** Look in `logs/edward.log` if something goes wrong
3. **Test components:** Run individual modules to test them separately
4. **Read docs:** Check `BOB_API_SETUP.md` for API configuration help

## Getting Help

1. Check `logs/edward.log` for error messages
2. Run `python test_bob_api.py` to diagnose connection issues
3. Read `BOB_API_SETUP.md` for detailed API setup
4. Check if Bob IDE is running and accessible

## Summary

**Minimum to get started:**
1. ✅ Install dependencies: `python setup.py`
2. ✅ Edit `.env`: Set your name
3. ✅ Test Bob API: `python test_bob_api.py`
4. ✅ Start Edward: `python main.py`
5. ✅ Press Win+Shift+E to test!

**Optional enhancements:**
- Configure ElevenLabs for voice
- Enable wake word detection
- Customize colors and settings

---

**Edward is ready. Let's get to work.** 🚀