"""
Edward Local Command Processor
Handles common commands instantly without any AI backend.
Matched BEFORE sending to Gemma — zero latency for demo-critical actions.
"""

import ctypes
import datetime
import re
import subprocess
import time
import urllib.parse
from typing import Optional

from config import USER_NAME
from logger import get_logger

logger = get_logger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _open(cmd, shell=False):
    try:
        subprocess.Popen(cmd, shell=shell, creationflags=subprocess.CREATE_NO_WINDOW)
        return True
    except Exception as e:
        logger.error(f"Failed to open {cmd}: {e}")
        return False


def _send_keys(vk: int):
    """Press and release a virtual key."""
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


def _type_text(text: str, delay: float = 1.2):
    """Open an app, wait for it to load, then type text via pyautogui."""
    try:
        import pyautogui
        time.sleep(delay)
        pyautogui.write(text, interval=0.04)
    except ImportError:
        logger.warning("pyautogui not installed — cannot type text")
    except Exception as e:
        logger.error(f"_type_text failed: {e}")


def _open_url(url: str):
    """Open a URL in the default browser."""
    import webbrowser
    webbrowser.open(url)


# ── Compiled patterns ─────────────────────────────────────────────────────────

_VAULT_RE        = re.compile(r'\b(open|show|launch|unlock)\s+(vault|password\s+manager|passwords|password\s+vault)\b', re.I)
_GREETINGS_RE    = re.compile(r'\b(hello|hi|hey|howdy|greetings)\b', re.I)
_TIME_RE         = re.compile(r'\b(time|what.?s the time|current time)\b', re.I)
_DATE_RE         = re.compile(r'\b(date|what.?s the date|today.?s date|what day)\b', re.I)
_HELP_RE         = re.compile(r'\b(help|commands|what can you do|capabilities)\b', re.I)
_WHO_RE          = re.compile(r'\b(who are you|what are you|introduce yourself)\b', re.I)
_LOCK_RE         = re.compile(r'\block\s*(screen|computer|workstation|pc|my\s+pc)?\b', re.I)
_DESKTOP_RE      = re.compile(r'\b(show\s+desktop|minimize\s+all|win\s*\+\s*d)\b', re.I)
_SCREENSHOT_RE   = re.compile(r'\b(take|save|capture)\s+a?\s*screenshot\b', re.I)
_CLIPBOARD_RE    = re.compile(r'\b(clipboard|what.?s\s+in\s+(my\s+)?clipboard)\b', re.I)
_VOL_UP_RE       = re.compile(r'\b(volume\s+up|louder|turn\s+up)\b', re.I)
_VOL_DOWN_RE     = re.compile(r'\b(volume\s+down|quieter|turn\s+down)\b', re.I)
_VOL_MUTE_RE     = re.compile(r'\b(mute|unmute|silence)\b', re.I)
_SYSINFO_RE      = re.compile(r'\b(system\s+info|cpu|ram|memory|battery|pc\s+info)\b', re.I)

# ── Spotify / media ───────────────────────────────────────────────────────────
_SPOT_PLAY_RE   = re.compile(r'\b(play|resume|unpause)\s*(?:music|song|spotify|track)?\b', re.I)
_SPOT_PAUSE_RE  = re.compile(r'\bpause\s*(?:music|song|spotify|track)?\b', re.I)
_SPOT_NEXT_RE   = re.compile(r'\b(next|skip)\s*(?:song|track|music)?\b', re.I)
_SPOT_PREV_RE   = re.compile(r'\b(previous|prev|back)\s*(?:song|track|music)?\b', re.I)
_SPOT_STOP_RE   = re.compile(r'\bstop\s*(?:music|song|spotify|track|playing)?\b', re.I)
_SPOT_NOW_RE    = re.compile(r'\b(what(?:\'s|\s+is)\s+playing|current\s+(?:song|track)|now\s+playing)\b', re.I)
_SPOT_PLAY_Q_RE = re.compile(
    # "play X" where X is NOT a generic media word → Spotify song search
    r'\b(?:play|put\s+on|start\s+playing)\s+'
    r'(?!(?:music|songs?|tracks?|spotify|it|that|this)\s*$)'
    r'(.+)',
    re.I | re.S,
)
_SPOT_OPEN_RE   = re.compile(r'\bopen\s+spotify\b', re.I)

