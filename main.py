"""
Edward - Local Windows Desktop AI Assistant
Main entry point that coordinates all components
"""

import os
import signal
import sys
import warnings

# Suppress NumPy and other startup warnings
warnings.filterwarnings('ignore')
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

# Qt 6 sets DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 automatically — no manual call needed.
# Suppress noisy third-party loggers before any imports that trigger them.
import logging as _logging
_logging.getLogger("comtypes").setLevel(_logging.WARNING)

# Suppress NumPy 2.x compatibility warnings
import numpy as np
if hasattr(np, '__version__') and np.__version__.startswith('1.'):
    pass  # NumPy 1.x is fine

from pathlib import Path
from typing import Optional
import asyncio
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal as pyqtSignal, QObject, Slot, QTimer
import pystray
from PIL import Image, ImageDraw

from agent import EdwardAgent
from overlay import EdwardOverlay
from tts import get_tts
from widgets.acting_indicator import ActingIndicator
from stt import get_stt
from gemma_client import get_gemma_client
from context_enhancer import get_context_enhancer
from ui import PasswordUnlockDialog, PasswordManagerDialog, SettingsDialog, ConfirmationDialog
from computer_actions import create_file, edit_file, open_file_or_app
from local_commands import process as local_process
from wake_word import WakeWordDetector
from mouse_actions import parse_and_execute_actions
from config import USER_NAME, WAKE_WORD_ENABLED
from logger import setup_logger

# Setup colored logging
logger = setup_logger(__name__, log_file='logs/edward.log')


class HotkeySignalBridge(QObject):
    """Bridge to safely emit signals from background threads to Qt main thread"""
    triggered = pyqtSignal(bytes, str)


class SpeechSignalBridge(QObject):
    """Bridge to safely emit speech recognition results to Qt main thread"""
    speech_result = pyqtSignal(object)  # Will emit Optional[str]


class TraySignalBridge(QObject):
    """Bridge to safely open dialogs from pystray's background thread"""
    open_vault    = pyqtSignal()
    open_settings = pyqtSignal()
    show_overlay  = pyqtSignal()


class WakeSignalBridge(QObject):
    """Bridge to safely trigger overlay from the wake-word background thread"""
    detected = pyqtSignal(str)   # payload: text command (may be empty string)


