# Edward Build - Task Division

## 🎯 Critical Path (Bob - Me)
**Goal: Get Edward working end-to-end with voice**

### Phase 1: Voice Pipeline (Priority 1)
1. ✅ Implement Porcupine wake word detection
2. ✅ Integrate faster-whisper for STT
3. ✅ Add ElevenLabs streaming TTS
4. ✅ Connect wake word → STT → Bob API → TTS pipeline
5. ✅ Add visual/audio feedback for wake/listening states
6. ✅ Test full voice flow (<3 seconds target)

### Phase 2: Polish & Integration (Priority 2)
7. ✅ Add "Edward is acting" visual indicator
8. ✅ Implement interrupt trigger ("Stop")
9. ✅ Add instant wake acknowledgment
10. ✅ Optimize performance for <2 second response
11. ✅ Test with Ollama as fallback to IBM Bob

---

## 🎨 UI/UX Tasks (Claude in Cursor)
**Goal: Polish the visual experience**

### Tasks for Claude:
1. **Enhanced Overlay UI**
   - Add animated "listening" indicator (waveform/pulsing orb)
   - Add "Edward is acting" corner widget
   - Improve color scheme consistency
   - Add smooth transitions

2. **Password Manager UI**
   - Create password manager dialog
   - Add master password unlock screen
   - Design credential list view
   - Add/edit/delete credential forms

3. **Settings Dialog**
   - Voice settings (enable/disable, voice selection)
   - Wake word sensitivity slider
   - Hotkey customization
   - Theme/color customization

4. **Tray Icon Improvements**
   - Design better tray icon (multiple states)
   - Add status indicators (sleeping/listening/thinking/acting)
   - Improve tray menu

### Prompt for Claude:
```
I'm building Edward, an AI desktop assistant. The core functionality works, but I need you to enhance the UI/UX. 

Current state:
- PySide6 overlay exists (overlay.py)
- Basic tray icon works
- Colors: background=#111111, panel=#1A1A1A, red=#B22222, gold=#DAA520, text=#F0EAD6

Tasks:
1. Add animated "listening" indicator to overlay (pulsing orb or waveform)
2. Create "Edward is acting" corner widget that appears during actions
3. Build password manager UI (master password unlock + credential management)
4. Create settings dialog for voice/wake word/hotkey configuration
5. Design better tray icon with status states

Files to modify:
- overlay.py (main UI)
- config.py (add new UI settings)
- Create new files: password_manager_ui.py, settings_dialog.py

Keep the Iron Man aesthetic - dark, sleek, minimal. Use existing color palette.
```

---

## 🐳 Backend/Infrastructure (Codex in Cursor)
**Goal: Production-ready deployment**

### Tasks for Codex:
1. **Docker Setup**
   - Create Dockerfile for Edward
   - Create docker-compose.yml
   - Include FastAPI control API
   - Include all dependencies

2. **FastAPI Enhancements**
   - Add authentication to control API
   - Add rate limiting
   - Add logging middleware
   - Create API documentation

3. **Testing Suite**
   - Unit tests for core modules
   - Integration tests for voice pipeline
   - API endpoint tests
   - Performance benchmarks

4. **Installation Scripts**
   - Windows installer script
   - Dependency checker
   - Auto-configuration wizard

### Prompt for Codex:
```
I need production-ready infrastructure for Edward, a Windows AI assistant.

Current state:
- Python 3.11+ project
- FastAPI control API (computer_control_api.py)
- Multiple dependencies (see requirements.txt)
- Runs on Windows 10/11

Tasks:
1. Create Docker setup (Dockerfile + docker-compose.yml)
2. Add authentication & rate limiting to FastAPI
3. Build comprehensive test suite (pytest)
4. Create Windows installation script (PowerShell)

Requirements:
- Docker must work on Windows with WSL2
- Tests should cover wake word, STT, TTS, API client
- Installer should check Python version, install deps, configure .env
- All scripts should be production-ready

Files to create:
- Dockerfile
- docker-compose.yml
- tests/ directory with test files
- install.ps1 (Windows installer)
- test_suite.py
```

---

## 📊 My Progress Tracking

### Completed by Bob:
- [ ] Porcupine wake word setup
- [ ] Faster-whisper integration
- [ ] ElevenLabs streaming
- [ ] Voice pipeline connection
- [ ] Visual feedback system
- [ ] Performance optimization
- [ ] Ollama fallback testing

### Completed by Claude:
- [ ] Listening indicator
- [ ] Acting indicator
- [ ] Password Manager UI
- [ ] Settings dialog
- [ ] Enhanced tray icon

### Completed by Codex:
- [ ] Docker setup
- [ ] API security
- [ ] Test suite
- [ ] Installation scripts

---

## 🎬 Final Phase (After Core Complete)
**We'll tackle together:**
1. Demo video recording
2. GitHub repo setup
3. Documentation polish
4. Submission materials (lablab.ai descriptions, slide deck)
5. IBM Bob session report export

---

## 📝 Notes
- Bob focuses on critical path (voice pipeline)
- Claude handles UI/UX polish
- Codex handles infrastructure
- All work in parallel for maximum efficiency
- Reconvene when critical path is done for final integration