# ── Web search (returns real results) ────────────────────────────────────────
_WEB_SEARCH_RE  = re.compile(
    r'\b(?:web\s+search|search\s+the\s+web|real\s+search|look\s+up\s+online|'
    r'what\s+is\s+the\s+latest|find\s+me\s+(?:info\s+)?(?:about|on))\s+(.+)',
    re.I | re.S,
)
# "fetch / scrape / read the page at [url]"
_FETCH_PAGE_RE  = re.compile(
    r'\b(?:fetch|scrape|read|get|summarize)\s+(?:the\s+)?(?:page|site|content|text)?\s*'
    r'(?:at|from|of)?\s*(https?://\S+|[\w\-]+\.(?:com|org|net|io|gov|edu)\S*)',
    re.I,
)

# ── Open + type / write ───────────────────────────────────────────────────────
# "open notepad and type hello world"  /  "open notepad and write a poem"
_NOTEPAD_TYPE_RE = re.compile(
    r'\bopen\s+notepad\s+and\s+(?:type|write|say|put)\s+(.+)', re.I | re.S
)

# ── Browser / search automation ───────────────────────────────────────────────
# "search for cats"  /  "google machine learning"  /  "look up quantum physics"
_SEARCH_RE = re.compile(
    r'\b(?:search(?:\s+for)?|google|look\s+up|find\s+(?:me\s+)?info(?:rmation)?\s+(?:on|about))\s+(.+)',
    re.I | re.S,
)
# "open chrome / browser / edge and search for X"
_BROWSER_SEARCH_RE = re.compile(
    r'\bopen\s+(?:chrome|browser|edge|firefox|internet)\s+and\s+'
    r'(?:search(?:\s+for)?|google|look\s+up)\s+(.+)',
    re.I | re.S,
)
# "open chrome and go to / visit / navigate to X"
_BROWSER_GOTO_RE = re.compile(
    r'\bopen\s+(?:chrome|browser|edge|firefox|internet)\s+and\s+'
    r'(?:go\s+to|navigate\s+to|visit|open)\s+(.+)',
    re.I | re.S,
)
# "open chrome" / "open browser" (without follow-up)
_OPEN_BROWSER_RE = re.compile(
    r'\bopen\s+(browser|chrome|edge|firefox|internet)\b', re.I
)
# "go to youtube.com"  /  "visit reddit.com"  — must have a real TLD
_GOTO_SITE_RE = re.compile(
    r'\b(?:go\s+to|visit|navigate\s+to)\s+([\w\.\-]+\.(?:com|org|net|io|gov|edu|co|uk|de|jp|au))\b',
    re.I,
)
# "open youtube and search for / play X"
_YOUTUBE_RE = re.compile(
    r'\bopen\s+youtube\s+and\s+(?:search(?:\s+for)?|play|find)\s+(.+)', re.I | re.S
)
# Plain app opens
_OPEN_NOTEPAD_RE  = re.compile(r'\bopen\s+notepad\b', re.I)
_OPEN_CALC_RE     = re.compile(r'\bopen\s+(calc(ulator)?)\b', re.I)
_OPEN_EXPLORER_RE = re.compile(r'\bopen\s+(file\s+)?explorer\b', re.I)
_OPEN_SETTINGS_RE = re.compile(r'\bopen\s+settings\b', re.I)
_OPEN_TASKMGR_RE  = re.compile(r'\bopen\s+task\s+manager\b', re.I)
_OPEN_PAINT_RE    = re.compile(r'\bopen\s+paint\b', re.I)
_OPEN_CMD_RE      = re.compile(
    r'\bopen\s+(cmd|terminal|command\s+prompt|powershell)\b', re.I
)
# "open spotify" / "open discord" / "open vscode" — generic known apps
_OPEN_APP_RE = re.compile(
    r'\bopen\s+(spotify|discord|slack|teams|zoom|vscode|code|word|excel|'
    r'powerpoint|outlook|skype|telegram|whatsapp|steam|obs|vlc|'
    r'photoshop|figma|notion|obsidian|winamp)\b',
    re.I,
)
_APP_CMDS = {
    'spotify':    'spotify',
    'discord':    'discord',
    'slack':      'slack',
    'teams':      'teams',
    'zoom':       'zoom',
    'vscode':     'code',
    'code':       'code',
    'word':       'winword',
    'excel':      'excel',
    'powerpoint': 'powerpnt',
    'outlook':    'outlook',
    'skype':      'skype',
    'telegram':   'telegram',
    'steam':      'steam',
    'obs':        'obs64',
    'vlc':        'vlc',
    'figma':      'figma',
}

