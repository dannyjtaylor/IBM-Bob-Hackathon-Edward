# Docker Setup for Edward Project

## Quick Start

### For Most Users (Recommended)
**Run Edward natively, not in Docker:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run Edward
python main.py
```

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for full explanation.

### For Bob API Deployment
If you're self-hosting the IBM Bob API:
```bash
# Start Bob API only
docker-compose -f docker-compose.bob-only.yml up -d

# Check it's running
curl http://localhost:6700/health

# Run Edward natively (connects to Bob API)
python main.py
```

## Files Overview

| File | Purpose | Use Case |
|------|---------|----------|
| `Dockerfile` | Edward container image | ❌ Not recommended (GUI app) |
| `docker-compose.yml` | Full stack (Edward + Bob) | ❌ Not recommended (complex) |
| `docker-compose.bob-only.yml` | Bob API only | ✅ **Recommended** |
| `.dockerignore` | Build optimization | ✅ Used by all builds |
| `DOCKER_GUIDE.md` | Complete guide | 📖 Read this first |

## Why Not Docker for Edward?

Edward is a **desktop GUI application** that needs:
- ✅ Display access for overlays
- ✅ Audio devices for TTS/STT  
- ✅ Keyboard/mouse for hotkeys
- ✅ File system for computer actions
- ✅ System tray integration

Docker adds complexity without benefits for desktop apps.

## Architecture

### Recommended Setup
```
┌─────────────────────┐
│   Your Desktop      │
│                     │
│  ┌───────────────┐  │
│  │    Edward     │  │  ← Run natively
│  │  (Python app) │  │
│  └───────┬───────┘  │
└──────────┼──────────┘
           │
           │ HTTP
           ▼
    ┌─────────────┐
    │  Bob API    │  ← Run in Docker
    │  (Container)│
    └─────────────┘
```

## Commands

### Bob API (Docker)
```bash
# Start
docker-compose -f docker-compose.bob-only.yml up -d

# Stop
docker-compose -f docker-compose.bob-only.yml down

# Logs
docker-compose -f docker-compose.bob-only.yml logs -f

# Restart
docker-compose -f docker-compose.bob-only.yml restart
```

### Edward (Native)
```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your keys

# Run
python main.py

# Test
python test_actions.py
```

## Environment Variables

### For Bob API (Docker)
```bash
# In .env or docker-compose
BOB_API_KEY=your_key_here
BOB_API_PORT=6700
```

### For Edward (Native)
```bash
# In .env
BOB_API_URL=http://localhost:6700
ELEVENLABS_API_KEY=your_key_here
USER_NAME=YourName
```

## Troubleshooting

### Bob API not starting
```bash
# Check logs
docker-compose -f docker-compose.bob-only.yml logs bob-api

# Check if port is in use
netstat -an | grep 6700

# Restart
docker-compose -f docker-compose.bob-only.yml restart
```

### Edward can't connect to Bob
```bash
# Test Bob API
curl http://localhost:6700/health

# Check .env
cat .env | grep BOB_API_URL

# Should be: BOB_API_URL=http://localhost:6700
```

### Docker build fails
```bash
# Clean build
docker-compose -f docker-compose.bob-only.yml build --no-cache

# Check Docker is running
docker ps
```

## Production Deployment

### Option 1: Local Development
- Bob API: Docker on localhost
- Edward: Native on your desktop

### Option 2: Remote Bob API
- Bob API: Docker on server
- Edward: Native on your desktop
- Update .env: `BOB_API_URL=http://your-server:6700`

### Option 3: Team Deployment
- Bob API: Docker on shared server
- Edward: Each team member runs natively
- All connect to same Bob API

## Next Steps

1. **Read the guide**: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
2. **Install natively**: Follow INSTALL.md
3. **Deploy Bob API**: Use docker-compose.bob-only.yml
4. **Run Edward**: `python main.py`

## Support

- Full guide: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)
- Installation: [INSTALL.md](INSTALL.md)
- Quick start: [QUICKSTART.md](QUICKSTART.md)
- Computer actions: [COMPUTER_ACTIONS.md](COMPUTER_ACTIONS.md)

---

**TL;DR**: Run Edward natively, optionally use Docker for Bob API. Simple and effective! 🚀