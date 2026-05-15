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
├── main.py              # Main entry point
├── agent.py             # Hotkey listener & screenshot capture
├── overlay.py           # PyQt6 overlay UI
├── tts.py               # ElevenLabs text-to-speech
├── stt.py               # Faster-whisper speech-to-text
├── wake_word.py         # OpenWakeWord detection
├── api_client.py        # IBM Bob API client
├── database.py          # Session history database
├── vault.py             # Encrypted password vault
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── data/                # Local data storage
│   ├── edward.db        # Session history
│   └── vault.db         # Password vault
├── logs/                # Application logs
│   └── edward.log
└── assets/              # Icons and resources
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

## Roadmap

- [ ] Wake word detection implementation
- [ ] Speech-to-text integration
- [ ] Computer control actions (file creation, app launching)
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
