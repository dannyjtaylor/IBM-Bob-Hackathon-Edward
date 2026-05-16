# Edward Voice Pipeline - Quick Start Guide

## 🎯 Goal
Get Edward's full voice pipeline working: Wake Word → Speech-to-Text → IBM Bob → Text-to-Speech

## ⚡ Quick Setup (5 Minutes)

### Step 1: Get API Keys

1. **Picovoice Porcupine** (Wake Word Detection)
   - Go to: https://console.picovoice.ai/
   - Sign up for free account
   - Create an access key
   - Copy the key

2. **ElevenLabs** (Text-to-Speech)
   - Go to: https://elevenlabs.io/
   - Sign up for free account
   - Get your API key from profile
   - Browse voice library and pick a voice
   - Copy voice ID

### Step 2: Configure Environment

Edit `.env` file and add your keys:

```env
# Picovoice Porcupine (Wake Word Detection)
PORCUPINE_ACCESS_KEY=your_actual_key_here

# ElevenLabs API
ELEVENLABS_API_KEY=your_actual_key_here
ELEVENLABS_VOICE_ID=your_actual_voice_id_here

# Enable features
WAKE_WORD_ENABLED=true
TTS_ENABLED=true
```

### Step 3: Install Dependencies

```powershell
cd IBM-Bob-Hackathon-Edward
pip install -r requirements.txt
```

**Note:** If PyAudio fails on Windows:
```powershell
pip install pipwin
pipwin install pyaudio
```

### Step 4: Test Components

**Test Wake Word:**
```powershell
python wake_word.py
```
Say "Jarvis" to test (we're using Jarvis as proxy for Edward)

**Test Speech-to-Text:**
```powershell
python stt.py
```
Speak when prompted

**Test Text-to-Speech:**
```powershell
python tts.py
```
Should hear Edward speak

### Step 5: Run Edward

```powershell
python main.py
```

Edward will:
- ✅ Start in system tray
- ✅ Listen for wake word "Jarvis"
- ✅ Respond to Win+Shift+E hotkey
- ✅ Capture screenshots
- ✅ Process with IBM Bob (or Ollama fallback)
- ✅ Speak responses

## 🎤 Voice Flow

```
1. Say "Jarvis" → Wake word detected
2. Edward says "Yes?" (instant acknowledgment)
3. Speak your question → STT transcribes
4. Screenshot captured automatically
5. Sent to IBM Bob API
6. Response streamed back
7. Edward speaks response via TTS
```

**Target: <2 seconds from wake to first word spoken**

## 🔧 Configuration Options

### Wake Word Sensitivity

In `.env`:
```env
WAKE_WORD_THRESHOLD=0.5  # 0.0 (sensitive) to 1.0 (strict)
```

Lower = more sensitive (more false positives)
Higher = less sensitive (might miss wake word)

### Voice Settings

```env
TTS_ENABLED=true          # Enable/disable voice
STT_MODEL=base            # Whisper model size
```

### Custom Wake Word

To use "Edward" instead of "Jarvis":
1. Go to https://console.picovoice.ai/
2. Train custom wake word "Edward"
3. Download .ppn file
4. Update wake_word.py to use custom keyword file

## 🐛 Troubleshooting

### Wake Word Not Working

**Problem:** "Porcupine access key not provided"
- **Solution:** Add `PORCUPINE_ACCESS_KEY` to `.env`

**Problem:** Wake word never triggers
- **Solution:** Increase microphone volume, reduce `WAKE_WORD_THRESHOLD`

**Problem:** Too many false positives
- **Solution:** Increase `WAKE_WORD_THRESHOLD` to 0.7 or 0.8

### Speech Recognition Issues

**Problem:** "No speech detected"
- **Solution:** Check microphone permissions, speak louder, increase timeout

**Problem:** Poor transcription accuracy
- **Solution:** Speak clearly, reduce background noise, check mic quality

### TTS Not Working

**Problem:** "TTS is disabled"
- **Solution:** Set `TTS_ENABLED=true` and add ElevenLabs API key

**Problem:** No audio output
- **Solution:** Check system volume, verify audio device

### IBM Bob API

**Problem:** "Bob API unavailable"
- **Solution:** Edward falls back to Ollama or basic responses
- **Solution:** Start Bob API server or configure Ollama

## 📊 Performance Optimization

### Reduce Latency

1. **Use Streaming TTS** (already enabled)
   - Audio starts playing before full generation

2. **Optimize STT**
   - Use `base` model for speed
   - Use `small` or `medium` for accuracy

3. **Instant Wake Acknowledgment**
   - Edward says "Yes?" immediately
   - Processing happens in background

### Resource Usage

- **Wake Word:** ~5-10 MB RAM, <1% CPU
- **STT:** ~500 MB RAM during transcription
- **TTS:** ~100 MB RAM during speech
- **Total:** ~1 GB RAM when active

## 🎯 Next Steps

### Phase 1: Core Voice (Current)
- [x] Wake word detection with Porcupine
- [x] Speech-to-text with Google SR
- [x] Text-to-speech with ElevenLabs
- [ ] Integrate all components in main.py
- [ ] Add visual feedback (listening indicator)
- [ ] Test full pipeline

### Phase 2: Enhanced Features
- [ ] Interrupt trigger ("Stop")
- [ ] Skip code blocks in TTS
- [ ] Conversation history in memory
- [ ] Faster-whisper for better STT
- [ ] Custom "Edward" wake word

### Phase 3: Polish
- [ ] Settings UI
- [ ] Voice selection
- [ ] Performance monitoring
- [ ] Error recovery

## 📝 Testing Checklist

- [ ] Wake word triggers reliably
- [ ] No false positives in normal conversation
- [ ] STT transcribes accurately
- [ ] TTS sounds natural
- [ ] Full flow completes in <3 seconds
- [ ] Hotkey still works as fallback
- [ ] Screenshot capture works
- [ ] Bob API integration works
- [ ] Ollama fallback works

## 🚀 Demo Script

For testing the full voice pipeline:

1. Start Edward: `python main.py`
2. Say "Jarvis"
3. Wait for "Yes?"
4. Say "What's on my screen?"
5. Edward captures screenshot, analyzes, responds
6. Say "Jarvis"
7. Say "Open Notepad"
8. Edward confirms and executes

## 📞 Need Help?

- Check logs in `logs/edward.log`
- Test components individually
- Verify API keys are correct
- Check microphone permissions
- Review `.env` configuration

---

**Ready to build the future of AI assistants! 🚀**