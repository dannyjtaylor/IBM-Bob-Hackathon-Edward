"""
Edward Computer Control API
FastAPI backend that exposes endpoints to control mouse and keyboard using pyautogui
"""

import asyncio
import base64
import io
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pyautogui
from PIL import Image

from logger import setup_logger

# Setup logging
logger = setup_logger(__name__, log_file='logs/control_api.log')

# Configure pyautogui safety features
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions

# Create FastAPI app
app = FastAPI(
    title="Edward Computer Control API",
    description="Local API for controlling mouse and keyboard",
    version="1.0.0"
)

# Add CORS middleware for local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class MouseMoveRequest(BaseModel):
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    duration: float = Field(0.2, description="Duration of movement in seconds")


class MouseClickRequest(BaseModel):
    x: Optional[int] = Field(None, description="X coordinate (current position if not provided)")
    y: Optional[int] = Field(None, description="Y coordinate (current position if not provided)")
    button: str = Field("left", description="Mouse button: 'left', 'right', or 'middle'")
    clicks: int = Field(1, description="Number of clicks")
    interval: float = Field(0.0, description="Interval between clicks")


class MouseDragRequest(BaseModel):
    x: int = Field(..., description="Target X coordinate")
    y: int = Field(..., description="Target Y coordinate")
    duration: float = Field(0.5, description="Duration of drag in seconds")
    button: str = Field("left", description="Mouse button to hold")


class MouseScrollRequest(BaseModel):
    clicks: int = Field(..., description="Number of scroll clicks (positive=up, negative=down)")
    x: Optional[int] = Field(None, description="X coordinate to scroll at")
    y: Optional[int] = Field(None, description="Y coordinate to scroll at")


class TypeTextRequest(BaseModel):
    text: str = Field(..., description="Text to type")
    interval: float = Field(0.0, description="Interval between keystrokes")


class PressKeyRequest(BaseModel):
    key: str = Field(..., description="Key to press (e.g., 'enter', 'tab', 'ctrl')")
    presses: int = Field(1, description="Number of times to press")
    interval: float = Field(0.0, description="Interval between presses")


class HotkeyRequest(BaseModel):
    keys: List[str] = Field(..., description="List of keys to press together (e.g., ['ctrl', 'c'])")


class ScreenshotRequest(BaseModel):
    region: Optional[List[int]] = Field(None, description="Region to capture [x, y, width, height]")


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Edward Computer Control API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "mouse": ["/mouse/move", "/mouse/click", "/mouse/drag", "/mouse/scroll", "/mouse/position"],
            "keyboard": ["/keyboard/type", "/keyboard/press", "/keyboard/hotkey"],
            "screen": ["/screen/screenshot", "/screen/size"]
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Mouse Control Endpoints
@app.post("/mouse/move")
async def mouse_move(request: MouseMoveRequest):
    """Move mouse to specified coordinates"""
    try:
        logger.info(f"Moving mouse to ({request.x}, {request.y})")
        pyautogui.moveTo(request.x, request.y, duration=request.duration)
        return {
            "success": True,
            "action": "move",
            "position": {"x": request.x, "y": request.y}
        }
    except Exception as e:
        logger.error(f"Mouse move failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mouse/click")
async def mouse_click(request: MouseClickRequest):
    """Click mouse at specified coordinates or current position"""
    try:
        if request.x is not None and request.y is not None:
            logger.info(f"Clicking {request.button} button at ({request.x}, {request.y})")
            pyautogui.click(
                x=request.x,
                y=request.y,
                clicks=request.clicks,
                interval=request.interval,
                button=request.button
            )
        else:
            logger.info(f"Clicking {request.button} button at current position")
            pyautogui.click(
                clicks=request.clicks,
                interval=request.interval,
                button=request.button
            )
        
        current_pos = pyautogui.position()
        return {
            "success": True,
            "action": "click",
            "button": request.button,
            "clicks": request.clicks,
            "position": {"x": current_pos.x, "y": current_pos.y}
        }
    except Exception as e:
        logger.error(f"Mouse click failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mouse/drag")