class Edward:
    """
    Main Edward application class.
    Coordinates agent, overlay, TTS, and system tray.
    """
    
    def __init__(self):
        """Initialize Edward application"""
        logger.info("=" * 60)
        logger.info("⚡ EDWARD ELRIC - FULLMETAL ALCHEMIST ⚡")
        logger.info("Equivalent Exchange: To obtain, something of equal value must be lost")
        logger.info("=" * 60)
        logger.info("Initializing Edward's Automail systems...")
        
        # Create Qt application
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Setup asyncio event loop for Qt
        try:
            import qasync
            self.loop = qasync.QEventLoop(self.app)
            asyncio.set_event_loop(self.loop)
        except ImportError:
            logger.warning("qasync not installed, using default event loop")
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        # Create signal bridges for thread-safe communication
        self.hotkey_bridge = HotkeySignalBridge()
        self.speech_bridge = SpeechSignalBridge()
        self.tray_bridge   = TraySignalBridge()
        self.wake_bridge   = WakeSignalBridge()
        
        # Initialize components
        self.overlay = EdwardOverlay()
        self.acting_indicator = ActingIndicator()
        self.agent = EdwardAgent(on_trigger_callback=self._on_hotkey_triggered)
        self.tts = get_tts()
        self.stt = get_stt()
        self.gemma_client = get_gemma_client()
        self.context_enhancer = get_context_enhancer()
        
        # Give overlay a capture callable so it can refresh the thumbnail periodically
        self.overlay._refresh_capture_fn = self.agent.capture_for_mode

        # Connect signals
        self.overlay.question_submitted.connect(self._on_question_submitted)
        self.hotkey_bridge.triggered.connect(self._show_overlay_safe)
        self.overlay.mic_button.clicked.connect(self._on_mic_button_clicked)
        self.speech_bridge.speech_result.connect(self._on_speech_result_safe)
        self.overlay.screenshot_mode_changed.connect(self._on_screenshot_mode_changed)
        self.overlay.backend_changed.connect(self._on_backend_changed)
        self.tray_bridge.open_vault.connect(self._show_password_vault_safe)
        self.tray_bridge.open_settings.connect(self._show_settings_safe)
        self.tray_bridge.show_overlay.connect(self._show_overlay_from_tray)
        self.wake_bridge.detected.connect(self._on_wake_detected_safe)

        self._auto_submit_speech = False   # True when mic was opened by wake word

        # Wake word detector — suppress while overlay is visible
        self.wake_detector = WakeWordDetector(
            on_wake_callback=self._on_wake_word_raw,
        )
        self.overlay.visibility_changed.connect(self._on_overlay_visibility)

        # System tray icon
        self.tray_icon = None
        
        logger.info("✓ Automail calibration complete")
        logger.info("✓ Alchemy circle activated")
        logger.info("Edward is ready for transmutation!")
        logger.info("=" * 60)
    
    def _on_hotkey_triggered(self, img_bytes: bytes, img_base64: str):
        """
        Called when hotkey is pressed (from background thread).
        Emits signal to show overlay safely in main thread.
        """
        logger.info("Hotkey triggered - emitting signal")
        self.hotkey_bridge.triggered.emit(img_bytes, img_base64)
    
    @Slot(bytes, str)
    def _show_overlay_safe(self, img_bytes: bytes, img_base64: str):
        """
        Shows overlay with screenshot data (runs in main Qt thread).
        """
        logger.info("Showing overlay in main thread")
        self.overlay.show_overlay(screenshot_data=(img_bytes, img_base64))
    
    def _on_mic_button_clicked(self):
        """Called when microphone button is clicked (manual). Clears auto-submit flag."""
        self._auto_submit_speech = False
        logger.info("Starting speech recognition...")
        self.overlay.set_status("Listening… ⚡")

        def on_speech_result(text: Optional[str]):
            self.speech_bridge.speech_result.emit(text)

        self.stt.listen_once_async(on_speech_result, timeout=5, phrase_time_limit=15)

    def _start_wake_listen(self):
        """Called by wake-word handler — mic opens with auto-submit enabled."""
        self._auto_submit_speech = True
        self.overlay.set_status("Listening… speak your command ⚡")

        def on_speech_result(text: Optional[str]):
            self.speech_bridge.speech_result.emit(text)

        self.stt.listen_once_async(on_speech_result, timeout=8, phrase_time_limit=15)

    @Slot(object)
    def _on_speech_result_safe(self, text: Optional[str]):
        """Handle speech recognition result on main thread."""
        if text:
            logger.info(f"Speech recognized: {text}")
            self.overlay.input_field.setPlainText(text)
            if self._auto_submit_speech:
                self._auto_submit_speech = False
                self.overlay.set_status("Recognized — transmuting… ⚡")
                QTimer.singleShot(400, lambda: self._on_question_submitted(text))
                return
            self.overlay.set_status("Speech recognized — press Enter or click Ask ⚡")
        else:
            logger.warning("No speech detected")
            self.overlay.set_status("No speech detected. Try again.", error=True)

        self.overlay.enable_input()
    
    @Slot(object)
    def _on_screenshot_mode_changed(self, mode):
        """Update agent mode and re-capture so the thumbnail refreshes immediately."""
        self.agent.screenshot_mode = mode
        self.overlay.set_status(f"Switched to {mode.value} mode — capturing…")
        try:
            img_bytes, img_base64 = self.agent.capture_for_mode(mode)
            self.overlay.update_screenshot(img_bytes, img_base64)
            self.overlay.set_status("")
        except Exception as e:
            logger.error(f"Re-capture failed after mode change: {e}")
            self.overlay.set_status(f"Capture failed: {e}", error=True)

    @Slot(str)
    def _on_backend_changed(self, name: str):
        """Hot-swap the AI backend."""
        self.gemma_client.set_backend(name)
        logger.info(f"Backend switched to {name}")

    def _on_question_submitted(self, question: str):
        """Called when user submits a question to Gemma 4."""
        logger.info(f"Processing question: {question[:50]}...")

        # Get screenshot data if available
        screenshot_base64 = None
        if self.overlay.screenshot_data:
            _, screenshot_base64 = self.overlay.screenshot_data
            logger.info("Including screenshot with question")

        # Fast path: local commands need no Ollama
        local_response = local_process(question, screenshot_base64)
        if local_response is not None:
            if local_response == "__OPEN_VAULT__":
                self.overlay.hide_overlay()
                self.tray_bridge.open_vault.emit()
            else:
                self.overlay.set_response(local_response)
                if self.tts.is_enabled and local_response:
                    self.tts.speak_async(local_response)
            self.overlay.enable_input()
            logger.info("Local command handled — skipping Gemma")
            return

        # Call API asynchronously
        asyncio.create_task(self._process_question_async(question, screenshot_base64))
    
    async def _process_question_async(self, question: str, screenshot_base64: Optional[str]):
        """Process question with Gemma 4 asynchronously."""
        self.acting_indicator.show_acting()
        try:
            # Clear previous response
            self.overlay.response_area.clear()
            
            # Build enhanced prompt with context (clipboard, conversation history, etc.)
            logger.info("Building enhanced prompt with context...")
            enhanced_prompt, context_metadata = self.context_enhancer.build_enhanced_prompt(
                user_question=question,
                screenshot_base64=screenshot_base64,
                include_clipboard=True,
                conversation_history=None  # TODO: Add conversation history from database
            )
            
            # Log what context was included
            if context_metadata.get('clipboard_included'):
                logger.info(f"Clipboard context added: {context_metadata['clipboard_type']}")
            if context_metadata.get('screenshot_included'):
                logger.info("Screenshot context included")
            
            # Ask Gemma 4 (Edward's alchemy!)
            full_response = ""
            region_info = dict(self.agent.last_region)  # snapshot; includes cursor pos
            # Always inject live cursor position even if region info is stale
            cx, cy = self.agent.get_cursor_pos()
            region_info["cursor_x"] = cx
            region_info["cursor_y"] = cy
            try:
                async for chunk in self.gemma_client.ask_question(
                    question=enhanced_prompt,
                    screenshot_base64=screenshot_base64,
                    stream=True,
                    region_info=region_info if region_info else None,
                    raw_question=question,
                ):
                    full_response += chunk
                    self.overlay.append_response(chunk)

                logger.info(f"⚡ Transmutation complete: {full_response[:100]}…")

            except Exception as api_error:
                logger.warning(f"⚠️ Gemma 4 unavailable: {api_error}. Using fallback response.")
                fallback_response = self._generate_fallback_response(question, screenshot_base64)
                full_response = fallback_response
                self.overlay.set_response(fallback_response)

            # Execute any [ACTION:...] tags the model included
            if full_response:
                clean_text, action_results = parse_and_execute_actions(full_response)
                if action_results:
                    logger.info(f"Actions executed: {action_results}")
                    # Append action feedback to overlay
                    feedback = "\n\n⚡ Actions taken:\n" + "\n".join(f"  • {r}" for r in action_results)
                    self.overlay.append_response(feedback)

            # Speak the response (TTS cleans action tags / markdown itself)
            if self.tts.is_enabled and full_response:
                logger.info("Speaking response...")
                self.tts.speak_async(full_response)

        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.overlay.set_response(error_msg)
            if self.tts.is_enabled:
                self.tts.speak_async("Sorry, something went wrong.")
        
        finally:
            self.acting_indicator.hide_acting()
            # Re-enable input
            self.overlay.enable_input()
    
    def _generate_fallback_response(self, question: str, screenshot_base64: Optional[str]) -> str:
        """
        Generate a fallback response when Gemma 4 is unavailable.
        
        Args:
            question: User's question
            screenshot_base64: Screenshot data (if available)
            
        Returns:
            Fallback response text
        """
        question_lower = question.lower()
        
        # Check for common patterns
        if any(word in question_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello, {USER_NAME}! I'm Edward, the FullCUDA Alchemist! Ollama with Gemma 4 seems to be offline. Make sure Ollama is running to enable my full alchemy powers!"
        
        elif any(word in question_lower for word in ['screen', 'see', 'what', 'show']):
            if screenshot_base64:
                return f"I can see the area around your cursor, {USER_NAME}, but I need Ollama with Gemma 4 running to analyze it with alchemy. Please start Ollama!"
            else:
                return "I don't have a screenshot to analyze. Try pressing Win+Shift+E to capture the area around your cursor first."
        
        elif any(word in question_lower for word in ['move', 'click', 'type', 'open', 'close']):
            return f"I understand you want me to perform an action, {USER_NAME}. However, I need Ollama with Gemma 4 running to execute autonomous actions. Start Ollama at http://localhost:11434."
        
        elif 'help' in question_lower:
            return f"""I'm Edward, the FullCUDA Alchemist! Currently in fallback mode because Ollama is offline.

To enable full alchemy (AI) functionality:
1. Make sure Ollama is running (http://localhost:11434)
2. Verify Gemma 4 model is installed: ollama list
3. Pull if needed: ollama pull gemma4:latest

In the meantime, I can provide basic responses. How can I assist you, {USER_NAME}?"""
        
        else:
            return f"I received your question: '{question}'. However, Ollama is currently offline. Make sure Ollama is running and Gemma 4 is pulled (`ollama pull gemma4:latest`), {USER_NAME}."
    
    def _create_tray_icon(self):
        """Create system tray icon — FMA transmutation circle"""
        image = self._draw_alchemy_circle(64)

        menu = pystray.Menu(
            pystray.MenuItem('Show Edward',    self._show_overlay),
            pystray.MenuItem('Password Vault', self._show_password_vault),
            pystray.MenuItem('Settings',       self._show_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self._quit_app)
        )

        self.tray_icon = pystray.Icon(
            "Edward", image, "Edward — FullCUDA Alchemist", menu
        )

    @staticmethod
    def _draw_alchemy_circle(size: int = 64) -> Image.Image:
        import math
        img  = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        gold  = (218, 165, 32, 255)
        dark  = (13,  13,  13, 255)

        cx = cy = size / 2
        ro = size / 2 - 2          # outer ring
        ri = ro * 0.72             # inner ring
        rh = ro * 0.62             # hexagram points
        rc = ro * 0.18             # center dot
        lw = max(1, size // 32)    # line width

        # Dark background disk
        draw.ellipse([2, 2, size - 2, size - 2], fill=dark)

        # Outer ring
        draw.ellipse([2, 2, size - 2, size - 2], outline=gold, width=lw)

        # Inner ring
        m = size // 2 - int(ri)
        draw.ellipse([m, m, size - m, size - m], outline=gold, width=lw)

        # Center circle
        mc = int(cx - rc), int(cy - rc), int(cx + rc), int(cy + rc)
        draw.ellipse(mc, outline=gold, width=lw)

        # Helper: point on circle
        def pt(deg, r):
            a = math.radians(deg - 90)
            return cx + r * math.cos(a), cy + r * math.sin(a)

        # Hexagram: two overlapping triangles
        for angles in [(0, 120, 240), (60, 180, 300)]:
            tri = [pt(a, rh) for a in angles]
            draw.polygon(tri, outline=gold, fill=None, width=lw)

        # Node dots at hexagram vertices
        rn = max(2, size // 22)
        for angle in range(0, 360, 60):
            px, py = pt(angle, rh)
            draw.ellipse([px - rn, py - rn, px + rn, py + rn], fill=gold)

        # Tick marks (12, like a clock)
        for i in range(12):
            a = math.radians(i * 30 - 90)
            x1, y1 = cx + (ro - 1) * math.cos(a), cy + (ro - 1) * math.sin(a)
            x2, y2 = cx + (ro - 4) * math.cos(a), cy + (ro - 4) * math.sin(a)
            draw.line([x1, y1, x2, y2], fill=gold, width=lw)

        return img
    
    # ── Tray callbacks (run on pystray's background thread → emit signals) ────

    def _show_overlay(self):
        self.tray_bridge.show_overlay.emit()

    def _show_password_vault(self):
        self.tray_bridge.open_vault.emit()

    def _show_settings(self):
        self.tray_bridge.open_settings.emit()

    # ── Thread-safe slots (run on Qt main thread) ─────────────────────────────

    @Slot()
    def _show_overlay_from_tray(self):
        self.overlay.show_overlay()

    @Slot()
    def _show_password_vault_safe(self):
        unlock = PasswordUnlockDialog()
        if unlock.exec() != PasswordUnlockDialog.DialogCode.Accepted:
            return
        vault = unlock.get_vault()
        if vault:
            PasswordManagerDialog(vault).exec()

    @Slot()
    def _show_settings_safe(self):
        SettingsDialog().exec()

    # ── Wake word ─────────────────────────────────────────────────────────────

    def _on_wake_word_raw(self, command: Optional[str]):
        """Called from wake-word thread — emit signal to main thread."""
        self.wake_bridge.detected.emit(command or "")

    @Slot(bool)
    def _on_overlay_visibility(self, visible: bool):
        if visible:
            self.wake_detector.suppress()
        else:
            self.wake_detector.resume()

    @Slot(str)
    def _on_wake_detected_safe(self, command: str):
        """Wake word fired — show overlay, optionally auto-submit command."""
        logger.info(f"Wake word → main thread, command={command!r}")
        # Save the foreground window BEFORE showing the overlay, same as the hotkey path.
        # Without this, active-window captures fall back to GetForegroundWindow() which
        # returns Edward's own panel once it's visible.
        import ctypes as _ct
        self.agent._target_hwnd = _ct.windll.user32.GetForegroundWindow()
        try:
            img_bytes, img_base64 = self.agent.capture_for_mode()
        except Exception:
            img_bytes, img_base64 = b"", ""

        self.overlay.show_overlay(
            screenshot_data=(img_bytes, img_base64) if img_bytes else None
        )

        if command:
            # Full utterance: "Hey Edward, open notepad" → auto-submit
            self.overlay.input_field.setPlainText(command)
            self._on_question_submitted(command)
        else:
            # Just the wake word — auto-listen and auto-submit when done
            self._start_wake_listen()

    def _request_action_confirmation(self, action_request):
        """
        Request user confirmation for a computer action.
        
        Args:
            action_request: ActionRequest object from confirmation_handler
        """
        logger.info(f"Requesting confirmation for: {action_request.description}")
        
        # Create confirmation dialog
        self.confirmation_dialog = ConfirmationDialog()
        self.confirmation_dialog.set_action(
            action_request.description,
            action_request.parameters
        )
        
        # Connect signals
        self.confirmation_dialog.confirmed.connect(
            lambda: self._on_action_confirmed(action_request)
        )
        self.confirmation_dialog.denied.connect(
            lambda: self._on_action_denied(action_request)
        )
        
        # Show dialog
        self.confirmation_dialog.exec()
    
    def _on_action_confirmed(self, action_request):
        """
        Handle user confirming an action.
        
        Args:
            action_request: ActionRequest object
        """
        logger.info(f"Action confirmed: {action_request.description}")
        
        # Execute the action
        result = self._execute_action(action_request)
        
        # Display result to user
        if result.get('success'):
            message = f"✓ {result['message']}"
            logger.info(f"Action succeeded: {message}")
        else:
            message = f"✗ {result['message']}"
            logger.error(f"Action failed: {message}")
        
        # Append result to overlay
        self.overlay.append_response(f"\n\n{message}")
        
        # Speak result if TTS enabled
        if self.tts.is_enabled:
            self.tts.speak_async(message)
    
    def _on_action_denied(self, action_request):
        """
        Handle user denying an action.
        
        Args:
            action_request: ActionRequest object
        """
        logger.info(f"Action denied: {action_request.description}")
        
        message = "Action cancelled by user."
        self.overlay.append_response(f"\n\n{message}")
        
        if self.tts.is_enabled:
            self.tts.speak_async(message)
    
    def _execute_action(self, action_request) -> dict:
        """
        Execute a confirmed computer action.
        
        Args:
            action_request: ActionRequest object
            
        Returns:
            Result dictionary with success status and message
        """
        from confirmation_handler import ActionType
        
        action_type = action_request.action_type
        params = action_request.parameters
        
        try:
            if action_type == ActionType.CREATE_FILE:
                return create_file(
                    params.get('file_path', ''),
                    params.get('content', ''),
                    overwrite=False
                )
            
            elif action_type == ActionType.EDIT_FILE:
                return edit_file(
                    params.get('file_path', ''),
                    params.get('new_content', '')
                )
            
            elif action_type == ActionType.OPEN_FILE or action_type == ActionType.OPEN_APP:
                return open_file_or_app(params.get('path', ''))
            
            else:
                return {
                    'success': False,
                    'message': f"Unknown action type: {action_type}",
                    'error': 'unknown_action'
                }
        
        except Exception as e:
            logger.error(f"Error executing action: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"Error executing action: {str(e)}",
                'error': 'execution_error'
            }

    def _quit_app(self):
        """Quit the application"""
        logger.info("Shutting down Edward...")
        self.agent.stop()
        self.wake_detector.stop()
        self.tts.cleanup()
        if self.tray_icon:
            self.tray_icon.stop()
        self.app.quit()
        self.loop.stop()
    
    def run(self):
        """Start Edward application"""
        logger.info("Starting Edward...")
        
        # Start agent (hotkey listener)
        self.agent.start()

        # Start wake word detector
        self.wake_detector.start()
        
        # Create and run system tray icon
        self._create_tray_icon()
        
        # Run tray icon in separate thread
        import threading
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
        logger.info(f"Edward is running. Press Win+Shift+E to activate, {USER_NAME}.")

        # Allow Ctrl+C to work inside Qt's event loop.
        # Qt's C loop can starve Python signal handling, so we ping Python
        # every 500 ms via a no-op timer to keep the GIL alive.
        from PySide6.QtCore import QTimer as _QTimer
        _sigint_timer = _QTimer()
        _sigint_timer.setInterval(500)
        _sigint_timer.timeout.connect(lambda: None)
        _sigint_timer.start()

        def _handle_sigint(*_):
            logger.info("Ctrl+C — shutting down Edward…")
            self._quit_app()

        signal.signal(signal.SIGINT, _handle_sigint)

        with self.loop:
            try:
                self.loop.run_forever()
            except (KeyboardInterrupt, SystemExit):
                self._quit_app()


def main():
    """Main entry point"""
    try:
        edward = Edward()
        edward.run()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        os._exit(0)   # force-kill any lingering daemon threads


if __name__ == "__main__":
    main()

