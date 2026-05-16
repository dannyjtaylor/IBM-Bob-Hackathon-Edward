"""
Edward Overlay Module
PySide6-based dark overlay panel that slides in from the right
"""

import sys
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QScrollArea
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal as pyqtSignal, QSize
from PySide6.QtGui import QFont, QPalette, QColor, QScreen, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

from config import COLORS, OVERLAY_WIDTH, OVERLAY_ANIMATION_DURATION, OVERLAY_OPACITY
from logger import get_logger
from widgets.listening_indicator import ListeningIndicator

# Setup logging
logger = get_logger(__name__)


def create_microphone_icon(color: str = "#DAA520", size: int = 24) -> QIcon:
    """
    Create a microphone SVG icon.
    
    Args:
        color: Icon color (hex)
        size: Icon size in pixels
        
    Returns:
        QIcon with microphone SVG
    """
    svg_data = f'''<?xml version="1.0" encoding="UTF-8"?>
    <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z"
              fill="{color}" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M19 10V12C19 15.866 15.866 19 12 19C8.13401 19 5 15.866 5 12V10"
              stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M12 19V23M8 23H16"
              stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>'''
    
    # Create QPixmap from SVG
    renderer = QSvgRenderer(svg_data.encode())
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)


class EdwardOverlay(QMainWindow):
    """
    Dark overlay panel that slides in from the right side of the screen.
    Displays user input field and Edward's responses.
    """
    
    # Signal emitted when user submits a question
    question_submitted = pyqtSignal(str)
    
    def __init__(self):
        """Initialize the overlay window"""
        super().__init__()
        
        self.screenshot_data: Optional[tuple[bytes, str]] = None
        self.is_visible = False
        
        self._setup_window()
        self._setup_ui()
        self._setup_animations()
        
        logger.info("Edward Overlay initialized")
    
    def _setup_window(self):
        """Configure the main window properties"""
        # Remove window frame and make it stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        
        # Allow window to accept focus for typing
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        
        # Set window opacity
        self.setWindowOpacity(OVERLAY_OPACITY)
        
        # Get screen geometry
        screen: QScreen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Position window off-screen to the right initially
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        
        self.setGeometry(
            self.screen_width,  # Start off-screen
            0,
            OVERLAY_WIDTH,
            self.screen_height
        )
        
        # Set window title
        self.setWindowTitle("Edward")
    
    def _setup_ui(self):
        """Create and configure UI elements"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        central_widget.setLayout(layout)
        
        # Apply dark theme
        self._apply_dark_theme(central_widget)
        
        # Title label
        title_label = QLabel("EDWARD")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['gold']}; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet(f"color: {COLORS['silver']}; padding: 5px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Listening indicator (hidden until mic is active)
        self.listening_indicator = ListeningIndicator(central_widget)
        self.listening_indicator.hide()
        layout.addWidget(self.listening_indicator, alignment=Qt.AlignmentFlag.AlignCenter)

        # Response display area (scrollable)
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setFont(QFont("Segoe UI", 11))
        self.response_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['silver']};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        self.response_area.setPlaceholderText("Edward's response will appear here...")
        layout.addWidget(self.response_area, stretch=3)
        
        # Input field
        self.input_field = QTextEdit()
        self.input_field.setFont(QFont("Segoe UI", 11))
        self.input_field.setMaximumHeight(100)
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['gold']};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        self.input_field.setPlaceholderText("Ask Edward anything or use microphone...")
        layout.addWidget(self.input_field, stretch=1)
        
        # Button row (microphone + ask)
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        
        # Microphone button with SVG icon
        self.mic_button = QPushButton(" Listen")
        mic_icon = create_microphone_icon(COLORS['background'], 20)
        self.mic_button.setIcon(mic_icon)
        self.mic_button.setIconSize(QSize(20, 20))
        self.mic_button.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.mic_button.setMinimumHeight(50)
        self.mic_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['gold']};
                color: {COLORS['background']};
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #E5B52E;
            }}
            QPushButton:pressed {{
                background-color: #C09020;
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """)
        self.mic_button.clicked.connect(self._on_mic_clicked)
        button_row.addWidget(self.mic_button, stretch=1)
        
        # Ask button
        self.ask_button = QPushButton("Ask Edward")
        self.ask_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.ask_button.setMinimumHeight(50)
        self.ask_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['red']};
                color: {COLORS['text']};
                border: none;
                border-radius: 5px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #CC2222;
            }}
            QPushButton:pressed {{
                background-color: #992222;
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """)
        self.ask_button.clicked.connect(self._on_ask_clicked)
        button_row.addWidget(self.ask_button, stretch=2)
        
        layout.addLayout(button_row)
        
        # Close button
        close_button = QPushButton("Close (Esc)")
        close_button.setFont(QFont("Segoe UI", 10))
        close_button.setMinimumHeight(40)
        close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['background']};
                color: {COLORS['silver']};
                border: 1px solid {COLORS['silver']};
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: #2A2A2A;
            }}
        """)
        close_button.clicked.connect(self.hide_overlay)
        layout.addWidget(close_button)
    
    def _apply_dark_theme(self, widget: QWidget):
        """Apply dark color palette to widget"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['panel']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['background']))
        palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text']))
        widget.setPalette(palette)
        widget.setAutoFillBackground(True)
    
    def _setup_animations(self):
        """Setup slide-in/slide-out animations"""
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(OVERLAY_ANIMATION_DURATION)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def show_overlay(self, screenshot_data: Optional[tuple[bytes, str]] = None):
        """
        Show the overlay with slide-in animation from the right.
        
        Args:
            screenshot_data: Tuple of (image_bytes, base64_string) from screenshot
        """
        if self.is_visible:
            logger.info("Overlay already visible, ignoring")
            return
        
        # Store screenshot data
        self.screenshot_data = screenshot_data
        
        # Animate slide-in from right
        start_rect = QRect(
            self.screen_width,
            0,
            OVERLAY_WIDTH,
            self.screen_height
        )
        end_rect = QRect(
            self.screen_width - OVERLAY_WIDTH,
            0,
            OVERLAY_WIDTH,
            self.screen_height
        )
        
        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(end_rect)
        
        # Show window and raise it to top
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Start animation
        self.slide_animation.start()
        
        # Focus on input field
        self.input_field.setFocus()
        
        self.is_visible = True
        logger.info(f"Overlay shown at position: {end_rect}")
    
    def hide_overlay(self):
        """Hide the overlay with slide-out animation to the right"""
        if not self.is_visible:
            return
        
        # Animate slide-out to right
        start_rect = self.geometry()
        end_rect = QRect(
            self.screen_width,
            0,
            OVERLAY_WIDTH,
            self.screen_height
        )
        
        self.slide_animation.setStartValue(start_rect)
        self.slide_animation.setEndValue(end_rect)
        self.slide_animation.finished.connect(self._on_hide_finished)
        self.slide_animation.start()
        
        self.is_visible = False
        logger.info("Overlay hidden")
    
    def _on_hide_finished(self):
        """Called when hide animation finishes"""
        self.hide()
        self.slide_animation.finished.disconnect(self._on_hide_finished)
        
        # Clear fields
        self.input_field.clear()
        self.response_area.clear()
        self.screenshot_data = None
    
    def show_listening(self):
        """Show listening indicator when mic is active"""
        self.listening_indicator.show()
        self.listening_indicator.start_animation()

    def hide_listening(self):
        """Hide listening indicator (fades out then hides)"""
        self.listening_indicator.stop_animation()

    def _on_mic_clicked(self):
        """Handle microphone button click"""
        logger.info("Microphone button clicked")

        # Disable buttons while listening
        self.mic_button.setEnabled(False)
        self.ask_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.set_status("🎤 Listening... Speak now!")
        self.show_listening()
        
        # Emit signal to start listening (will be handled by main.py)
        # For now, just re-enable after a moment
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._start_listening)
    
    def _start_listening(self):
        """Start listening for speech (called from main thread)"""
        # This will be connected to STT in main.py
        pass
    
    def _on_ask_clicked(self):
        """Handle Ask Edward button click"""
        question = self.input_field.toPlainText().strip()
        
        if not question:
            self.set_status("Please enter a question", error=True)
            return
        
        # Disable input while processing
        self.input_field.setEnabled(False)
        self.ask_button.setEnabled(False)
        self.mic_button.setEnabled(False)
        self.set_status("Processing...")
        
        # Emit signal with question
        self.question_submitted.emit(question)
        
        logger.info(f"Question submitted: {question[:50]}...")
    
    def set_status(self, message: str, error: bool = False):
        """
        Update status label.
        
        Args:
            message: Status message to display
            error: If True, display in red
        """
        color = COLORS['red'] if error else COLORS['silver']
        self.status_label.setStyleSheet(f"color: {color}; padding: 5px;")
        self.status_label.setText(message)
    
    def append_response(self, text: str):
        """
        Append text to response area (for streaming responses).
        
        Args:
            text: Text to append
        """
        self.response_area.insertPlainText(text)
        # Auto-scroll to bottom
        scrollbar = self.response_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def set_response(self, text: str):
        """
        Set complete response text.
        
        Args:
            text: Full response text
        """
        self.response_area.setPlainText(text)
    
    def enable_input(self):
        """Re-enable input field and buttons after processing"""
        self.hide_listening()
        self.input_field.setEnabled(True)
        self.ask_button.setEnabled(True)
        self.mic_button.setEnabled(True)
        self.input_field.clear()
        self.input_field.setFocus()
        self.set_status("Ready")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Close on Escape
        if event.key() == Qt.Key.Key_Escape:
            self.hide_overlay()
        # Submit on Enter (with or without Ctrl)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Only submit if input field has focus and has content
            if self.input_field.hasFocus() and self.input_field.toPlainText().strip():
                self._on_ask_clicked()
            event.accept()
        else:
            super().keyPressEvent(event)


# Example usage
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    overlay = EdwardOverlay()
    
    # Test callback
    def on_question(question: str):
        print(f"Question received: {question}")
        overlay.set_response(f"You asked: {question}")
        overlay.enable_input()
    
    overlay.question_submitted.connect(on_question)
    overlay.show_overlay()
    
    sys.exit(app.exec())

# Made with Bob