# ── Clipboard write ───────────────────────────────────────────────────────────
# "copy X to clipboard" / "put X in clipboard"
_CLIP_WRITE_RE = re.compile(
    r'\b(?:copy|put|save)\s+(.+?)\s+(?:to|in(?:to)?)\s+(?:my\s+)?clipboard\b', re.I | re.S
)

# ── Window management ─────────────────────────────────────────────────────────
_FULLSCREEN_RE = re.compile(r'\b(fullscreen|full.screen|maximize)\b', re.I)
_MINIMIZE_RE   = re.compile(r'\bminimize\s*(?:window|this)?\b', re.I)
_CLOSE_WIN_RE  = re.compile(r'\bclose\s+(?:this\s+)?(?:window|app|application)\b', re.I)
_ALT_TAB_RE    = re.compile(r'\b(?:switch\s+(?:window|app)|alt.?tab)\b', re.I)

# ── Typing into active window ─────────────────────────────────────────────────
# "type hello world" / "write this: hello"
_TYPE_RE = re.compile(r'\b(?:type|write|input)\s+(?:this[:\s]+)?(.+)', re.I | re.S)



# ── Slash command dispatcher ───────────────────────────────────────────────────

_KNOWN_APPS = {
    'spotify': 'spotify', 'discord': 'discord', 'slack': 'slack',
    'teams': 'teams', 'zoom': 'zoom', 'vscode': 'code', 'code': 'code',
    'word': 'winword', 'excel': 'excel', 'powerpoint': 'powerpnt',
    'outlook': 'outlook', 'skype': 'skype', 'telegram': 'telegram',
    'steam': 'steam', 'obs': 'obs64', 'vlc': 'vlc', 'figma': 'figma',
    'notepad': 'notepad.exe', 'calc': 'calc.exe', 'calculator': 'calc.exe',
    'explorer': 'explorer.exe', 'taskmgr': 'taskmgr.exe',
    'paint': 'mspaint.exe', 'cmd': 'cmd.exe', 'terminal': 'cmd.exe',
    'powershell': 'powershell.exe', 'ps': 'powershell.exe',
}


def _slash_help() -> str:
    return (
        "EDWARD SLASH COMMANDS\n"
        "══════════════════════════════════════\n\n"
        "SEARCH:\n"
        "  /google [query]       — Google search\n"
        "  /bing [query]         — Bing search\n"
        "  /duckduckgo [query]   — DuckDuckGo (alias: /ddg)\n"
        "  /youtube [query]      — YouTube search (alias: /yt)\n"
        "  /web [query]          — Real search results (no browser)\n"
        "  /fetch [url]          — Scrape & read a web page\n\n"
        "NAVIGATE:\n"
        "  /goto [url]           — Open any URL\n\n"
        "SPOTIFY / MEDIA:\n"
        "  /spotify [query]      — Search & open on Spotify\n"
        "  /play                 — Play / resume\n"
        "  /pause                — Pause\n"
        "  /next                 — Next track (alias: /skip)\n"
        "  /prev                 — Previous track\n"
        "  /np                   — Now playing\n\n"
        "APPS:\n"
        "  /notepad [text]       — Open Notepad, optionally type text\n"
        "  /calc                 — Calculator\n"
        "  /explorer             — File Explorer\n"
        "  /settings             — Windows Settings\n"
        "  /taskmgr              — Task Manager\n"
        "  /cmd                  — Command Prompt\n"
        "  /ps                   — PowerShell\n"
        "  /paint                — Paint\n"
        "  /open [app]           — Open any known app\n\n"
        "SYSTEM:\n"
        "  /time                 — Current time\n"
        "  /date                 — Current date\n"
        "  /lock                 — Lock screen\n"
        "  /desktop              — Show desktop\n"
        "  /volup                — Volume up\n"
        "  /voldown              — Volume down\n"
        "  /mute                 — Toggle mute\n"
        "  /screenshot           — Save current screenshot (alias: /ss)\n"
        "  /sysinfo              — CPU, RAM, disk, battery\n\n"
        "CLIPBOARD:\n"
        "  /clip                 — Read clipboard\n"
        "  /copy [text]          — Copy text to clipboard\n"
        "  /type [text]          — Type text into active window\n\n"
        "OTHER:\n"
        "  /vault                — Open password vault\n"
        "  /help                 — This list\n"
    )


