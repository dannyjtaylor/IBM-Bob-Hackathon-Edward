# Edward - Local Windows Desktop AI Assistant

Edward is a local Windows desktop AI assistant inspired by Jarvis from Iron Man. It runs silently in your system tray, responds to hotkeys and wake words, and helps you with tasks while maintaining your privacy.

## Features

- 🎯 **Hotkey Activation**: Trigger Edward with Win+Shift+E
- 🗣️ **Wake Word Detection**: Say "Hey Ed", "Hey Edward", or "Edward"
- 📸 **Context-Aware**: Captures screenshots for visual context
- 🎨 **Dark Overlay UI**: Sleek, minimal interface with Iron Man-inspired colors
- 🔊 **Text-to-Speech**: Natural voice responses using ElevenLabs
- 🔒 **Local Password Vault**: Encrypted password manager (never sent to APIs)
- 💾 **Session History**: Tracks all interactions locally
- 🤖 **IBM Bob Integration**: Powered by IBM Bob AI via API
- 🖱️ **Computer Control**: Direct mouse and keyboard control via local API
- 🤖 **Autonomous Control**: AI-driven computer control with IBM Watsonx Vision

## Color Palette

- Background: `#111111`
- Panel: `#1A1A1A`
- Red: `#B22222`
- Gold: `#DAA520`
- Silver: `#A8A9AD`
- Text: `#F0EAD6`

## Tech Stack

- **Python 3.11**
- **PyQt6** - Overlay UI
- **pystray** - System tray integration
- **mss** - Screenshot capture
- **pynput** - Global hotkey listener
- **faster-whisper** - Speech-to-text
- **OpenWakeWord** - Wake word detection
- **ElevenLabs** - Text-to-speech
- **SQLite** - Local database
- **cryptography** - Password encryption
- **FastAPI** - Computer control API
- **PyAutoGUI** - Mouse and keyboard automation

## Installation

### Prerequisites

- Python 3.11 or higher
- Windows 10/11
- ElevenLabs API key
- IBM Bob API access

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Edward
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   - `ELEVENLABS_API_KEY` - Your ElevenLabs API key
   - `ELEVENLABS_VOICE_ID` - Your preferred voice ID
   - `IBM_BOB_API_URL` - IBM Bob API endpoint
   - `IBM_BOB_API_KEY` - Your IBM Bob API key
   - `USER_NAME` - Your name (Edward will use this)

5. **Run Edward**
   ```bash
   python main.py
   ```

## Usage

### Hotkey Activation

1. Press **Win+Shift+E** anywhere in Windows
2. Edward captures a screenshot and shows the overlay
3. Type or speak your question
4. Click "Ask Edward" or press Ctrl+Enter
5. Edward responds with text and voice

### Wake Word Activation

1. Say "Hey Edward", "Hey Ed", or "Edward"
2. Edward activates and listens for your question
3. Speak your question naturally
4. Edward responds

### System Tray

- Right-click the Edward icon in the system tray
- **Show Edward** - Open the overlay manually
- **Settings** - Configure Edward (coming soon)
- **Exit** - Close Edward

## Project Structure

```
Edward/
├── main.py                      # Main entry point
├── agent.py                     # Hotkey listener & screenshot capture
├── overlay.py                   # PyQt6 overlay UI
├── tts.py                       # ElevenLabs text-to-speech
├── stt.py                       # Faster-whisper speech-to-text
├── wake_word.py                 # OpenWakeWord detection
├── api_client.py                # IBM Bob API client
├── computer_control_api.py      # FastAPI computer control server
├── control_client.py            # Computer control API client
├── start_control_api.py         # Control API startup script
├── test_computer_control.py     # Control API test suite
├── database.py                  # Session history database
├── vault.py                     # Encrypted password vault
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── COMPUTER_CONTROL_GUIDE.md    # Computer control documentation
├── data/                        # Local data storage
│   ├── edward.db                # Session history
│   └── vault.db                 # Password vault
├── logs/                        # Application logs
│   ├── edward.log
│   └── control_api.log
└── assets/                      # Icons and resources
```

## Personality

Edward has a dry wit, calm demeanor, and precise communication style:

- Calls you by your name
- Never hallucinates or makes assumptions
- Always asks for confirmation before taking actions
- Provides short, spoken-friendly responses
- No markdown or bullet points in speech
- Occasionally sharp but always helpful

## Security & Privacy

