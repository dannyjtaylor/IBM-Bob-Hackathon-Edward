"""
Edward - Local Windows Desktop AI Assistant
Main entry point that coordinates all components
"""

import sys
import warnings
import os

# Suppress NumPy and other startup warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

from pathlib import Path
from typing import Optional
import asyncio
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, Signal as pyqtSignal, QObject, Slot
import pystray
from PIL import Image, ImageDraw

from agent import EdwardAgent
from overlay import EdwardOverlay
from tts import get_tts
from widgets.acting_indicator import ActingIndicator
from stt import get_stt
from api_client import get_api_client
from context_enhancer import get_context_enhancer
from ui import PasswordUnlockDialog, PasswordManagerDialog
from config import USER_NAME, COLORS
from logger import setup_logger

# Setup colored logging
logger = setup_logger(__name__, log_file='logs/edward.log')


class HotkeySignalBridge(QObject):
    """Bridge to safely emit signals from background threads to Qt main thread"""
    triggered = pyqtSignal(bytes, str)


class SpeechSignalBridge(QObject):
    """Bridge to safely emit speech recognition results to Qt main thread"""
    speech_result = pyqtSignal(object)  # Will emit Optional[str]


class Edward:
    """
    Main Edward application class.
    Coordinates agent, overlay, TTS, and system tray.
    """
    
    def __init__(self):
        """Initialize Edward application"""
        logger.info("Initializing Edward...")
        
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
        
        # Initialize components
        self.overlay = EdwardOverlay()
        self.acting_indicator = ActingIndicator()
        self.agent = EdwardAgent(on_trigger_callback=self._on_hotkey_triggered)
        self.tts = get_tts()
        self.stt = get_stt()
        self.api_client = get_api_client()
        self.context_enhancer = get_context_enhancer()
        
        # Connect signals
        self.overlay.question_submitted.connect(self._on_question_submitted)
        self.hotkey_bridge.triggered.connect(self._show_overlay_safe)
        self.overlay.mic_button.clicked.connect(self._on_mic_button_clicked)
        self.speech_bridge.speech_result.connect(self._on_speech_result_safe)
        
        # System tray icon
        self.tray_icon = None
        
        logger.info("Edward initialized successfully")
    
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
        """
        Called when microphone button is clicked.
        Starts listening for speech input.
        """
        logger.info("Starting speech recognition...")
        
        def on_speech_result(text: Optional[str]):
            """Callback when speech recognition completes (runs in background thread)"""
            # Emit signal to safely update UI in main thread
            self.speech_bridge.speech_result.emit(text)
        
        # Start listening asynchronously
        self.stt.listen_once_async(on_speech_result, timeout=5, phrase_time_limit=15)
    
    @Slot(object)
    def _on_speech_result_safe(self, text: Optional[str]):
        """
        Handle speech recognition result safely in main Qt thread.
        
        Args:
            text: Recognized speech text or None if failed
        """
        if text:
            logger.info(f"Speech recognized: {text}")
            self.overlay.input_field.setPlainText(text)
            self.overlay.set_status("Speech recognized! Click 'Ask Edward' to submit.")
        else:
            logger.warning("No speech detected")
            self.overlay.set_status("No speech detected. Try again.", error=True)
        
        # Re-enable buttons
        self.overlay.enable_input()
    
    def _on_question_submitted(self, question: str):
        """
        Called when user submits a question.
        Sends to IBM Bob API and handles response.
        """
        logger.info(f"Processing question: {question[:50]}...")
        
        # Get screenshot data if available
        screenshot_base64 = None
        if self.overlay.screenshot_data:
            _, screenshot_base64 = self.overlay.screenshot_data
            logger.info("Including screenshot with question")
        
        # Call API asynchronously
        asyncio.create_task(self._process_question_async(question, screenshot_base64))
    
    async def _process_question_async(self, question: str, screenshot_base64: Optional[str]):
        """
        Process question with IBM Bob API asynchronously.
        
        Args:
            question: User's question
            screenshot_base64: Base64-encoded screenshot (optional)
        """
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
            
            # Try to connect to Bob API
            full_response = ""
            try:
                async for chunk in self.api_client.ask_question(
                    question=enhanced_prompt,  # Use enhanced prompt instead of raw question
                    screenshot_base64=screenshot_base64,
                    stream=True
                ):
                    full_response += chunk
                    self.overlay.append_response(chunk)
                
                logger.info(f"Received response from Bob API: {full_response[:100]}...")
                
            except Exception as api_error:
                # Fallback response when Bob API is not available
                logger.warning(f"Bob API unavailable: {api_error}. Using fallback response.")
                
                fallback_response = self._generate_fallback_response(question, screenshot_base64)
                full_response = fallback_response
                self.overlay.set_response(fallback_response)
            
            # Speak response if TTS enabled
            if self.tts.is_enabled and full_response:
                logger.info("Speaking response...")
                self.tts.speak_async(full_response, stream_audio=True)
            
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.overlay.set_response(error_msg)
        
        finally:
            self.acting_indicator.hide_acting()
            # Re-enable input
            self.overlay.enable_input()
    
    def _generate_fallback_response(self, question: str, screenshot_base64: Optional[str]) -> str:
        """
        Generate a fallback response when Bob API is unavailable.
        
        Args:
            question: User's question
            screenshot_base64: Screenshot data (if available)
            
        Returns:
            Fallback response text
        """
        question_lower = question.lower()
        
        # Check for common patterns
        if any(word in question_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello, {USER_NAME}! I'm Edward, your AI assistant. The Bob API server is currently offline, but I'm here to help with basic responses. To enable full functionality, please start the Bob API server."
        
        elif any(word in question_lower for word in ['screen', 'see', 'what', 'show']):
            if screenshot_base64:
                return f"I can see your screen, {USER_NAME}, but I need the Bob API server to analyze it properly. The server appears to be offline. Please start it to enable vision capabilities."
            else:
                return "I don't have a screenshot to analyze. Try pressing Win+Shift+E to capture your screen first."
        
        elif any(word in question_lower for word in ['move', 'click', 'type', 'open', 'close']):
            return f"I understand you want me to perform an action, {USER_NAME}. However, I need the Bob API server running to execute autonomous actions. Please start the server at http://localhost:6700."
        
        elif 'help' in question_lower:
            return f"""I'm Edward, your AI assistant. Currently running in fallback mode because the Bob API server is offline.

To enable full functionality:
1. Start the Bob API server (should run on http://localhost:6700)
2. Make sure the server is configured in your .env file

In the meantime, I can provide basic responses. How can I assist you, {USER_NAME}?"""
        
        else:
            return f"I received your question: '{question}'. However, the Bob API server is currently offline, so I can't provide a detailed response. Please start the Bob API server to enable full AI capabilities, {USER_NAME}."
    
    def _create_tray_icon(self):
        """Create system tray icon"""
        # Create a simple icon
        width = 64
        height = 64
        color1 = COLORS['gold']
        color2 = COLORS['red']
        
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            (width // 4, height // 4, width * 3 // 4, height * 3 // 4),
            fill=color2
        )
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem('Show Edward', self._show_overlay),
            pystray.MenuItem('Password Vault', self._show_password_vault),
            pystray.MenuItem('Settings', self._show_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Exit', self._quit_app)
        )
        
        # Create icon
        self.tray_icon = pystray.Icon(
            "Edward",
            image,
            "Edward - AI Assistant",
            menu
        )
    
    def _show_overlay(self):
        """Show overlay from tray menu"""
        self.overlay.show_overlay()
    
    def _show_password_vault(self):
        """Open password vault — prompt for master password then show manager."""
        unlock = PasswordUnlockDialog()
        if unlock.exec() != PasswordUnlockDialog.DialogCode.Accepted:
            return
        vault = unlock.get_vault()
        if vault:
            PasswordManagerDialog(vault).exec()

    def _show_settings(self):
        """Show settings dialog (placeholder)"""
        logger.info("Settings clicked (not implemented yet)")
    
    def _quit_app(self):
        """Quit the application"""
        logger.info("Shutting down Edward...")
        
        # Stop components
        self.agent.stop()
        self.tts.cleanup()
        
        # Stop tray icon
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Quit Qt application
        self.app.quit()
    
    def run(self):
        """Start Edward application"""
        logger.info("Starting Edward...")
        
        # Start agent (hotkey listener)
        self.agent.start()
        
        # Create and run system tray icon
        self._create_tray_icon()
        
        # Run tray icon in separate thread
        import threading
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
        logger.info(f"Edward is running. Press Win+Shift+E to activate, {USER_NAME}.")
        
        # Run Qt event loop with asyncio support
        with self.loop:
            sys.exit(self.loop.run_forever())


def main():
    """Main entry point"""
    try:
        edward = Edward()
        edward.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
