# Quick Start Guide

## What You Need

You already have:
- ✅ `llama3.2:3b` (text model)

You still need:
- ⬜ `llava:7b` (vision model)

## Step 1: Download Vision Model

```bash
ollama pull llava:7b
```

This will take ~5 minutes (4.7GB download).

## Step 2: Start Control API

Open a terminal and run:

```bash
python start_control_api.py
```

**Keep this terminal open!** It needs to stay running.

## Step 3: Run the Demo

Open a **second terminal** and run:

```bash
python demo_hybrid_control.py
```

## Step 4: Enter Your Task

When prompted, enter what you want the AI to do, for example:

```
Open Notepad and type 'Hello World'
```

## What Happens

1. 📸 Takes screenshot every 2 seconds
2. 👁️ `llava:7b` analyzes what's on screen
3. 🧠 `llama3.2:3b` decides what action to take
4. 📝 Shows you the action (won't execute yet because AUTO_EXECUTE_ACTIONS=false)

## To Enable Auto-Execute

When you're ready to let it actually control your computer:

1. Edit `.env`
2. Change `AUTO_EXECUTE_ACTIONS=false` to `AUTO_EXECUTE_ACTIONS=true`
3. Restart the demo

## Stop the Demo

Press `Ctrl+C` in the demo terminal.

## Troubleshooting

**"Cannot connect to Ollama"**
- Make sure Ollama is running
- Try: `ollama serve`

**"Vision model not found"**
- Run: `ollama pull llava:7b`

**"Control API not running"**
- Make sure terminal 1 is still running `start_control_api.py`

---

That's it! You're ready to go! 🚀