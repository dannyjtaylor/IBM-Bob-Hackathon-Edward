"""
Edward MCP Server
Exposes Edward's desktop integration capabilities as MCP tools for Bob AI
"""

import asyncio
import base64
import logging
from pathlib import Path
from typing import Optional
import mss
import mss.tools
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Import Edward's modules
from tts import EdwardTTS
from vault import PasswordVault
from database import get_database
from config import USER_NAME, TTS_ENABLED, DATA_DIR

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("edward")

# Initialize Edward components
tts = EdwardTTS() if TTS_ENABLED else None
db = get_database()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Edward tools"""
    return [
        Tool(
            name="capture_screenshot",
            description=f"Capture a screenshot of {USER_NAME}'s screen. Returns base64-encoded PNG image.",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitor": {
                        "type": "integer",
                        "description": "Monitor number to capture (default: 1 for primary monitor)",
                        "default": 1
                    }
                }
            }
        ),
        Tool(
            name="speak_text",
            description=f"Speak text aloud to {USER_NAME} using text-to-speech (ElevenLabs). Only works if TTS is enabled.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to speak aloud"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="store_password",
            description=f"Store a password in {USER_NAME}'s encrypted vault. Passwords are encrypted with AES-128 and never sent to external APIs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name (e.g., 'Gmail', 'GitHub')"
                    },
                    "username": {
                        "type": "string",
                        "description": "Username or email"
                    },
                    "password": {
                        "type": "string",
                        "description": "Password to store"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about this password",
                        "default": ""
                    },
                    "master_password": {
                        "type": "string",
                        "description": "Master password for vault encryption"
                    }
                },
                "required": ["service", "username", "password", "master_password"]
            }
        ),
        Tool(
            name="retrieve_password",
            description=f"Retrieve a password from {USER_NAME}'s encrypted vault.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name"
                    },
                    "username": {
                        "type": "string",
                        "description": "Username or email"
                    },
                    "master_password": {
                        "type": "string",
                        "description": "Master password for vault decryption"
                    }
                },
                "required": ["service", "username", "master_password"]
            }
        ),
        Tool(
            name="list_passwords",
            description=f"List all services stored in {USER_NAME}'s password vault (without revealing passwords).",
            inputSchema={
                "type": "object",
                "properties": {
                    "master_password": {
                        "type": "string",
                        "description": "Master password for vault access"
                    }
                },
                "required": ["master_password"]
            }
        ),
        Tool(
            name="save_interaction",
            description=f"Save an interaction to {USER_NAME}'s session history database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "User's question"
                    },
                    "response": {
                        "type": "string",
                        "description": "AI's response"
                    },
                    "screenshot_path": {
                        "type": "string",
                        "description": "Optional path to screenshot",
                        "default": None
                    }
                },
                "required": ["question", "response"]
            }
        ),
        Tool(
            name="search_history",
            description=f"Search {USER_NAME}'s interaction history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_recent_sessions",
            description=f"Get {USER_NAME}'s recent interaction sessions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of sessions to retrieve",
                        "default": 5
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    
    try:
        if name == "capture_screenshot":
            return await handle_capture_screenshot(arguments)
        
        elif name == "speak_text":
            return await handle_speak_text(arguments)
        
        elif name == "store_password":
            return await handle_store_password(arguments)
        
        elif name == "retrieve_password":
            return await handle_retrieve_password(arguments)
        
        elif name == "list_passwords":
            return await handle_list_passwords(arguments)
        
        elif name == "save_interaction":
            return await handle_save_interaction(arguments)
        
        elif name == "search_history":
            return await handle_search_history(arguments)
        
        elif name == "get_recent_sessions":
            return await handle_get_recent_sessions(arguments)
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_capture_screenshot(args: dict) -> list[ImageContent]:
    """Capture screenshot and return as base64"""
    monitor_num = args.get("monitor", 1)
    
    with mss.mss() as sct:
        # Get monitor
        if monitor_num > len(sct.monitors) - 1:
            monitor_num = 1
        
        monitor = sct.monitors[monitor_num]
        
        # Capture screenshot
        screenshot = sct.grab(monitor)
        
        # Convert to PNG bytes
        png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        
        # Encode to base64
        if png_bytes:
            base64_image = base64.b64encode(png_bytes).decode('utf-8')
        else:
            raise Exception("Failed to capture screenshot")
        
        logger.info(f"Screenshot captured from monitor {monitor_num}")
        
        return [
            ImageContent(
                type="image",
                data=base64_image,
                mimeType="image/png"
            )
        ]


async def handle_speak_text(args: dict) -> list[TextContent]:
    """Speak text using TTS"""
    text = args["text"]
    
    if not TTS_ENABLED or not tts:
        return [TextContent(
            type="text",
            text="TTS is disabled. Enable it in .env to use this feature."
        )]
    
    try:
        # Run synchronous speak in thread pool
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, tts.speak, text)
        
        if success:
            return [TextContent(
                type="text",
                text=f"Spoke: {text[:50]}..." if len(text) > 50 else f"Spoke: {text}"
            )]
        else:
            return [TextContent(
                type="text",
                text="TTS failed - check if ElevenLabs API key is configured"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"TTS error: {str(e)}"
        )]


async def handle_store_password(args: dict) -> list[TextContent]:
    """Store password in encrypted vault"""
    service = args["service"]
    username = args["username"]
    password = args["password"]
    notes = args.get("notes", "")
    master_password = args["master_password"]
    
    try:
        vault = PasswordVault(master_password=master_password)
        vault.add_password(service, username, password, notes)
        
        return [TextContent(
            type="text",
            text=f"Password stored for {service} ({username})"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to store password: {str(e)}"
        )]


async def handle_retrieve_password(args: dict) -> list[TextContent]:
    """Retrieve password from vault"""
    service = args["service"]
    username = args["username"]
    master_password = args["master_password"]
    
    try:
        vault = PasswordVault(master_password=master_password)
        entry = vault.get_password(service, username)
        
        if entry:
            return [TextContent(
                type="text",
                text=f"Service: {entry['service']}\nUsername: {entry['username']}\nPassword: {entry['password']}\nNotes: {entry['notes']}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"No password found for {service} ({username})"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to retrieve password: {str(e)}"
        )]


async def handle_list_passwords(args: dict) -> list[TextContent]:
    """List all services in vault"""
    master_password = args["master_password"]
    
    try:
        vault = PasswordVault(master_password=master_password)
        entries = vault.list_entries()
        
        if entries:
            result = "Stored passwords:\n\n"
            for entry in entries:
                result += f"- {entry['service']} ({entry['username']})\n"
            return [TextContent(type="text", text=result)]
        else:
            return [TextContent(
                type="text",
                text="No passwords stored in vault"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to list passwords: {str(e)}"
        )]


async def handle_save_interaction(args: dict) -> list[TextContent]:
    """Save interaction to database"""
    question = args["question"]
    response = args["response"]
    screenshot_path = args.get("screenshot_path")
    
    try:
        session_id = db.create_session()
        db.add_interaction(session_id, question, response, screenshot_path)
        
        return [TextContent(
            type="text",
            text=f"Interaction saved to session {session_id}"
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to save interaction: {str(e)}"
        )]


async def handle_search_history(args: dict) -> list[TextContent]:
    """Search interaction history"""
    query = args["query"]
    limit = args.get("limit", 10)
    
    try:
        results = db.search_interactions(query, limit)
        
        if results:
            result_text = f"Found {len(results)} results:\n\n"
            for r in results:
                result_text += f"[{r['timestamp']}]\n"
                result_text += f"Q: {r['question'][:100]}...\n"
                result_text += f"A: {r['response'][:100]}...\n\n"
            return [TextContent(type="text", text=result_text)]
        else:
            return [TextContent(
                type="text",
                text=f"No results found for: {query}"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Search failed: {str(e)}"
        )]


async def handle_get_recent_sessions(args: dict) -> list[TextContent]:
    """Get recent sessions"""
    limit = args.get("limit", 5)
    
    try:
        sessions = db.get_recent_sessions(limit)
        
        if sessions:
            result_text = f"Recent {len(sessions)} sessions:\n\n"
            for session in sessions:
                result_text += f"Session {session['id']} - {session['created_at']}\n"
                result_text += f"  Interactions: {session['interaction_count']}\n\n"
            return [TextContent(type="text", text=result_text)]
        else:
            return [TextContent(
                type="text",
                text="No sessions found"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to get sessions: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    logger.info("Starting Edward MCP Server...")
    logger.info(f"User: {USER_NAME}")
    logger.info(f"TTS Enabled: {TTS_ENABLED}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
