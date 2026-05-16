"""
Edward Agent Module
Handles global hotkey listening and multi-mode screenshot capture.
"""

import ctypes
import ctypes.wintypes
import io
import base64
from typing import Callable, Optional, Tuple
from pynput import keyboard
from pynput.mouse import Controller as MouseController
from mss import mss
from PIL import Image, ImageDraw

from config import HOTKEY_ENABLED, HOTKEY_COMBINATION, ScreenshotMode, CURSOR_REGION_SIZE
from logger import get_logger

logger = get_logger(__name__)


def _get_foreground_window_rect() -> Tuple[int, int, int, int]:
    """Return (left, top, width, height) of the current foreground window."""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    left   = rect.left
    top    = rect.top
    width  = rect.right  - rect.left
    height = rect.bottom - rect.top
    return left, top, width, height


class EdwardAgent:
    """
    Listens for the global hotkey and captures screenshots in one of three modes:
      • CURSOR_REGION — ~1 000 px square around the mouse pointer (fast, focused)
      • ACTIVE_WINDOW — the foreground window (medium)
      • FULL_SCREEN   — all monitors combined (slow, widest context)
    """

    def __init__(self, on_trigger_callback: Optional[Callable] = None):
        self.on_trigger_callback = on_trigger_callback
        self.listener: Optional[keyboard.GlobalHotKeys] = None
        self.is_running = False
        self.mouse = MouseController()
        self.screenshot_mode = ScreenshotMode.CURSOR_REGION
        # HWND of the window that was foreground when Win+Shift+E fired.
        # Used by capture_active_window so it never accidentally captures the overlay.
        self._target_hwnd: Optional[int] = None
        self.last_region: dict = {}   # populated after every capture; used for coord context
        logger.info("Edward Agent initialised — multi-mode capture ready")

    # ── Public capture API ────────────────────────────────────────────────────

    def capture_for_mode(
        self, mode: Optional[ScreenshotMode] = None
    ) -> Tuple[bytes, str]:
        """
        Capture a screenshot using the given mode (or self.screenshot_mode).
        Returns (image_bytes, base64_string).
        Also updates self.last_region with coordinate-mapping info.
        """
        mode = mode or self.screenshot_mode
        if mode == ScreenshotMode.CURSOR_REGION:
            img_bytes, img_base64, _ = self.capture_cursor_region(CURSOR_REGION_SIZE)
        elif mode == ScreenshotMode.ACTIVE_WINDOW:
            img_bytes, img_base64 = self.capture_active_window()
        else:
            img_bytes, img_base64 = self.capture_full_screen()
        return img_bytes, img_base64

    def get_cursor_pos(self) -> Tuple[int, int]:
        """Return the current screen cursor position."""
        x, y = self.mouse.position
        return int(x), int(y)

    def capture_cursor_region(
        self, region_size: int = 1000
    ) -> Tuple[bytes, str, Tuple[int, int]]:
        """
        Capture a square around the cursor and draw a gold crosshair at the cursor centre.
        Returns (image_bytes, base64_string, cursor_position).
        """
        try:
            cursor_x, cursor_y = self.mouse.position

            with mss() as sct:
                monitor = sct.monitors[0]
                screen_w = monitor['width']
                screen_h = monitor['height']

                half = region_size // 2
                left   = max(0, cursor_x - half)
                top    = max(0, cursor_y - half)
                right  = min(screen_w, cursor_x + half)
                bottom = min(screen_h, cursor_y + half)

                region = {'left': left, 'top': top, 'width': right - left, 'height': bottom - top}
                shot   = sct.grab(region)
                img    = Image.frombytes("RGB", (shot.width, shot.height), shot.rgb)

                draw = ImageDraw.Draw(img)
                rx = cursor_x - left
                ry = cursor_y - top
                r  = 12
                draw.ellipse([rx - r, ry - r, rx + r, ry + r], outline='#DAA520', width=3)
                draw.line([rx - r - 5, ry, rx + r + 5, ry], fill='#DAA520', width=2)
                draw.line([rx, ry - r - 5, rx, ry + r + 5], fill='#DAA520', width=2)

                img_bytes  = self._to_bytes(img)
                img_base64 = base64.b64encode(img_bytes).decode()

                self.last_region = {
                    "mode":      "cursor_region",
                    "left":      left,
                    "top":       top,
                    "reg_w":     right - left,
                    "reg_h":     bottom - top,
                    "cursor_x":  cursor_x,
                    "cursor_y":  cursor_y,
                    "img_w":     shot.width,
                    "img_h":     shot.height,
                    "screen_w":  screen_w,
                    "screen_h":  screen_h,
                }
                logger.info(f"Cursor-region shot: {shot.width}×{shot.height} @ ({cursor_x},{cursor_y})")
                return img_bytes, img_base64, (cursor_x, cursor_y)

        except Exception as e:
            logger.error(f"capture_cursor_region failed: {e}")
            raise

    def capture_active_window(self) -> Tuple[bytes, str]:
        """
        Capture the window that was in the foreground when Win+Shift+E fired.
        Falls back to full-screen if the rect is degenerate.
        Using _target_hwnd avoids accidentally capturing the overlay itself.
        """
        try:
            if self._target_hwnd:
                rect = ctypes.wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(self._target_hwnd, ctypes.byref(rect))
                left   = rect.left
                top    = rect.top
                width  = rect.right  - rect.left
                height = rect.bottom - rect.top
            else:
                left, top, width, height = _get_foreground_window_rect()

            if width <= 0 or height <= 0:
                logger.warning("Active window has zero size — falling back to full screen")
                return self.capture_full_screen()

            with mss() as sct:
                monitor = sct.monitors[0]
                # Clamp to screen bounds
                left   = max(0, left)
                top    = max(0, top)
                width  = min(width,  monitor['width']  - left)
                height = min(height, monitor['height'] - top)

                region = {'left': left, 'top': top, 'width': width, 'height': height}
                shot   = sct.grab(region)
                img    = Image.frombytes("RGB", (shot.width, shot.height), shot.rgb)

                img_bytes  = self._to_bytes(img)
                img_base64 = base64.b64encode(img_bytes).decode()

                cx, cy = self.mouse.position
                self.last_region = {
                    "mode":     "active_window",
                    "left":     left,
                    "top":      top,
                    "reg_w":    width,
                    "reg_h":    height,
                    "cursor_x": int(cx),
                    "cursor_y": int(cy),
                    "img_w":    shot.width,
                    "img_h":    shot.height,
                    "screen_w": monitor['width'],
                    "screen_h": monitor['height'],
                }
                logger.info(f"Active-window shot: {width}×{height}")
                return img_bytes, img_base64

        except Exception as e:
            logger.error(f"capture_active_window failed: {e}")
            raise

    def capture_full_screen(self) -> Tuple[bytes, str]:
        """
        Capture all monitors as a single image.
        Returns (image_bytes, base64_string).
        """
        try:
            with mss() as sct:
                monitor = sct.monitors[0]
                shot    = sct.grab(monitor)
                img     = Image.frombytes("RGB", (shot.width, shot.height), shot.rgb)

                img_bytes  = self._to_bytes(img)
                img_base64 = base64.b64encode(img_bytes).decode()

                cx, cy = self.mouse.position
                self.last_region = {
                    "mode":     "full_screen",
                    "left":     0,
                    "top":      0,
                    "reg_w":    shot.width,
                    "reg_h":    shot.height,
                    "cursor_x": int(cx),
                    "cursor_y": int(cy),
                    "img_w":    shot.width,
                    "img_h":    shot.height,
                    "screen_w": shot.width,
                    "screen_h": shot.height,
                }
                logger.info(f"Full-screen shot: {shot.width}×{shot.height}")
                return img_bytes, img_base64

        except Exception as e:
            logger.error(f"capture_full_screen failed: {e}")
            raise

    # ── Hotkey handler ────────────────────────────────────────────────────────

    def _on_hotkey_pressed(self):
        logger.info("⚡ Transmutation Circle Activated! (Win+Shift+E)")
        try:
            # Save the foreground window NOW, before the overlay takes focus
            self._target_hwnd = ctypes.windll.user32.GetForegroundWindow()
            img_bytes, img_base64 = self.capture_for_mode()
            if self.on_trigger_callback:
                self.on_trigger_callback(img_bytes, img_base64)
            else:
                logger.warning("No trigger callback registered")
        except Exception as e:
            logger.error(f"Error in hotkey handler: {e}")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        if not HOTKEY_ENABLED:
            logger.info("Hotkey disabled in config")
            return
        if self.is_running:
            logger.warning("Agent already running")
            return
        try:
            self.listener = keyboard.GlobalHotKeys(
                {'<cmd>+<shift>+e': self._on_hotkey_pressed}
            )
            self.listener.start()
            self.is_running = True
            logger.info("Edward Agent started — listening for Win+Shift+E")
        except Exception as e:
            logger.error(f"Failed to start agent: {e}")
            raise

    def stop(self):
        if not self.is_running:
            return
        try:
            if self.listener:
                self.listener.stop()
                self.listener = None
            self.is_running = False
            logger.info("Edward Agent stopped")
        except Exception as e:
            logger.error(f"Error stopping agent: {e}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _to_bytes(img: Image.Image) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format='PNG', optimize=True)
        return buf.getvalue()
