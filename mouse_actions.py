"""
Edward Mouse & Keyboard Actions
Uses pynput (already installed, proven reliable on Windows) for all
mouse and keyboard control.  pyautogui is gone — it had DPI-scaling bugs.

Swaps the system cursor to cursor_action.png while Edward controls the mouse.
"""

import ctypes
import ctypes.wintypes as wintypes
import re
import time
from pathlib import Path
from typing import Optional

from logger import get_logger

logger = get_logger(__name__)

# ── Make this process DPI-aware so coordinates match what the user sees ────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()    # older fallback
    except Exception:
        pass

# ── pynput controllers (module-level singletons) ──────────────────────────────
try:
    from pynput.mouse import Button as _Btn, Controller as _MouseCtrl
    from pynput.keyboard import Key as _Key, Controller as _KbCtrl
    _mouse    = _MouseCtrl()
    _keyboard = _KbCtrl()
    _PYNPUT_OK = True
except ImportError:
    _PYNPUT_OK = False
    logger.error("pynput not installed — mouse/keyboard actions unavailable")

# ── Key name → pynput Key mapping ─────────────────────────────────────────────
if _PYNPUT_OK:
    _KEY_MAP: dict = {
        "ctrl":      _Key.ctrl,      "control":  _Key.ctrl,
        "shift":     _Key.shift,
        "alt":       _Key.alt,
        "win":       _Key.cmd,       "cmd":      _Key.cmd,
        "enter":     _Key.enter,     "return":   _Key.enter,
        "tab":       _Key.tab,
        "esc":       _Key.esc,       "escape":   _Key.esc,
        "space":     _Key.space,
        "backspace": _Key.backspace,
        "delete":    _Key.delete,    "del":      _Key.delete,
        "up":        _Key.up,        "down":     _Key.down,
        "left":      _Key.left,      "right":    _Key.right,
        "home":      _Key.home,      "end":      _Key.end,
        "pageup":    _Key.page_up,   "pagedown": _Key.page_down,
        "f1":  _Key.f1,  "f2":  _Key.f2,  "f3":  _Key.f3,  "f4":  _Key.f4,
        "f5":  _Key.f5,  "f6":  _Key.f6,  "f7":  _Key.f7,  "f8":  _Key.f8,
        "f9":  _Key.f9,  "f10": _Key.f10, "f11": _Key.f11, "f12": _Key.f12,
    }
else:
    _KEY_MAP = {}


def _resolve_key(name: str):
    """Return a pynput Key object or single-char string."""
    n = name.lower().strip()
    if n in _KEY_MAP:
        return _KEY_MAP[n]
    return name[0] if name else name   # single character


def _press_combo(combo: str):
    """Press a key combination like 'ctrl+c' or a single key like 'enter'."""
    parts = [p.strip() for p in combo.split("+")]
    keys  = [_resolve_key(p) for p in parts]
    for k in keys:
        _keyboard.press(k)
    for k in reversed(keys):
        _keyboard.release(k)


# ── Action regex ──────────────────────────────────────────────────────────────

_ACTION_RE = re.compile(r'\[ACTION:\s*(\w+)\(([^)]*)\)\]', re.I)


def _parse_args(raw: str) -> list:
    result = []
    for part in raw.split(","):
        part = part.strip().strip("\"'")
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            try:
                result.append(float(part))
            except ValueError:
                result.append(part)
    return result


# ── Windows cursor-swap structs ───────────────────────────────────────────────

class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize",          wintypes.DWORD),
        ("biWidth",         wintypes.LONG),
        ("biHeight",        wintypes.LONG),
        ("biPlanes",        wintypes.WORD),
        ("biBitCount",      wintypes.WORD),
        ("biCompression",   wintypes.DWORD),
        ("biSizeImage",     wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed",       wintypes.DWORD),
        ("biClrImportant",  wintypes.DWORD),
    ]

class _ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon",    wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask",  wintypes.HANDLE),
        ("hbmColor", wintypes.HANDLE),
    ]

_CURSOR_PNG = Path(__file__).parent / "assets" / "cursor_action.png"
_OCR_NORMAL = 32512   # IDC_ARROW slot


def _make_hcursor(path: Path, hotspot_x: int = 0, hotspot_y: int = 0) -> Optional[int]:
    try:
        from PIL import Image
        user32 = ctypes.windll.user32
        gdi32  = ctypes.windll.gdi32
        cx = user32.GetSystemMetrics(13)
        cy = user32.GetSystemMetrics(14)
        img = Image.open(path).convert("RGBA").resize((cx, cy), Image.LANCZOS)
        r, g, b, a = img.split()
        from PIL import Image as _I
        bgra = _I.merge("RGBA", (b, g, r, a)).transpose(_I.FLIP_TOP_BOTTOM)
        bgra_bytes = bgra.tobytes()
        bmi = _BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.biWidth = cx; bmi.biHeight = cy
        bmi.biPlanes = 1; bmi.biBitCount = 32; bmi.biCompression = 0
        pv = ctypes.c_void_p()
        hbm_color = gdi32.CreateDIBSection(None, ctypes.byref(bmi), 0, ctypes.byref(pv), None, 0)
        if hbm_color and pv.value:
            ctypes.memmove(pv.value, bgra_bytes, len(bgra_bytes))
        hbm_mask = gdi32.CreateBitmap(cx, cy, 1, 1, None)
        ii = _ICONINFO()
        ii.fIcon = False; ii.xHotspot = hotspot_x; ii.yHotspot = hotspot_y
        ii.hbmMask = hbm_mask; ii.hbmColor = hbm_color
        hcursor = user32.CreateIconIndirect(ctypes.byref(ii))
        gdi32.DeleteObject(hbm_color); gdi32.DeleteObject(hbm_mask)
        return hcursor or None
    except Exception as e:
        logger.warning(f"Could not build action cursor: {e}")
        return None