def _handle_slash(cmd: str, arg: str, screenshot_b64: Optional[str]) -> Optional[str]:
    """Route /command [arg] to the appropriate action."""
    c = cmd.lower().lstrip('/')

    # ── Search engines ─────────────────────────────────────────────────────────
    if c == "google":
        if not arg:
            return "Usage: /google [query]"
        _open_url(f"https://www.google.com/search?q={urllib.parse.quote(arg)}")
        return f"Googling: \"{arg}\" ⚡"

    if c == "bing":
        if not arg:
            return "Usage: /bing [query]"
        _open_url(f"https://www.bing.com/search?q={urllib.parse.quote(arg)}")
        return f"Bing search: \"{arg}\" ⚡"

    if c in ("duckduckgo", "ddg", "duck"):
        if not arg:
            return "Usage: /duckduckgo [query]"
        _open_url(f"https://duckduckgo.com/?q={urllib.parse.quote(arg)}")
        return f"DuckDuckGo: \"{arg}\" ⚡"

    if c in ("youtube", "yt"):
        if not arg:
            _open_url("https://youtube.com")
            return "Opening YouTube ⚡"
        _open_url(f"https://www.youtube.com/results?search_query={urllib.parse.quote(arg)}")
        return f"YouTube search: \"{arg}\" ⚡"

    if c in ("web", "search"):
        if not arg:
            return "Usage: /web [query]"
        try:
            from web_tools import web_search
            return web_search(arg)
        except Exception as e:
            return f"Web search error: {e}"

    if c == "fetch":
        if not arg:
            return "Usage: /fetch [url]"
        try:
            from web_tools import fetch_page_text
            return f"Content from {arg}:\n\n{fetch_page_text(arg)}"
        except Exception as e:
            return f"Fetch error: {e}"

    # ── Navigate ───────────────────────────────────────────────────────────────
    if c in ("goto", "go", "visit"):
        if not arg:
            return "Usage: /goto [url]"
        url = arg if arg.startswith(('http://', 'https://')) else 'https://' + arg
        _open_url(url)
        return f"Navigating to {url} ⚡"

    # ── Spotify / media ────────────────────────────────────────────────────────
    if c == "spotify":
        if arg:
            url = f"https://open.spotify.com/search/{urllib.parse.quote(arg)}"
            _open_url(url)
            return f"Searching Spotify: \"{arg}\" ⚡"
        _open(['spotify'], shell=True)
        return "Opening Spotify ⚡"

    if c in ("play", "resume"):
        if arg:
            url = f"https://open.spotify.com/search/{urllib.parse.quote(arg)}"
            _open_url(url)
            return f"Searching Spotify: \"{arg}\" ⚡"
        try:
            from spotify_client import play_pause
            return play_pause()
        except Exception:
            return "Spotify not available ⚡"

    if c == "pause":
        try:
            from spotify_client import play_pause
            return play_pause()
        except Exception:
            return "Spotify not available ⚡"

    if c in ("next", "skip"):
        try:
            from spotify_client import next_track
            return next_track()
        except Exception:
            return "Spotify not available ⚡"

    if c in ("prev", "previous", "back"):
        try:
            from spotify_client import prev_track
            return prev_track()
        except Exception:
            return "Spotify not available ⚡"

    if c in ("np", "nowplaying", "playing"):
        try:
            from spotify_client import get_spotify_client
            info = get_spotify_client().current_track_info()
            return f"Now playing: {info} ⚡" if info else "Nothing playing ⚡"
        except Exception:
            return "Spotify not available ⚡"

    # ── Apps ───────────────────────────────────────────────────────────────────
    if c == "notepad":
        _open(['notepad.exe'])
        if arg:
            import threading
            threading.Thread(target=_type_text, args=(arg,), daemon=True).start()
            return f"Notepad opened — typing: \"{arg}\" ⚡"
        return "Opening Notepad ⚡"

    if c in ("calc", "calculator"):
        _open(['calc.exe'])
        return "Opening Calculator ⚡"

    if c in ("explorer", "files"):
        _open(['explorer.exe'])
        return "Opening File Explorer ⚡"

    if c == "settings":
        _open(['ms-settings:'], shell=True)
        return "Opening Windows Settings ⚡"

    if c in ("taskmgr", "taskmanager"):
        _open(['taskmgr.exe'])
        return "Opening Task Manager ⚡"

    if c in ("cmd", "terminal"):
        _open(['cmd.exe'])
        return "Opening Command Prompt ⚡"

    if c in ("ps", "powershell"):
        _open(['powershell.exe'])
        return "Opening PowerShell ⚡"

    if c == "paint":
        _open(['mspaint.exe'])
        return "Opening Paint ⚡"

    if c == "open":
        if not arg:
            return "Usage: /open [app name or url]"
        name = arg.lower().strip()
        if name in _KNOWN_APPS:
            _open([_KNOWN_APPS[name]], shell=True)
            return f"Opening {arg.title()} ⚡"
        if '.' in name:
            url = name if name.startswith(('http://', 'https://')) else 'https://' + name
            _open_url(url)
            return f"Opening {url} ⚡"
        _open([name], shell=True)
        return f"Trying to open: {arg} ⚡"

    if c in _KNOWN_APPS:
        _open([_KNOWN_APPS[c]], shell=True)
        return f"Opening {c.title()} ⚡"

    # ── System ─────────────────────────────────────────────────────────────────
    if c == "time":
        now = datetime.datetime.now()
        return f"It is {now.strftime('%I:%M %p')}, {USER_NAME}. ⚡"

    if c == "date":
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}, {USER_NAME}."

    if c == "lock":
        ctypes.windll.user32.LockWorkStation()
        return "Locking the screen ⚡"

    if c in ("desktop", "showdesktop"):
        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
        return "Showing desktop ⚡"

    if c in ("volup", "vol+"):
        for _ in range(5): _send_keys(0xAF)
        return "Volume up ⚡"

    if c in ("voldown", "vol-"):
        for _ in range(5): _send_keys(0xAE)
        return "Volume down ⚡"

    if c == "mute":
        _send_keys(0xAD)
        return "Mute toggled ⚡"

    if c in ("screenshot", "ss"):
        if screenshot_b64:
            try:
                import base64, io
                from PIL import Image
                ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"screenshot_{ts}.png"
                img  = Image.open(io.BytesIO(base64.b64decode(screenshot_b64)))
                img.save(path)
                return f"Screenshot saved: {path} ⚡"
            except Exception as e:
                return f"Could not save screenshot: {e}"
        return "No screenshot available. Press Ctrl+R first."

    if c in ("sysinfo", "sys", "info"):
        try:
            import platform, psutil
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            bat  = psutil.sensors_battery()
            bat_str = (
                f"{bat.percent:.0f}% {'(charging)' if bat.power_plugged else '(on battery)'}"
                if bat else "N/A"
            )
            return (
                f"System Report, {USER_NAME}:\n"
                f"  OS:      {platform.system()} {platform.release()}\n"
                f"  CPU:     {cpu}% usage\n"
                f"  RAM:     {ram.percent}% ({ram.used//1024**2} MB / {ram.total//1024**2} MB)\n"
                f"  Disk:    {disk.percent}% used\n"
                f"  Battery: {bat_str} ⚡"
            )
        except ImportError:
            return "psutil not installed — run: pip install psutil"
        except Exception as e:
            return f"Could not read system info: {e}"

    # ── Clipboard ──────────────────────────────────────────────────────────────
    if c in ("clip", "clipboard"):
        try:
            import pyperclip
            content = pyperclip.paste()
            if content:
                preview = content[:500] + ("…" if len(content) > 500 else "")
                return f"Clipboard:\n\n{preview}"
            return "Clipboard is empty."
        except Exception as e:
            return f"Could not read clipboard: {e}"

    if c in ("copy", "cp"):
        if not arg:
            return "Usage: /copy [text]"
        try:
            import pyperclip
            pyperclip.copy(arg)
            return f"Copied: \"{arg}\" ⚡"
        except Exception as e:
            return f"Could not copy: {e}"

    if c == "type":
        if not arg:
            return "Usage: /type [text]"
        import threading
        threading.Thread(target=_type_text, args=(arg, 0.3), daemon=True).start()
        return f"Typing: \"{arg}\" ⚡"

    # ── Other ──────────────────────────────────────────────────────────────────
    if c == "vault":
        return "__OPEN_VAULT__"

    if c in ("help", "?", "commands"):
        return _slash_help()

    # Unknown slash command — let AI handle it
    return f"Unknown command: /{c}\nType /help to see all available commands."


