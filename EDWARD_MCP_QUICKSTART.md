# Edward MCP Quick Start

Get Edward working with Bob in 3 steps!

## What Changed?

Edward is now an **MCP server** instead of trying to call Bob's API. This means:
- ✅ Bob calls Edward's tools directly
- ✅ No need for Bob to expose an API
- ✅ Better architecture and integration

## Quick Setup

### Step 1: Install MCP (Already Done!)

```bash
pip install mcp
```

✅ MCP is installed!

### Step 2: Add Edward to Bob's MCP Config

You need to tell Bob about Edward's MCP server. Add this to Bob's MCP configuration:

```json
{
  "mcpServers": {
    "edward": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "c:/Users/danny/OneDrive/Documents/GitHub/Bob/IBM-Bob-Hackathon-Edward",
      "env": {}
    }
  }
}
```

**Where to add this:**
- Check Bob's settings/preferences for "MCP" or "Model Context Protocol"
- Or use the provided `edward-mcp-config.json` file

### Step 3: Test It!

Ask Bob to use Edward's tools:

```
"Bob, use the capture_screenshot tool to see what's on my screen"
```

```
"Bob, use speak_text to say hello to me"
```

## Available Tools

Edward provides 8 tools:

1. **capture_screenshot** - Take a screenshot
2. **speak_text** - Speak using TTS (if enabled)
3. **store_password** - Save to encrypted vault
4. **retrieve_password** - Get from vault
5. **list_passwords** - List vault entries
6. **save_interaction** - Save to history
7. **search_history** - Search past interactions
8. **get_recent_sessions** - Get recent sessions

## Optional: Enable Voice

To enable Edward's voice:

1. Get ElevenLabs API key: https://elevenlabs.io/
2. Update `.env`:
   ```env
   TTS_ENABLED=true
   ELEVENLABS_API_KEY=your_key_here
   ELEVENLABS_VOICE_ID=your_voice_id_here
   ```

## Optional: Use Hotkey

Want to trigger Edward with Win+Shift+E?

1. Run: `python main.py`
2. Press Win+Shift+E
3. Type your question
4. Edward sends to Bob via MCP

## That's It!

Edward is ready to work with Bob as an MCP server.

**Next:** Ask Bob to use Edward's tools and see the magic happen! ✨

---

For detailed documentation, see `MCP_SETUP.md`