- **Local-First**: All data stored locally on your machine
- **Encrypted Vault**: Passwords encrypted with Fernet (AES-128)
- **No Data Leaks**: Password vault never sends data to external APIs
- **Session History**: Stored locally in SQLite database
- **Screenshot Privacy**: Screenshots only sent to IBM Bob API when you ask a question

## Development

### Running Tests

```bash
# Test individual modules
python agent.py
python overlay.py
python tts.py
```

### Adding Features

1. Create new module in project root
2. Import in `main.py`
3. Integrate with Edward class
4. Update configuration in `config.py`

## Computer Control

Edward now includes a powerful computer control system that allows direct mouse and keyboard automation:

### Quick Start

1. **Start the Control API:**
   ```bash
   python start_control_api.py
   ```

2. **Test the API:**
   ```bash
   python test_computer_control.py
   ```

3. **Use in your code:**
   ```python
   from control_client import get_control_client
   
   client = get_control_client()
   client.move_mouse(500, 300)
   client.click_mouse()
   client.type_text("Hello, World!")
   ```

For detailed documentation, see [COMPUTER_CONTROL_GUIDE.md](COMPUTER_CONTROL_GUIDE.md)

## Autonomous Computer Control (NEW! 🚀)

Edward now features AI-driven autonomous computer control with **two options**:

### Option 1: Local AI with Ollama (Recommended) 🏠

Run everything locally on your laptop - no cloud, no API costs, complete privacy!

**Quick Start:**
1. Install Ollama from https://ollama.ai
2. Download model: `ollama pull llava:13b`
3. Start Control API: `python start_control_api.py`
4. Run Demo: `python demo_ollama_control.py`

**Perfect for your Intel Arc 140V GPU (8GB) + 16GB RAM!**

**Documentation:**
- [Quick Start (5 min)](QUICKSTART_OLLAMA.md) - Get running fast
- [Full Setup Guide](OLLAMA_SETUP_GUIDE.md) - Complete instructions

### Option 2: Cloud AI with IBM Watsonx ☁️

Use IBM's cloud-based vision AI (requires API key).

**Quick Start:**
1. Get credentials from [IBM Cloud](https://cloud.ibm.com/)
2. Configure `.env` with `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`
3. Start Control API: `python start_control_api.py`
4. Run Demo: `python demo_autonomous_control.py`

**Documentation:**
- [Quick Start Guide](QUICKSTART_AUTONOMOUS_CONTROL.md)
- [Full Documentation](AUTONOMOUS_CONTROL_GUIDE.md)

### Features (Both Options)

- 📸 **Periodic Screenshots**: Captures screen every 2 seconds (configurable)
- 🧠 **AI Vision Analysis**: Understands what's on your screen
- 🎯 **Smart Actions**: AI decides mouse movements, clicks, typing, etc.
- 🔒 **Safety Controls**: Manual confirmation mode, failsafe features
- 📊 **Action History**: Track all AI decisions and actions

### Example: Local Ollama

```python
from ollama_control_processor import OllamaAutonomousLoop

# Create autonomous control loop
control_loop = OllamaAutonomousLoop(
    task_description="Open Notepad and type 'Hello World'",
    ollama_model="llava:13b",
    screenshot_interval=2.0,
    auto_execute=True
)

# Start AI control
await control_loop.start()
```

### Comparison

| Feature | Ollama (Local) | Watsonx (Cloud) |
|---------|----------------|-----------------|
| Cost | ✅ FREE | ❌ Pay per API call |
| Privacy | ✅ 100% Local | ⚠️ Data sent to cloud |
| Speed | ✅ Fast (no network) | ⚠️ Network dependent |
| Setup | ⚠️ Requires GPU | ✅ No GPU needed |
| Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Recommendation**: Use Ollama for privacy, cost savings, and speed!

## Roadmap

- [x] Computer control API with mouse/keyboard automation
- [x] Autonomous AI-driven computer control with Watsonx Vision
- [ ] Wake word detection implementation
- [ ] Speech-to-text integration
- [ ] Settings UI
- [ ] Multi-monitor support
- [ ] Custom voice training
- [ ] Plugin system
- [ ] Mobile companion app

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.

## Acknowledgments

- Inspired by Jarvis from Iron Man
- Powered by IBM Bob AI
- Voice by ElevenLabs
- Built with love for productivity and privacy

---

**Edward**: *"Ready when you are, sir."*