# ── Main handler ──────────────────────────────────────────────────────────────

def process(text: str, screenshot_b64: Optional[str] = None) -> Optional[str]:
    """
    Try to handle the command locally.
    Returns a response string if handled, or None to fall through to AI.
    """
    t = text.strip()

    # ── Slash commands (highest priority) ──────────────────────────────────────
    if t.startswith('/'):
        parts = t[1:].split(None, 1)          # split off command word
        cmd   = parts[0] if parts else ''
        arg   = parts[1].strip() if len(parts) > 1 else ''
        if cmd:
            return _handle_slash(cmd, arg, screenshot_b64)

    # ── Password vault ─────────────────────────────────────────────────────────
    if _VAULT_RE.search(t):
        return "__OPEN_VAULT__"

    # ── Web search (real results via DuckDuckGo) ───────────────────────────────
    m = _WEB_SEARCH_RE.search(t)
    if m:
        query = m.group(1).strip()
        logger.info(f"Local: real web search '{query[:50]}'")
        try:
            from web_tools import web_search
            return web_search(query)
        except Exception as e:
            return f"Web search error: {e}"

    # ── Fetch/scrape a web page ────────────────────────────────────────────────
    m = _FETCH_PAGE_RE.search(t)
    if m:
        url = m.group(1).strip()
        logger.info(f"Local: fetch page '{url}'")
        try:
            from web_tools import fetch_page_text
            text = fetch_page_text(url)
            return f"Content from {url}:\n\n{text}"
        except Exception as e:
            return f"Page fetch error: {e}"

    # ── Spotify / media controls ───────────────────────────────────────────────
    # "play X on spotify" — must check BEFORE generic play/pause
    m = _SPOT_PLAY_Q_RE.search(t)
    if m:
        query = m.group(1).strip()
        logger.info(f"Local: Spotify play '{query}'")
        try:
            from spotify_client import get_spotify_client
            sp = get_spotify_client()
            result = sp.search_and_play(query)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Spotify search failed: {e}")
        # Fallback: open Spotify + search on YouTube
        url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
        _open_url(url)
        return f"Searching Spotify for: {query} ⚡"

    if _SPOT_NOW_RE.search(t):
        try:
            from spotify_client import get_spotify_client
            info = get_spotify_client().current_track_info()
            if info:
                return f"Now playing: {info} ⚡"
        except Exception:
            pass
        return "Spotify track info unavailable — make sure Spotify is running ⚡"

    if _SPOT_PAUSE_RE.search(t):
        from spotify_client import play_pause
        return play_pause()

    if _SPOT_PLAY_RE.search(t):
        from spotify_client import play_pause
        return play_pause()

    if _SPOT_NEXT_RE.search(t):
        from spotify_client import next_track
        return next_track()

    if _SPOT_PREV_RE.search(t):
        from spotify_client import prev_track
        return prev_track()

    if _SPOT_STOP_RE.search(t):
        from spotify_client import stop_media
        return stop_media()

    if _SPOT_OPEN_RE.search(t):
        _open(['spotify'], shell=True)
        return "Opening Spotify ⚡"

    # ── Greetings — only when the message STARTS with a greeting word (≤6 words)
    if _GREETINGS_RE.match(t) and len(t.split()) <= 6:
        return (
            f"Hello, {USER_NAME}! I am Edward — the FullCUDA Alchemist. "
            "At your service. What shall we transmute today? ⚡"
        )

    # ── Identity ───────────────────────────────────────────────────────────────
    if _WHO_RE.search(t):
        return (
            "I am Edward, the FullCUDA Alchemist — your AI desktop assistant. "
            "I can see your screen, answer questions, open apps, automate tasks, "
            "manage your passwords, and execute actions. "
            "All equivalent exchange: you ask, I transmute. ⚡\n\n"
            "Type 'help' for a full list of instant commands."
        )

    # ── Help ───────────────────────────────────────────────────────────────────
    if _HELP_RE.search(t):
        return _slash_help() + (
            "\nKEYBOARD SHORTCUTS (while overlay is open):\n"
            "  Win+Shift+E  → activate Edward\n"
            "  Ctrl+R       → refresh screenshot\n"
            "  Ctrl+1/2/3   → cursor / window / full-screen mode\n"
            "  Enter        → transmute  |  Esc → close\n\n"
            "AI-POWERED (anything without a leading /):\n"
            "  Visual analysis, coding help, Q&A, computer control, reasoning"
        )

    # ── Time ───────────────────────────────────────────────────────────────────
    if _TIME_RE.search(t):
        now = datetime.datetime.now()
        return f"The time is {now.strftime('%I:%M %p')}, {USER_NAME}. ⚡"

    # ── Date ───────────────────────────────────────────────────────────────────
    if _DATE_RE.search(t):
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}, {USER_NAME}."

    # ── Open Notepad and TYPE ──────────────────────────────────────────────────
    m = _NOTEPAD_TYPE_RE.search(t)
    if m:
        content = m.group(1).strip()
        logger.info(f"Local: open notepad + type '{content[:40]}'")
        _open(['notepad.exe'])
        # Type in a background thread so we return the response immediately
        import threading
        threading.Thread(
            target=_type_text, args=(content,), daemon=True
        ).start()
        return f"Opening Notepad and typing: \"{content}\" ⚡"

    # ── YouTube search / play ──────────────────────────────────────────────────
    m = _YOUTUBE_RE.search(t)
    if m:
        query = m.group(1).strip()
        logger.info(f"Local: youtube search '{query}'")
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        _open_url(url)
        return f"Opening YouTube and searching for: \"{query}\" ⚡"

    # ── Open browser + GO TO URL ───────────────────────────────────────────────
    m = _BROWSER_GOTO_RE.search(t)
    if m:
        dest = m.group(1).strip()
        if not dest.startswith(('http://', 'https://')):
            dest = 'https://' + dest
        logger.info(f"Local: browser → {dest}")
        _open_url(dest)
        return f"Navigating to {dest} ⚡"

    # ── Open browser + SEARCH ──────────────────────────────────────────────────
    m = _BROWSER_SEARCH_RE.search(t)
    if m:
        query = m.group(1).strip()
        logger.info(f"Local: browser search '{query}'")
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        _open_url(url)
        return f"Searching Google for: \"{query}\" ⚡"

    # ── Plain "search for X" / "google X" ─────────────────────────────────────
    m = _SEARCH_RE.search(t)
    if m:
        query = m.group(1).strip()
        logger.info(f"Local: search '{query}'")
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        _open_url(url)
        return f"Googling: \"{query}\" ⚡"

    # ── Copy text to clipboard ────────────────────────────────────────────────
    m = _CLIP_WRITE_RE.search(t)
    if m:
        content = m.group(1).strip()
        try:
            import pyperclip
            pyperclip.copy(content)
            return f"Copied to clipboard: \"{content}\" ⚡"
        except Exception as e:
            return f"Could not copy to clipboard: {e}"

    # ── Type into active window ────────────────────────────────────────────────
    m = _TYPE_RE.search(t)
    if m:
        content = m.group(1).strip()
        logger.info(f"Local: type '{content[:40]}'")
        import threading
        threading.Thread(
            target=_type_text, args=(content, 0.3), daemon=True
        ).start()
        return f"Typing: \"{content}\" ⚡"

    # ── Window management ──────────────────────────────────────────────────────
    if _FULLSCREEN_RE.search(t):
        import pyautogui
        pyautogui.hotkey('win', 'up')
        return "Maximizing window! ⚡"

    if _MINIMIZE_RE.search(t):
        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)   # Win
        ctypes.windll.user32.keybd_event(0x28, 0, 0, 0)   # Down
        ctypes.windll.user32.keybd_event(0x28, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
        return "Window minimized! ⚡"

    if _CLOSE_WIN_RE.search(t):
        import pyautogui
        pyautogui.hotkey('alt', 'f4')
        return "Closing window! ⚡"

    if _ALT_TAB_RE.search(t):
        import pyautogui
        pyautogui.hotkey('alt', 'tab')
        return "Switching window! ⚡"

    # ── Open browser (plain — no search query) ────────────────────────────────
    m = _OPEN_BROWSER_RE.search(t)
    if m:
        what = m.group(1).lower()
        if 'firefox' in what:
            _open(['firefox'], shell=True)
            return "Opening Firefox! ⚡"
        elif 'chrome' in what:
            _open(['chrome'], shell=True)
            return "Opening Chrome! ⚡"
        else:
            _open(['msedge'], shell=True)
            return "Opening Microsoft Edge! ⚡"

    # ── Open named apps (BEFORE goto-site so "open discord" doesn't become a URL)
    if _OPEN_NOTEPAD_RE.search(t):
        _open(['notepad.exe'])
        return "Opening Notepad! ⚡"

    if _OPEN_CALC_RE.search(t):
        _open(['calc.exe'])
        return "Opening Calculator! ⚡"

    if _OPEN_EXPLORER_RE.search(t):
        _open(['explorer.exe'])
        return "Opening File Explorer! ⚡"

    if _OPEN_SETTINGS_RE.search(t):
        _open(['ms-settings:'], shell=True)
        return "Opening Windows Settings! ⚡"

    if _OPEN_TASKMGR_RE.search(t):
        _open(['taskmgr.exe'])
        return "Opening Task Manager! ⚡"

    if _OPEN_PAINT_RE.search(t):
        _open(['mspaint.exe'])
        return "Opening Paint! ⚡"

    if _OPEN_CMD_RE.search(t):
        what = _OPEN_CMD_RE.search(t).group(1).lower()
        if 'powershell' in what:
            _open(['powershell.exe'])
            return "Opening PowerShell! ⚡"
        _open(['cmd.exe'])
        return "Opening Command Prompt! ⚡"

    m = _OPEN_APP_RE.search(t)
    if m:
        app_name = m.group(1).lower()
        cmd = _APP_CMDS.get(app_name, app_name)
        logger.info(f"Local: open app '{app_name}' → '{cmd}'")
        _open([cmd], shell=True)
        return f"Opening {app_name.title()}! ⚡"

    # ── "go to site.com" / "visit reddit.com" (requires real TLD) ────────────
    m = _GOTO_SITE_RE.search(t)
    if m:
        site = m.group(1).strip()
        if not site.startswith(('http://', 'https://')):
            site = 'https://' + site
        logger.info(f"Local: goto {site}")
        _open_url(site)
        return f"Opening {site} ⚡"

    # ── Lock screen ────────────────────────────────────────────────────────────
    if _LOCK_RE.search(t):
        ctypes.windll.user32.LockWorkStation()
        return "Locking the screen. Equivalent exchange: you rest, the screen sleeps. ⚡"

    # ── Show desktop ───────────────────────────────────────────────────────────
    if _DESKTOP_RE.search(t):
        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)
        return "Minimizing all windows — showing the desktop! ⚡"

    # ── Volume ─────────────────────────────────────────────────────────────────
    if _VOL_UP_RE.search(t):
        for _ in range(5):
            _send_keys(0xAF)
        return "Volume increased! ⚡"

    if _VOL_DOWN_RE.search(t):
        for _ in range(5):
            _send_keys(0xAE)
        return "Volume decreased!"

    if _VOL_MUTE_RE.search(t):
        _send_keys(0xAD)
        return "Audio muted/unmuted! ⚡"

    # ── Clipboard read ─────────────────────────────────────────────────────────
    if _CLIPBOARD_RE.search(t):
        try:
            import pyperclip
            content = pyperclip.paste()
            if content:
                preview = content[:500] + ("…" if len(content) > 500 else "")
                return f"Your clipboard contains:\n\n{preview}"
            return "Your clipboard is empty."
        except Exception as e:
            return f"Could not read clipboard: {e}"

    # ── Screenshot save ────────────────────────────────────────────────────────
    if _SCREENSHOT_RE.search(t):
        if screenshot_b64:
            try:
                import base64, io
                from PIL import Image
                ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"screenshot_{ts}.png"
                raw  = base64.b64decode(screenshot_b64)
                img  = Image.open(io.BytesIO(raw))
                img.save(path)
                return f"Screenshot saved as {path} ⚡"
            except Exception as e:
                return f"Could not save screenshot: {e}"
        return "No screenshot available. Press Ctrl+R first."

    # ── System info ────────────────────────────────────────────────────────────
    if _SYSINFO_RE.search(t):
        try:
            import platform, psutil
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            bat  = psutil.sensors_battery()
            bat_str = (
                f"{bat.percent:.0f}% {'(charging)' if bat.power_plugged else '(on battery)'}"
                if bat else "N/A"
            )
            return (
                f"System Transmutation Report, {USER_NAME}:\n"
                f"  OS:      {platform.system()} {platform.release()}\n"
                f"  CPU:     {cpu}% usage\n"
                f"  RAM:     {ram.percent}% used ({ram.used // 1024**2} MB / {ram.total // 1024**2} MB)\n"
                f"  Disk:    {disk.percent}% used\n"
                f"  Battery: {bat_str} ⚡"
            )
        except ImportError:
            return "psutil not installed — run: pip install psutil"
        except Exception as e:
            return f"Could not read system info: {e}"

    return None   # not handled locally — send to AI
