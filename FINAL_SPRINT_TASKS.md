# Final Sprint - Task Division

## 🎯 Goal: Complete Computer Control, Confirmations & Docker

### 📋 Bob's Tasks (Backend/Core Logic)
**Priority: Computer Control Actions + Verbal Confirmation System**

#### Task 1: Computer Control Module (`computer_actions.py`)
Create a safe, sandboxed module for file operations:
- ✅ Create new file with content
- ✅ Edit existing file (read, modify, write)
- ✅ Open application or file
- ✅ List directory contents
- ✅ Safety checks (no system files, require confirmation)

#### Task 2: Confirmation System (`confirmation_handler.py`)
Implement verbal/UI confirmation flow:
- ✅ Parse Bob's response for action requests
- ✅ Present confirmation dialog to user
- ✅ Execute action only after approval
- ✅ Support voice confirmation ("yes"/"no")
- ✅ Timeout handling (auto-cancel after 30s)

#### Task 3: Integration into Main Pipeline
Wire computer actions into Edward's response handler:
- ✅ Detect action requests in Bob's responses
- ✅ Trigger confirmation flow
- ✅ Execute approved actions
- ✅ Report results back to user

---

### 🎨 Claude's Tasks (UI/UX + Polish)
**Priority: Password Manager Wiring + ElevenLabs Voice Selection**

#### Task 1: Password Manager Backend Integration
Wire the existing UI to vault.py:
- Connect unlock dialog to vault authentication
- Wire add/edit/delete buttons to vault methods
- Implement search filtering
- Add auto-lock timer (5 min inactivity)
- Test full password workflow

#### Task 2: ElevenLabs Voice Selection UI
Add voice picker to Settings → Voice tab:
- Fetch available voices from ElevenLabs API
- Display voice list with preview buttons
- Save selected voice to .env
- Update TTS to use selected voice

#### Task 3: Visual Polish
- Add loading states to password manager
- Improve error messages
- Add tooltips to settings
- Test all UI flows

---

### 🐳 Codex's Tasks (DevOps/Infrastructure)
**Priority: Docker Setup + Deployment**

#### Task 1: Dockerfile
Create production-ready Docker image:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

#### Task 2: Docker Compose
Multi-service setup:
- Edward container (main app)
- Bob API container (if needed)
- Volume mounts for .env and vault
- Network configuration

#### Task 3: Documentation
- Update README with Docker instructions
- Add docker-compose.yml
- Create .dockerignore
- Test clean install

---

## 📊 Timeline (Next 2-3 Hours)

### Hour 1: Core Features
- **Bob**: Computer actions module (45 min)
- **Claude**: Password manager wiring (45 min)
- **Codex**: Dockerfile creation (30 min)

### Hour 2: Integration
- **Bob**: Confirmation system (45 min)
- **Claude**: Voice selection UI (45 min)
- **Codex**: Docker Compose setup (45 min)

### Hour 3: Testing & Polish
- **All**: Integration testing
- **Bob**: Wire actions into main.py
- **Claude**: Visual polish
- **Codex**: Documentation

---

## 🚀 Success Criteria

### Computer Control ✅
- [ ] Can create new files safely
- [ ] Can edit existing files
- [ ] Can open applications
- [ ] All actions require confirmation
- [ ] No access to system directories

### Confirmation System ✅
- [ ] Clear confirmation dialogs
- [ ] Voice confirmation works
- [ ] Timeout protection
- [ ] Action results displayed

### Password Manager ✅
- [ ] Unlock with master password
- [ ] Add/edit/delete credentials
- [ ] Search works
- [ ] Auto-lock after 5 min
- [ ] Copy to clipboard

### Docker ✅
- [ ] Dockerfile builds successfully
- [ ] Docker Compose runs all services
- [ ] Clean install works
- [ ] Documentation complete

---

## 📝 Notes

**Safety First:**
- Computer actions must be sandboxed
- No system file access
- All actions require explicit confirmation
- Log all actions for audit

**User Experience:**
- Confirmations should be quick and clear
- Voice confirmations should work seamlessly
- Error messages should be helpful
- UI should feel responsive

**Deployment:**
- Docker should work on Windows/Linux/Mac
- .env should be mounted, not baked in
- Vault should persist across restarts
- Logs should be accessible

---

## 🎯 After This Sprint

**High Priority:**
- Test with IBM Bob API
- Record demo video
- Export IBM Bob session report
- Write lablab.ai descriptions

**Optional:**
- Wake word integration
- Auto-lock vault refinements
- Additional computer control actions