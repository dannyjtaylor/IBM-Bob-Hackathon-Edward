"""
Edward Configuration Module
Loads environment variables and provides configuration constants
"""

import os
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
ASSETS_DIR = PROJECT_ROOT / "assets"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# ── Color palette (FullCUDA Alchemist — Edward) ────────────────────────
COLORS = {
    "background": "#0D0D0D",
    "panel":      "#141414",
    "red":        "#B22222",
    "gold":       "#DAA520",
    "silver":     "#A8A9AD",
    "text":       "#F0EAD6",
    "blueprint":  "#0A1628",   # blueprint-paper response area
}


# ── Screenshot mode ───────────────────────────────────────────────────────────
class ScreenshotMode(Enum):
    CURSOR_REGION = "cursor"   # region around cursor — fastest / most focused
    ACTIVE_WINDOW = "window"   # foreground window — medium
    FULL_SCREEN   = "screen"   # all monitors — most context, slowest


_mode_map = {m.value: m for m in ScreenshotMode}
SCREENSHOT_MODE = _mode_map.get(
    os.getenv("SCREENSHOT_MODE", "cursor"),
    ScreenshotMode.CURSOR_REGION,
)
CURSOR_REGION_SIZE = int(os.getenv("CURSOR_REGION_SIZE", "400"))

# ── AI backend ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AI_BACKEND     = os.getenv("AI_BACKEND", "gemini")   # gemini | moondream | ollama
AI_MODEL       = os.getenv("AI_MODEL",   "flash-lite")  # gemini model key

# ── API keys ──────────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

# ── User ──────────────────────────────────────────────────────────────────────
USER_NAME = os.getenv("USER_NAME", "User")

# ── Wake word ─────────────────────────────────────────────────────────────────
WAKE_WORD_ENABLED    = os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true"
WAKE_WORD_THRESHOLD  = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
WAKE_WORDS           = ["hey ed", "hey edward", "edward"]
PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")  # optional upgrade

# ── Hotkey ────────────────────────────────────────────────────────────────────
HOTKEY_ENABLED     = os.getenv("HOTKEY_ENABLED", "true").lower() == "true"
HOTKEY_COMBINATION = "<cmd>+<shift>+e"   # Win+Shift+E

# ── Audio ─────────────────────────────────────────────────────────────────────
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"
STT_MODEL   = os.getenv("STT_MODEL", "base")

# ── UI ────────────────────────────────────────────────────────────────────────
OVERLAY_WIDTH              = 520
OVERLAY_ANIMATION_DURATION = 300   # ms
OVERLAY_OPACITY            = 0.97

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH    = DATA_DIR / "edward.db"
VAULT_PATH = DATA_DIR / "vault.db"
