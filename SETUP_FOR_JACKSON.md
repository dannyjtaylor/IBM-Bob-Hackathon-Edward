# Edward MCP Server Setup for Jackson

## ✅ What's Been Configured

1. **MCP Configuration Updated** - `edward-mcp-config.json` now points to your system path:
   ```json
   {
     "mcpServers": {
       "edward": {
         "command": "python",
         "args": ["mcp_server.py"],
         "cwd": "C:/Users/BoppJ/Desktop/IBM-Bob-Hackathon-Edward",
         "env": {}
       }
     }
   }
   ```

2. **Environment File Created** - `.env` configured with:
   - USER_NAME=Jackson
   - TTS_ENABLED=false (disabled for now, can enable later with ElevenLabs API key)

3. **Dependencies Updated** - `requirements.txt` updated to work with Python 3.13

## 🚀 Next Steps

### Step 1: Verify Installation (Currently Running)
The Python dependencies are being installed. Once complete, verify with:
```powershell
cd IBM-Bob-Hackathon-Edward
python -c "import mcp; print('MCP installed successfully')"
```

### Step 2: Test Edward MCP Server
Run the MCP server to ensure it works:
```powershell
cd IBM-Bob-Hackathon-Edward
python mcp_server.py
```

You should see:
```
🎉 Edward MCP Server is Ready!
User: Jackson
TTS: Disabled
Database initialized
```

### Step 3: Add Edward to Bob's MCP Settings

**Option A: Using Bob's Settings UI**
1. Open Bob's settings/preferences
2. Look for "MCP" or "Model Context Protocol" section
3. Add a new MCP server with these details:
   - Name: `edward`
   - Command: `python`
   - Args: `["mcp_server.py"]`
   - Working Directory: `C:/Users/BoppJ/Desktop/IBM-Bob-Hackathon-Edward`

**Option B: Using Configuration File**
If Bob uses a JSON config file for MCP servers, add the contents of `edward-mcp-config.json` to it.

### Step 4: Test Edward's Tools with Bob

Once configured, ask Bob to use Edward's tools:

```
"Bob, use the capture_screenshot tool to see what's on my screen"
```

```
"Bob, use save_interaction to save this conversation"
```

```
"Bob, use search_history to find our previous Python conversations"
```

## 🛠️ Available Edward Tools

Edward provides 8 tools that Bob can use:

1. **capture_screenshot** - Take a screenshot of your screen
   - Returns base64-encoded PNG image
   - Optional: specify monitor number

2. **speak_text** - Text-to-speech (when TTS is enabled)
   - Requires ElevenLabs API key in .env

3. **store_password** - Save credentials to encrypted vault
   - Parameters: service, username, password

4. **retrieve_password** - Get password from vault
   - Parameters: service, username

5. **list_passwords** - List all vault entries
   - Returns list of services and usernames

6. **save_interaction** - Save conversation to history database
   - Parameters: user_input, assistant_response, context

7. **search_history** - Search past interactions
   - Parameters: query, limit (optional)

8. **get_recent_sessions** - Get recent conversation sessions
   - Parameters: limit (optional)

## 🔧 Optional Enhancements

### Enable Text-to-Speech
1. Get an ElevenLabs API key: https://elevenlabs.io/
2. Update `.env`:
   ```env
   TTS_ENABLED=true
   ELEVENLABS_API_KEY=your_key_here
   ELEVENLABS_VOICE_ID=your_voice_id_here
   ```

### Use Hotkey Activation (Win+Shift+E)
Run Edward's main interface:
```powershell
cd IBM-Bob-Hackathon-Edward
python main.py
```

Then press Win+Shift+E to activate Edward's voice input.

## 🐛 Troubleshooting

### If MCP server won't start:
1. Check Python version: `python --version` (should be 3.9+)
2. Verify all dependencies installed: `pip list | findstr mcp`
3. Check for errors in terminal output

### If Bob can't find Edward:
1. Verify the path in MCP config is correct
2. Restart Bob after adding MCP configuration
3. Check Bob's logs for MCP connection errors

### If tools don't work:
1. Ensure Edward MCP server is running
2. Check `.env` file has correct settings
3. Verify database directory exists (created automatically)

## 📁 Project Structure

```
IBM-Bob-Hackathon-Edward/
├── mcp_server.py          # MCP server implementation
├── edward-mcp-config.json # MCP configuration for Bob
├── .env                   # Environment configuration
├── requirements.txt       # Python dependencies
├── main.py               # Main Edward interface (optional)
├── database.py           # History database
├── vault.py              # Password vault
├── tts.py                # Text-to-speech
└── config.py             # Configuration loader
```

## 🎯 Architecture

```
┌─────────────┐
│   Bob AI    │
│  (Client)   │
└──────┬──────┘
       │ MCP Protocol
       │
┌──────▼──────────────────┐
│  Edward MCP Server      │
│  - Screenshot capture   │
│  - Password vault       │
│  - History database     │
│  - TTS (optional)       │
└─────────────────────────┘
```

Bob calls Edward's tools directly via MCP - no API needed!

## ✨ Benefits of MCP Architecture

- ✅ **Direct Integration** - Bob calls Edward's tools directly
- ✅ **Secure** - All data stays local, passwords encrypted
- ✅ **Fast** - Direct process communication
- ✅ **Flexible** - Bob decides when to use Edward's capabilities
- ✅ **No API Setup** - No need to expose HTTP endpoints

## 🤝 Team Collaboration

Your teammate Danny has already:
- ✅ Created the MCP server implementation
- ✅ Set up all 8 tools
- ✅ Configured database and vault
- ✅ Written documentation

You've now:
- ✅ Updated paths for your system
- ✅ Configured environment for Jackson
- ✅ Updated dependencies for Python 3.13
- ✅ Ready to integrate with Bob!

## 📞 Need Help?

Check the detailed documentation:
- `MCP_SETUP.md` - Detailed MCP setup guide
- `EDWARD_MCP_QUICKSTART.md` - Quick start guide
- `HOW_TO_TEST.md` - Testing instructions

Good luck with the IBM Bob Hackathon! 🚀