async def mouse_drag(request: MouseDragRequest):
    """Drag mouse to specified coordinates"""
    try:
        logger.info(f"Dragging to ({request.x}, {request.y})")
        pyautogui.drag(
            request.x,
            request.y,
            duration=request.duration,
            button=request.button
        )
        return {
            "success": True,
            "action": "drag",
            "position": {"x": request.x, "y": request.y}
        }
    except Exception as e:
        logger.error(f"Mouse drag failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mouse/scroll")
async def mouse_scroll(request: MouseScrollRequest):
    """Scroll mouse wheel"""
    try:
        if request.x is not None and request.y is not None:
            logger.info(f"Scrolling {request.clicks} clicks at ({request.x}, {request.y})")
            pyautogui.scroll(request.clicks, x=request.x, y=request.y)
        else:
            logger.info(f"Scrolling {request.clicks} clicks at current position")
            pyautogui.scroll(request.clicks)
        
        return {
            "success": True,
            "action": "scroll",
            "clicks": request.clicks
        }
    except Exception as e:
        logger.error(f"Mouse scroll failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mouse/position")
async def get_mouse_position():
    """Get current mouse position"""
    try:
        pos = pyautogui.position()
        return {
            "success": True,
            "position": {"x": pos.x, "y": pos.y}
        }
    except Exception as e:
        logger.error(f"Failed to get mouse position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Keyboard Control Endpoints
@app.post("/keyboard/type")
async def keyboard_type(request: TypeTextRequest):
    """Type text using keyboard"""
    try:
        logger.info(f"Typing text: {request.text[:50]}...")
        pyautogui.write(request.text, interval=request.interval)
        return {
            "success": True,
            "action": "type",
            "text_length": len(request.text)
        }
    except Exception as e:
        logger.error(f"Keyboard type failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keyboard/press")
async def keyboard_press(request: PressKeyRequest):
    """Press a specific key"""
    try:
        logger.info(f"Pressing key: {request.key} ({request.presses} times)")
        pyautogui.press(request.key, presses=request.presses, interval=request.interval)
        return {
            "success": True,
            "action": "press",
            "key": request.key,
            "presses": request.presses
        }
    except Exception as e:
        logger.error(f"Keyboard press failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/keyboard/hotkey")
async def keyboard_hotkey(request: HotkeyRequest):
    """Press a combination of keys (hotkey)"""
    try:
        logger.info(f"Pressing hotkey: {'+'.join(request.keys)}")
        pyautogui.hotkey(*request.keys)
        return {
            "success": True,
            "action": "hotkey",
            "keys": request.keys
        }
    except Exception as e:
        logger.error(f"Keyboard hotkey failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Screen Control Endpoints
@app.post("/screen/screenshot")
async def take_screenshot(request: Optional[ScreenshotRequest] = None):
    """Take a screenshot and return as base64"""
    try:
        if request and request.region and len(request.region) == 4:
            logger.info(f"Taking screenshot of region: {request.region}")
            screenshot = pyautogui.screenshot(region=(request.region[0], request.region[1], request.region[2], request.region[3]))
        else:
            logger.info("Taking full screenshot")
            screenshot = pyautogui.screenshot()
        
        # Convert to base64
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {
            "success": True,
            "action": "screenshot",
            "image": img_base64,
            "size": {"width": screenshot.width, "height": screenshot.height}
        }
    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/screen/size")
async def get_screen_size():
    """Get screen size"""
    try:
        size = pyautogui.size()
        return {
            "success": True,
            "width": size.width,
            "height": size.height
        }
    except Exception as e:
        logger.error(f"Failed to get screen size: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Utility Endpoints
@app.get("/keyboard/keys")
async def list_keyboard_keys():
    """List all available keyboard keys"""
    return {
        "success": True,
        "keys": pyautogui.KEYBOARD_KEYS
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Edward Computer Control API...")
    logger.info("API will be available at http://localhost:8001")
    logger.info("Documentation at http://localhost:8001/docs")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )

# Made with Bob