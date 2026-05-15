"""
Edward Configuration Module
Loads environment variables and provides configuration constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# Color Palette
COLORS = {
    "background": "#111111",
    "panel": "#1A1A1A",
    "red": "#B22222",
    "gold": "#DAA520",
    "silver": "#A8A9AD",
    "text": "#F0EAD6",
}

# API Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
IBM_BOB_API_URL = os.getenv("IBM_BOB_API_URL", "http://localhost:8000")
IBM_BOB_API_KEY = os.getenv("IBM_BOB_API_KEY", "")

# User Settings
USER_NAME = os.getenv("USER_NAME", "User")

# Wake Word Settings
WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true"
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
WAKE_WORDS = ["hey ed", "hey edward", "edward"]

# Hotkey Settings
HOTKEY_ENABLED = os.getenv("HOTKEY_ENABLED", "true").lower() == "true"
HOTKEY_COMBINATION = "<cmd>+<shift>+e"  # Win+Shift+E

# Audio Settings
TTS_ENABLED = os.getenv("TTS_ENABLED", "true").lower() == "true"
STT_MODEL = os.getenv("STT_MODEL", "base")

# UI Settings
OVERLAY_WIDTH = 500
OVERLAY_ANIMATION_DURATION = 300  # milliseconds
OVERLAY_OPACITY = 0.95

# Database
DB_PATH = DATA_DIR / "edward.db"
VAULT_PATH = DATA_DIR / "vault.db"

# Made with Bob
