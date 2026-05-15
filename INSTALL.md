# Edward Installation Guide

Complete installation instructions for Windows, including solutions for common issues.

## Quick Install (Recommended)

This installs Edward with core features (hotkey, overlay, TTS) without requiring C++ build tools:

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install core dependencies
pip install -r requirements.txt

# 3. Configure
copy .env.example .env
# Edit .env with your settings

# 4. Run Edward
python main.py
```

This gives you:
- ✅ Hotkey activation (Win+Shift+E)
- ✅ Dark overlay UI
- ✅ Text-to-speech (ElevenLabs)
- ✅ Screenshot capture
- ✅ Bob API integration
- ✅ Password vault
- ✅ Session history

**Note:** Wake word detection and speech-to-text are optional features that require additional setup (see below).

## System Requirements

- **OS:** Windows 10 or Windows 11
- **Python:** 3.11 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** 500MB for dependencies

## Step-by-Step Installation

### 1. Install Python 3.11+

Download from: https://www.python.org/downloads/

**Important:** Check "Add Python to PATH" during installation!

Verify installation:
```bash
python --version
# Should show: Python 3.11.x or higher
```

### 2. Clone or Download Edward

```bash
git clone <repository-url>
cd Edward
```

Or download and extract the ZIP file.

### 3. Create Virtual Environment

```bash
python -m venv venv
```

Activate it:
```bash
# Windows PowerShell
venv\Scripts\activate

# Windows Command Prompt
venv\Scripts\activate.bat
```

You should see `(venv)` in your prompt.

### 4. Install Core Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs everything except wake word detection and speech-to-text (which require C++ build tools).

### 5. Configure Environment

```bash
copy .env.example .env
```

Edit `.env` with your settings:
```env
USER_NAME=YourName
IBM_BOB_API_URL=http://localhost:8000
IBM_BOB_API_KEY=
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
TTS_ENABLED=true
```

### 6. Test Installation

```bash
# Test Bob API connection
python test_bob_api.py

# Test individual modules
python agent.py
python overlay.py
```

### 7. Run Edward

```bash
python main.py
```

Press **Win+Shift+E** to activate!

## Optional Features

### Speech-to-Text (faster-whisper)

**Requires:** Microsoft Visual C++ 14.0 or greater

#### Option 1: Install C++ Build Tools (Recommended)

1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run installer
3. Select "Desktop development with C++"
4. Install (requires ~7GB disk space)
5. Restart computer
6. Install faster-whisper:
   ```bash
   pip install faster-whisper==0.10.0
   ```

#### Option 2: Use Pre-built Wheels

```bash
# Install from pre-built wheels (if available)
pip install faster-whisper --only-binary :all:
```

#### Option 3: Skip Speech-to-Text

Edward works perfectly without speech-to-text! You can:
- Type questions instead of speaking
- Use the overlay text input
- Add speech-to-text later when needed

### Wake Word Detection (openwakeword)

**Requires:** Same C++ build tools as above

After installing C++ build tools:
```bash
pip install openwakeword==0.5.1
```

Or skip it - hotkey activation (Win+Shift+E) works great!

## Troubleshooting

### Error: "Microsoft Visual C++ 14.0 or greater is required"

**Problem:** Some packages (faster-whisper, openwakeword) need C++ build tools.

**Solution 1 - Skip Optional Features (Easiest):**
- Edward works without these features
- Use hotkey instead of wake word
- Type instead of speaking
- Install later if needed

**Solution 2 - Install Build Tools:**
1. Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Restart computer
4. Run: `pip install faster-whisper openwakeword`

**Solution 3 - Use Alternative Packages:**
```bash
# Use OpenAI Whisper API instead (requires API key)
pip install openai

# Or use Windows Speech Recognition (built-in)
pip install pywin32
```

### Error: "No module named 'PyQt6'"

**Problem:** Dependencies not installed.

**Solution:**
```bash
pip install -r requirements.txt
```

### Error: "python is not recognized"

**Problem:** Python not in PATH.

**Solution:**
1. Reinstall Python
2. Check "Add Python to PATH"
3. Or add manually to system PATH

### Error: "Cannot find module 'config'"

**Problem:** Running from wrong directory.

**Solution:**
```bash
cd path\to\Edward
python main.py
```

### Hotkey doesn't work

**Problem:** Win+Shift+E not triggering.

**Solutions:**
1. Run as administrator
2. Check if another app uses this hotkey
3. Verify `HOTKEY_ENABLED=true` in `.env`
4. Check logs: `logs/edward.log`

### No voice output

**Problem:** Edward doesn't speak.

**Solutions:**
1. Check `TTS_ENABLED=true` in `.env`
2. Verify ElevenLabs API key is correct
3. Check internet connection
4. Test with: `python tts.py`

### "Connection refused" to Bob API

**Problem:** Can't connect to Bob IDE.

**Solutions:**
1. Make sure Bob IDE is running
2. Run: `python test_bob_api.py`
3. Check `IBM_BOB_API_URL` in `.env`
4. Read `BOB_API_SETUP.md`

## Minimal Installation (No C++ Build Tools)

If you want to avoid C++ build tools entirely:

```bash
# Install only core dependencies
pip install PyQt6 pystray Pillow pynput mss pygame elevenlabs httpx cryptography python-dotenv aiofiles pydantic pydantic-settings fastapi uvicorn python-multipart
```

This gives you all core Edward features without optional speech components.

## Updating Edward

```bash
# Activate virtual environment
venv\Scripts\activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Update Edward
git pull  # or download new version
```

## Uninstalling

```bash
# Deactivate virtual environment
deactivate

# Delete Edward directory
cd ..
rmdir /s Edward
```

## Alternative Installation Methods

### Using Conda

```bash
conda create -n edward python=3.11
conda activate edward
pip install -r requirements.txt
```

### Using Poetry

```bash
poetry install
poetry run python main.py
```

### Using Docker (Advanced)

```dockerfile
# Dockerfile
FROM python:3.11-windowsservercore
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## Performance Tips

1. **Use SSD:** Install on SSD for faster loading
2. **Close unused apps:** Free up RAM
3. **Disable antivirus scanning:** For Edward directory (if safe)
4. **Use lightweight voice:** Choose faster ElevenLabs voice
5. **Reduce screenshot quality:** Edit `agent.py` to compress screenshots

## Security Considerations

1. **API Keys:** Never commit `.env` to git
2. **Master Password:** Use strong password for vault
3. **Firewall:** Allow Python through Windows Firewall
4. **Updates:** Keep dependencies updated
5. **Logs:** Review `logs/edward.log` periodically

## Getting Help

1. **Check logs:** `logs/edward.log`
2. **Test components:** Run individual modules
3. **Read docs:** Check all `.md` files
4. **Test API:** Run `python test_bob_api.py`
5. **GitHub Issues:** Report bugs (if applicable)

## Summary

**Minimum Requirements:**
- ✅ Python 3.11+
- ✅ Core dependencies (no C++ build tools needed)
- ✅ Bob IDE running
- ✅ 500MB disk space

**Optional:**
- C++ Build Tools (for speech features)
- ElevenLabs API (for voice)
- 7GB disk space (for C++ tools)

**Installation Time:**
- Core: 5-10 minutes
- With C++ tools: 30-60 minutes

Start with core features, add optional ones later! 🚀