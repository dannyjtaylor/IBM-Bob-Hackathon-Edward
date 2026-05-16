# Docker Deployment Guide for Edward

## Important: Edward is a Desktop Application

Edward is a **GUI desktop assistant** that requires:
- Display/screen access for overlays
- Audio devices for TTS and STT
- Keyboard/mouse for hotkeys and interactions
- Direct file system access for computer actions

**Recommendation**: Run Edward **natively on your desktop**, not in Docker.

## What to Dockerize

### ✅ Bob API Server (Recommended)
If you're self-hosting the IBM Bob API, Docker is perfect:

```yaml
# docker-compose.yml for Bob API only
version: '3.8'

services:
  bob-api:
    image: ibm-bob-api:latest
    container_name: bob-api
    restart: unless-stopped
    ports:
      - "6700:6700"
    environment:
      - BOB_API_PORT=6700
      - BOB_API_KEY=${BOB_API_KEY}
    volumes:
      - bob-data:/app/data
    networks:
      - bob-network

networks:
  bob-network:
    driver: bridge

volumes:
  bob-data:
    driver: local
```

Then configure Edward to connect:
```bash
# In .env
BOB_API_URL=http://localhost:6700
```

### ❌ Edward Desktop App (Not Recommended)

Running Edward in Docker requires complex setup:
- X11 forwarding for GUI
- Audio device passthrough
- Input device access
- Host filesystem mounting

This defeats the purpose of containerization and adds complexity.

## Native Installation (Recommended)

### Windows
```powershell
# Clone repository
git clone https://github.com/dannyjtaylor/IBM-Bob-Hackathon-Edward
cd IBM-Bob-Hackathon-Edward

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure .env
copy .env.example .env
# Edit .env with your API keys

# Run Edward
python main.py
```

### Linux
```bash
# Clone repository
git clone https://github.com/dannyjtaylor/IBM-Bob-Hackathon-Edward
cd IBM-Bob-Hackathon-Edward

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies
sudo apt-get install portaudio19-dev python3-pyaudio libsndfile1 ffmpeg

# Configure .env
cp .env.example .env
# Edit .env with your API keys

# Run Edward
python main.py
```

### macOS
```bash
# Clone repository
git clone https://github.com/dannyjtaylor/IBM-Bob-Hackathon-Edward
cd IBM-Bob-Hackathon-Edward

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies
brew install portaudio ffmpeg

# Configure .env
cp .env.example .env
# Edit .env with your API keys

# Run Edward
python main.py
```

## Advanced: Docker for Development

If you really want to use Docker for development (not recommended for production):

### Prerequisites
- Docker Desktop with WSL2 (Windows)
- X11 server (VcXsrv on Windows, XQuartz on Mac)
- Audio passthrough setup

### Docker Compose with GUI Support (Linux Only)

```yaml
version: '3.8'

services:
  edward-dev:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: edward-dev
    environment:
      - DISPLAY=${DISPLAY}
      - PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ${XDG_RUNTIME_DIR}/pulse:${XDG_RUNTIME_DIR}/pulse
      - ./.env:/app/.env:ro
      - ./data:/app/data
      - ./logs:/app/logs
    network_mode: host
    devices:
      - /dev/snd:/dev/snd
    privileged: true
```

**Setup on Linux:**
```bash
# Allow X11 connections
xhost +local:docker

# Run with audio
docker-compose up edward-dev
```

## Production Deployment

### Recommended Architecture

```
┌─────────────────────┐
│   User's Desktop    │
│                     │
│  ┌───────────────┐  │
│  │    Edward     │  │
│  │  (Native App) │  │
│  └───────┬───────┘  │
│          │          │
└──────────┼──────────┘
           │
           │ HTTP/WebSocket
           │
    ┌──────▼──────┐
    │  Bob API    │
    │  (Docker)   │
    └─────────────┘
```

**Benefits:**
- Edward runs natively with full desktop access
- Bob API runs in Docker for easy deployment
- Clean separation of concerns
- Easy to scale Bob API independently

### Deployment Steps

1. **Deploy Bob API** (if self-hosting):
   ```bash
   docker-compose up -d bob-api
   ```

2. **Install Edward natively**:
   ```bash
   # Follow native installation steps above
   python main.py
   ```

3. **Configure connection**:
   ```bash
   # .env
   BOB_API_URL=http://localhost:6700
   # or remote: http://your-server:6700
   ```

## Troubleshooting

### "Cannot connect to Bob API"
- Check Bob API is running: `docker ps`
- Check port is accessible: `curl http://localhost:6700/health`
- Verify .env configuration

### "Audio not working in Docker"
- Don't run Edward in Docker - use native installation
- Audio passthrough in Docker is complex and unreliable

### "GUI not showing in Docker"
- Don't run Edward in Docker - use native installation
- X11 forwarding is complex and has performance issues

## Summary

**✅ DO:**
- Run Edward natively on your desktop
- Use Docker for Bob API (if self-hosting)
- Use Docker for development/testing of backend services

**❌ DON'T:**
- Run Edward GUI in Docker (too complex, defeats purpose)
- Try to containerize desktop applications with heavy GUI/audio needs

## Alternative: Headless Mode (Future)

If you need server deployment, consider creating a headless version:
- Remove GUI components
- API-only interface
- No TTS/STT
- Webhook-based interactions

This would be Docker-friendly, but it's a different use case than the desktop assistant.

---

**Questions?** For desktop use, stick with native installation. For Bob API deployment, use Docker. Best of both worlds!