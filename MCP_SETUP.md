# Edward MCP Server Setup Guide

Edward is now available as an **MCP (Model Context Protocol) server** that Bob can use directly!

## What is MCP?

MCP allows Bob to call Edward's desktop integration tools directly, without Edward needing to call an external API. This is a much better architecture:

```
Old: Edward → tries to call Bob API → ❌ doesn't exist
New: Bob → calls Edward MCP server → ✅ Edward provides tools
```

## Available Tools

Edward exposes these tools via MCP:

### 1. `capture_screenshot`
Capture a screenshot of Danny's screen
- **Input**: `monitor` (optional, default: 1)
- **Output**: Base64-encoded PNG image

### 2. `speak_text`
Speak text aloud using ElevenLabs TTS
- **Input**: `text` (required)
- **Output**: Confirmation message
- **Note**: Only works if TTS is enabled in `.env`

### 3. `store_password`
Store a password in encrypted vault
- **Input**: `service`, `username`, `password`, `master_password`, `notes` (optional)
- **Output**: Confirmation message
- **Security**: Passwords encrypted with AES-128, never sent to external APIs

### 4. `retrieve_password`
Retrieve a password from vault
- **Input**: `service`, `username`, `master_password`
- **Output**: Password details

### 5. `list_passwords`
List all services in vault (without revealing passwords)
- **Input**: `master_password`
- **Output**: List of services and usernames

### 6. `save_interaction`
Save an interaction to session history
- **Input**: `question`, `response`, `screenshot_path` (optional)
- **Output**: Session ID

### 7. `search_history`
Search interaction history
- **Input**: `query`, `limit` (optional, default: 10)
- **Output**: Matching interactions

### 8. `get_recent_sessions`
Get recent interaction sessions
- **Input**: `limit` (optional, default: 5)
- **Output**: Recent sessions with interaction counts

## Installation

### 1. Install MCP Package

```bash
pip install mcp
```

✅ Already done!

### 2. Configure Bob to Use Edward MCP Server

Add Edward to Bob's MCP configuration. The config file location depends on your Bob setup:

**Option A: Add to Bob's MCP config file**

Find Bob's MCP configuration file (usually in Bob's settings or config directory) and add:

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

**Option B: Use the provided config file**

We've created `edward-mcp-config.json` in this directory. Point Bob to use this config file.

### 3. Test the MCP Server

Run the MCP server directly to test:

```bash
python mcp_server.py
```

The server will start and wait for MCP protocol messages via stdin/stdout.

## Usage Examples

Once configured, you (Bob) can call Edward's tools:

### Example 1: Capture Screenshot
```
Bob: Use the capture_screenshot tool to see what's on Danny's screen
```

### Example 2: Speak Text
```
Bob: Use speak_text to say "Hello Danny, I'm ready to help"
```

### Example 3: Store Password
```
Bob: Use store_password to save Danny's GitHub credentials
- service: "GitHub"
- username: "danny@example.com"
- password: "secret123"
- master_password: "danny_master_pass"
```

### Example 4: Search History
```
Bob: Use search_history to find previous conversations about Python
- query: "Python"
- limit: 5
```

## How It Works

1. **Bob calls Edward's MCP tools** when needed
2. **Edward executes the tool** (screenshot, TTS, vault, etc.)
3. **Edward returns results** to Bob
4. **Bob uses the results** to provide intelligent responses

## Architecture Benefits

✅ **No external API needed** - Edward doesn't need to call Bob's API
✅ **Direct integration** - Bob calls Edward's tools directly via MCP
✅ **Secure** - All data stays local, passwords never leave the machine
✅ **Flexible** - Bob decides when to use Edward's tools
✅ **Efficient** - No HTTP overhead, direct process communication

## Hotkey Integration (Optional)

You can still use Edward's hotkey (Win+Shift+E) for manual activation:

1. Run `python main.py` to start Edward's hotkey listener
2. Press Win+Shift+E to capture screenshot and show overlay
3. Type question in overlay
4. Edward sends to Bob via MCP
5. Bob responds using Edward's tools

## Configuration

Edward's behavior is controlled by `.env`:

```env
# Your name
USER_NAME=Danny

# TTS (optional)
TTS_ENABLED=false
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here

# Hotkey
HOTKEY_ENABLED=true
```

## Troubleshooting

### MCP server won't start
- Check Python version: `python --version` (need 3.11+)
- Verify MCP installed: `pip show mcp`
- Check for errors: `python mcp_server.py`

### Tools not working
- **Screenshot**: Requires `mss` package
- **TTS**: Requires ElevenLabs API key in `.env`
- **Vault**: Requires `cryptography` package
- **History**: Requires SQLite (built into Python)

### Bob can't find Edward
- Verify MCP config path is correct
- Check `cwd` points to Edward's directory
- Ensure `python` command works in terminal

## Next Steps

1. **Configure Bob** to use Edward's MCP server
2. **Test tools** by asking Bob to use them
3. **Enable TTS** (optional) by adding ElevenLabs API key
4. **Use hotkey** (optional) by running `python main.py`

## Summary

**Edward is now an MCP server!**

- ✅ MCP server created (`mcp_server.py`)
- ✅ 8 tools exposed for Bob to use
- ✅ Config file ready (`edward-mcp-config.json`)
- ✅ All dependencies installed

**To use:**
1. Add Edward to Bob's MCP configuration
2. Ask Bob to use Edward's tools
3. Enjoy seamless desktop integration!

---

**Edward is ready. Let's get to work.** 🚀