def _set_action_cursor():
    if not _CURSOR_PNG.exists():
        return
    hcursor = _make_hcursor(_CURSOR_PNG)
    if hcursor:
        try:
            ctypes.windll.user32.SetSystemCursor(hcursor, _OCR_NORMAL)
            logger.info("Action cursor set")
        except Exception as e:
            logger.warning(f"SetSystemCursor: {e}")


def _restore_cursor():
    try:
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0)
        logger.info("Cursor restored")
    except Exception as e:
        logger.warning(f"Restore cursor: {e}")


# ── Single action executor ─────────────────────────────────────────────────────

_MOUSE_NAMES = {"mouse_move", "mouse_click", "mouse_right_click",
                "mouse_double_click", "scroll"}


def _clamp_to_screen(x: int, y: int) -> tuple[int, int]:
    """Clamp coordinates to the actual screen bounds at call time."""
    info = get_screen_info()
    sw, sh = info["width"], info["height"]
    cx = max(0, min(x, sw - 1))
    cy = max(0, min(y, sh - 1))
    if cx != x or cy != y:
        logger.warning(f"Coordinate ({x},{y}) out of bounds for {sw}x{sh} screen — clamped to ({cx},{cy})")
    return cx, cy


def execute_action(name: str, args: list) -> str:
    if not _PYNPUT_OK:
        return "pynput unavailable"

    name = name.lower().strip()
    try:
        if name == "mouse_move":
            x, y = _clamp_to_screen(int(args[0]), int(args[1]))
            _mouse.position = (x, y)
            logger.info(f"Mouse moved to ({x},{y})")
            return f"Moved mouse to ({x}, {y})"

        elif name == "mouse_click":
            x, y = _clamp_to_screen(int(args[0]), int(args[1]))
            _mouse.position = (x, y)
            time.sleep(0.05)
            _mouse.press(_Btn.left)
            time.sleep(0.05)
            _mouse.release(_Btn.left)
            logger.info(f"Clicked ({x},{y})")
            return f"Clicked ({x}, {y})"

        elif name == "mouse_right_click":
            x, y = _clamp_to_screen(int(args[0]), int(args[1]))
            _mouse.position = (x, y)
            time.sleep(0.05)
            _mouse.click(_Btn.right)
            return f"Right-clicked ({x}, {y})"

        elif name == "mouse_double_click":
            x, y = _clamp_to_screen(int(args[0]), int(args[1]))
            _mouse.position = (x, y)
            time.sleep(0.05)
            _mouse.click(_Btn.left, 2)
            return f"Double-clicked ({x}, {y})"

        elif name in ("type_text", "type"):
            text = str(args[0]) if args else ""
            _keyboard.type(text)
            return f"Typed: {text[:40]}"

        elif name in ("key_press", "key"):
            combo = str(args[0]) if args else ""
            _press_combo(combo)
            return f"Key: {combo}"

        elif name == "scroll":
            x, y      = _clamp_to_screen(int(args[0]), int(args[1]))
            direction  = str(args[2]).lower() if len(args) > 2 else "down"
            amount     = int(args[3])          if len(args) > 3 else 3
            _mouse.position = (x, y)
            dy = amount if direction == "up" else -amount
            _mouse.scroll(0, dy)
            return f"Scrolled {direction} {amount}× at ({x}, {y})"

        else:
            return f"Unknown action: {name}"

    except (IndexError, ValueError) as e:
        return f"Bad args for {name}: {e}"
    except Exception as e:
        logger.error(f"Action {name} failed: {e}", exc_info=True)
        return f"Action failed: {e}"


# ── Batch executor ────────────────────────────────────────────────────────────

def parse_and_execute_actions(text: str, inter_delay: float = 0.3) -> tuple[str, list[str]]:
    """
    Find [ACTION:...] tags, execute them in order, return (clean_text, results).
    Sets Edward's custom cursor for the duration of any mouse actions.
    """
    results: list[str] = []
    matches = list(_ACTION_RE.finditer(text))

    if not matches:
        return _ACTION_RE.sub("", text).strip(), results

    has_mouse = any(m.group(1).lower() in _MOUSE_NAMES for m in matches)
    if has_mouse:
        _set_action_cursor()

    try:
        for m in matches:
            aname    = m.group(1)
            args_str = m.group(2).strip()
            args     = _parse_args(args_str) if args_str else []
            logger.info(f"ACTION: {aname}({args})")
            result = execute_action(aname, args)
            results.append(result)
            logger.info(f"  → {result}")
            time.sleep(inter_delay)
    finally:
        if has_mouse:
            _restore_cursor()

    return _ACTION_RE.sub("", text).strip(), results


# ── Screen info ───────────────────────────────────────────────────────────────

def get_screen_info() -> dict:
    try:
        from mss import mss as _mss
        with _mss() as sct:
            m = sct.monitors[0]
            return {"width": m["width"], "height": m["height"]}
    except Exception:
        return {"width": 1920, "height": 1080}
