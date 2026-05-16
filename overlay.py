"""
Edward Overlay — FullMetal Alchemist Edition
PySide6 panel that slides in from the right.
Features: animated alchemy circle, screenshot-mode selector, live thumbnail,
real-time STT display, blueprint response area, glow effects.
"""

import sys
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QEvent, QObject, QRect, QSize, QTimer,
    Signal as pyqtSignal, Slot,
)
from PySide6.QtGui import (
    QColor, QFont, QFontDatabase, QPainter, QPen, QPixmap,
    QScreen, QIcon, QLinearGradient, QBrush,
)
from PySide6.QtSvg import QSvgRenderer

from config import COLORS, OVERLAY_WIDTH, OVERLAY_ANIMATION_DURATION, OVERLAY_OPACITY, ScreenshotMode
from logger import get_logger
from widgets.alchemy_circle import AlchemyCircle
from widgets.listening_indicator import ListeningIndicator

logger = get_logger(__name__)

# ── Colour helpers ────────────────────────────────────────────────────────────
GOLD   = COLORS['gold']
RED    = COLORS['red']
SILVER = COLORS['silver']
BG     = COLORS['background']
PANEL  = COLORS['panel']
TEXT   = COLORS['text']
BLUE   = COLORS['blueprint']

# ── Icon helpers ──────────────────────────────────────────────────────────────

def _svg_icon(svg: str, size: int = 20) -> QIcon:
    renderer = QSvgRenderer(svg.encode())
    pixmap   = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter  = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def _mic_icon(color: str = GOLD, size: int = 20) -> QIcon:
    svg = f'''<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none"
               xmlns="http://www.w3.org/2000/svg">
      <path d="M12 1C10.34 1 9 2.34 9 4V12C9 13.66 10.34 15 12 15C13.66 15 15 13.66 15 12V4C15 2.34 13.66 1 12 1Z"
            fill="{color}" stroke="{color}" stroke-width="1.2"/>
      <path d="M19 10V12C19 15.866 15.866 19 12 19C8.134 19 5 15.866 5 12V10"
            stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M12 19V23M8 23H16" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
    </svg>'''
    return _svg_icon(svg, size)


# ── Stylesheet constants ──────────────────────────────────────────────────────

_BUTTON_BASE = f"""
    QPushButton {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #1C1000, stop:0.45 #2A1A00, stop:1 #141414);
        color: {GOLD};
        border: 1px solid {GOLD};
        border-left: 3px solid {GOLD};
        border-radius: 0px;
        padding: 8px 14px;
        font-weight: bold;
        text-align: left;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #3A2400, stop:1 #1E1400);
        border-left: 3px solid #FFD700;
        color: #FFD700;
    }}
    QPushButton:pressed {{
        background: #0D0800;
        border-left: 3px solid {RED};
        color: {RED};
    }}
    QPushButton:disabled {{
        background: #111111;
        color: #444444;
        border-color: #333333;
    }}
"""

_TRANSMUTE_BUTTON = f"""
    QPushButton {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #5A0000, stop:0.5 {RED}, stop:1 #8B0000);
        color: {TEXT};
        border: 1px solid #CC3333;
        border-radius: 0px;
        padding: 10px 18px;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 1px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #7A0000, stop:0.5 #CC2222, stop:1 #AA1111);
        border: 1px solid #FF4444;
    }}
    QPushButton:pressed {{
        background: #3A0000;
    }}
    QPushButton:disabled {{
        background: #1A1A1A;
        color: #444444;
        border-color: #333333;
    }}
"""

_RESPONSE_AREA = f"""
    QTextEdit {{
        background-color: {BLUE};
        color: {GOLD};
        border: 1px solid #1E3050;
        border-top: 2px solid #2A4070;
        border-radius: 0px;
        padding: 10px;
        selection-background-color: {RED};
        selection-color: {TEXT};
        font-size: 11px;
        line-height: 1.5;
    }}
    QScrollBar:vertical {{
        background: #0D0D0D;
        width: 8px;
    }}
    QScrollBar::handle:vertical {{
        background: {GOLD};
        border-radius: 4px;
        min-height: 20px;
    }}
"""

_INPUT_FIELD = f"""
    QTextEdit {{
        background-color: {BG};
        color: {TEXT};
        border: 2px solid {GOLD};
        border-radius: 0px;
        padding: 8px;
        font-size: 11px;
    }}
    QTextEdit:focus {{
        border: 2px solid #FFD700;
    }}
"""

_CLOSE_BUTTON = f"""
    QPushButton {{
        background: transparent;
        color: {SILVER};
        border: 1px solid #333333;
        border-radius: 0px;
        padding: 5px;
        font-size: 10px;
    }}
    QPushButton:hover {{
        background: #1A1A1A;
        color: {TEXT};
        border-color: {SILVER};
    }}
"""

_MODE_CHECKED = f"""
    QPushButton {{
        background: {GOLD};
        color: #0D0D0D;
        border: 1px solid {GOLD};
        border-radius: 0px;
        font-weight: bold;
        font-size: 10px;
        padding: 4px 2px;
    }}
"""
_MODE_UNCHECKED = f"""
    QPushButton {{
        background: #1A1200;
        color: {GOLD};
        border: 1px solid #554000;
        border-radius: 0px;
        font-size: 10px;
        padding: 4px 2px;
    }}
    QPushButton:hover {{
        background: #2A2000;
        border-color: {GOLD};
    }}
"""


def _glow(widget, color: str = GOLD, radius: int = 12):
    fx = QGraphicsDropShadowEffect()
    fx.setColor(QColor(color))
    fx.setBlurRadius(radius)
    fx.setOffset(0, 0)
    widget.setGraphicsEffect(fx)


# ── Separator ─────────────────────────────────────────────────────────────────

class _GoldLine(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFixedHeight(2)
        self.setStyleSheet(f"background: {GOLD}; border: none;")


# ── Enter-key filter (QTextEdit eats Return; this intercepts it) ──────────────

class _SubmitOnEnter(QObject):
    """
    Installed on the input QTextEdit.
    Plain Enter → submit.  Shift+Enter → newline (pass through).
    """
    def __init__(self, submit_fn, parent=None):
        super().__init__(parent)
        self._submit = submit_fn

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    self._submit()
                    return True   # consume — don't insert newline
        return False


# ── Main overlay ──────────────────────────────────────────────────────────────

class EdwardOverlay(QMainWindow):
    """
    Dark slide-in panel: animated alchemy circle, screenshot mode selector,
    thumbnail preview, blueprint response area, glow buttons.
    """

    question_submitted      = pyqtSignal(str)
    screenshot_mode_changed = pyqtSignal(object)   # emits ScreenshotMode
    backend_changed         = pyqtSignal(str)      # emits backend name string
    visibility_changed      = pyqtSignal(bool)     # True=shown, False=hidden

    def __init__(self):
        super().__init__()
        self.screenshot_data: Optional[tuple[bytes, str]] = None
        self.is_visible = False
        self._current_mode    = ScreenshotMode.CURSOR_REGION
        self._current_backend = "gemini"

        # Set by main.py: lambda → (img_bytes, img_base64)
        self._refresh_capture_fn = None

        self._setup_window()
        self._setup_ui()
        self._setup_animations()

        # Timer exists but only starts when manually triggered (Ctrl+R)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(4000)
        self._refresh_timer.timeout.connect(self._periodic_refresh)

        # Start alchemy circle
        self.alchemy_circle.start()

        logger.info("EdwardOverlay initialised — FMA edition")

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setWindowOpacity(OVERLAY_OPACITY)

        screen: QScreen = QApplication.primaryScreen()
        geo = screen.geometry()
        self.screen_width  = geo.width()
        self.screen_height = geo.height()

        self.setGeometry(self.screen_width, 0, OVERLAY_WIDTH, self.screen_height)
        self.setWindowTitle("Edward")

        # Overall dark stylesheet
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BG};
                color: {TEXT};
                font-family: 'Segoe UI', 'Consolas', monospace;
            }}
        """)

    # ── UI construction ───────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 10)
        layout.setSpacing(10)

        layout.addLayout(self._build_header())
        layout.addWidget(_GoldLine())
        layout.addLayout(self._build_mode_selector())
        layout.addLayout(self._build_backend_selector())
        layout.addWidget(self._build_thumbnail())
        layout.addWidget(self._build_response_area(), stretch=3)
        layout.addWidget(self._build_stt_display())
        layout.addWidget(_GoldLine())
        layout.addWidget(self._build_input_field(), stretch=1)
        layout.addLayout(self._build_buttons())
        layout.addWidget(self._build_close_button())

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        self.alchemy_circle = AlchemyCircle(54)
        row.addWidget(self.alchemy_circle)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        name = QLabel("EDWARD")
        name.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {GOLD}; letter-spacing: 2px;")
        _glow(name, GOLD, 18)
        title_col.addWidget(name)

        sub = QLabel("The FullCUDA Alchemist")
        sub.setFont(QFont("Segoe UI", 8))
        sub.setStyleSheet(f"color: {SILVER}; letter-spacing: 1px;")
        title_col.addWidget(sub)

        row.addLayout(title_col)
        row.addStretch()
        return row

    # ── Screenshot mode selector ──────────────────────────────────────────────

    def _build_mode_selector(self) -> QHBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(4)

        label = QLabel("EDWARD'S VIEW")
        label.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {SILVER}; letter-spacing: 2px;")
        col.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(4)

        modes = [
            (ScreenshotMode.CURSOR_REGION, "⊙ CURSOR\nFAST",   "Fast — focused region around mouse"),
            (ScreenshotMode.ACTIVE_WINDOW, "▣ WINDOW\nMED",    "Medium — current foreground window"),
            (ScreenshotMode.FULL_SCREEN,   "⬜ SCREEN\nSLOW",  "Slow — all monitors"),
        ]

        self._mode_btns: dict[ScreenshotMode, QPushButton] = {}
        for mode, label_text, tip in modes:
            btn = QPushButton(label_text)
            btn.setToolTip(tip)
            btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            btn.setMinimumHeight(40)
            btn.pressed.connect(lambda m=mode: self._select_mode(m))
            self._mode_btns[mode] = btn
            row.addWidget(btn)

        self._select_mode(ScreenshotMode.CURSOR_REGION, emit=False)
        col.addLayout(row)

        wrapper = QVBoxLayout()
        wrapper.addLayout(col)
        return wrapper

    def _select_mode(self, mode: ScreenshotMode, emit: bool = True):
        self._current_mode = mode
        for m, btn in self._mode_btns.items():
            btn.setChecked(m == mode)
            btn.setStyleSheet(_MODE_CHECKED if m == mode else _MODE_UNCHECKED)
        if emit:
            logger.info(f"Screenshot mode → {mode.value}")
            self.screenshot_mode_changed.emit(mode)

    # ── AI backend selector ───────────────────────────────────────────────────

    _BACKEND_CHECKED = f"""
        QPushButton {{
            background: {RED};
            color: {TEXT};
            border: 1px solid #CC3333;
            border-radius: 0px;
            font-weight: bold;
            font-size: 9px;
            padding: 3px 2px;
        }}
    """
    _BACKEND_UNCHECKED = f"""
        QPushButton {{
            background: #120000;
            color: #884444;
            border: 1px solid #330000;
            border-radius: 0px;
            font-size: 9px;
            padding: 3px 2px;
        }}
        QPushButton:hover {{
            background: #200000;
            color: {RED};
            border-color: {RED};
        }}
    """

    def _build_backend_selector(self) -> QHBoxLayout:
        from gemma_client import BACKEND_LABELS
        col = QVBoxLayout()
        col.setSpacing(4)

        label = QLabel("AI ENGINE")
        label.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {SILVER}; letter-spacing: 2px;")
        col.addWidget(label)

        row = QHBoxLayout()
        row.setSpacing(4)

        self._backend_btns: dict[str, QPushButton] = {}
        for key, display in BACKEND_LABELS.items():
            btn = QPushButton(display)
            btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            btn.setMinimumHeight(30)
            btn.pressed.connect(lambda k=key: self._select_backend(k))
            self._backend_btns[key] = btn
            row.addWidget(btn)

        self._select_backend("gemini", emit=False)
        col.addLayout(row)
        return col

    def _select_backend(self, name: str, emit: bool = True):
        self._current_backend = name
        for k, btn in self._backend_btns.items():
            btn.setStyleSheet(
                self._BACKEND_CHECKED if k == name else self._BACKEND_UNCHECKED
            )
        if emit:
            logger.info(f"AI backend → {name}")
            self.backend_changed.emit(name)

    # ── Screenshot thumbnail ──────────────────────────────────────────────────

    def _build_thumbnail(self) -> QWidget:
        frame = QWidget()
        frame.setFixedHeight(110)
        frame.setStyleSheet(f"background: #0A0A0A; border: 1px solid #2A2A00;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        hdr = QLabel("EDWARD'S CURRENT VIEW")
        hdr.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        hdr.setStyleSheet(f"color: {SILVER}; letter-spacing: 1px; border: none;")
        layout.addWidget(hdr)

        self.thumbnail_label = QLabel("No screenshot captured yet")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet(
            f"color: #444444; font-size: 9px; border: 1px dashed #2A2A2A;"
        )
        self.thumbnail_label.setScaledContents(False)
        layout.addWidget(self.thumbnail_label, stretch=1)

        self.thumb_frame = frame
        return frame

    def _update_thumbnail(self, img_bytes: bytes):
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)
        available_w = self.thumb_frame.width() - 16
        available_h = 80
        scaled = pixmap.scaled(
            available_w, available_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.thumbnail_label.setPixmap(scaled)
        self.thumbnail_label.setStyleSheet("border: 1px solid #554000;")

    # ── Response area ─────────────────────────────────────────────────────────

    def _build_response_area(self) -> QTextEdit:
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setFont(QFont("Consolas", 10))
        self.response_area.setStyleSheet(_RESPONSE_AREA)
        self.response_area.setPlaceholderText(
            "Edward's transmutation will appear here...\n\n"
            "「The world isn't perfect. But it's there for us, doing the best it can.」"
        )
        return self.response_area

    # ── Live STT display ──────────────────────────────────────────────────────

    def _build_stt_display(self) -> QLabel:
        self.stt_label = QLabel("")
        self.stt_label.setFont(QFont("Segoe UI", 9, italic=True))
        self.stt_label.setStyleSheet(f"color: {SILVER}; padding: 2px 4px;")
        self.stt_label.setWordWrap(True)
        self.stt_label.hide()
        return self.stt_label

    def update_stt_text(self, text: str):
        """Show partial speech recognition text as user speaks."""
        if text:
            self.stt_label.setText(f"🎤  {text}…")
            self.stt_label.show()
        else:
            self.stt_label.hide()

    # ── Input field ───────────────────────────────────────────────────────────

    def _build_input_field(self) -> QTextEdit:
        self.input_field = QTextEdit()
        self.input_field.setFont(QFont("Segoe UI", 11))
        self.input_field.setMaximumHeight(90)
        self.input_field.setStyleSheet(_INPUT_FIELD)
        self.input_field.setPlaceholderText("Ask Edward anything…  (Enter to transmute  |  Shift+Enter for newline)")

        # Event filter so Enter submits instead of inserting a newline
        self._enter_filter = _SubmitOnEnter(self._on_ask_clicked, self.input_field)
        self.input_field.installEventFilter(self._enter_filter)

        return self.input_field

    # ── Buttons ───────────────────────────────────────────────────────────────

    def _build_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        # Mic / listen
        self.mic_button = QPushButton(" LISTEN")
        self.mic_button.setIcon(_mic_icon(BG, 18))
        self.mic_button.setIconSize(QSize(18, 18))
        self.mic_button.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.mic_button.setMinimumHeight(48)
        self.mic_button.setStyleSheet(_BUTTON_BASE)
        _glow(self.mic_button, GOLD, 10)
        self.mic_button.clicked.connect(self._on_mic_clicked)
        row.addWidget(self.mic_button, stretch=1)

        # Transmute / ask
        self.ask_button = QPushButton("⚡  TRANSMUTE")
        self.ask_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.ask_button.setMinimumHeight(48)
        self.ask_button.setStyleSheet(_TRANSMUTE_BUTTON)
        _glow(self.ask_button, RED, 14)
        self.ask_button.clicked.connect(self._on_ask_clicked)
        row.addWidget(self.ask_button, stretch=2)

        # Listening indicator (embedded, hidden until active)
        self.listening_indicator = ListeningIndicator()
        self.listening_indicator.setFixedSize(36, 36)
        self.listening_indicator.hide()
        row.addWidget(self.listening_indicator)

        return row

    def _build_close_button(self) -> QPushButton:
        btn = QPushButton("CLOSE  [ Esc ]")
        btn.setFont(QFont("Segoe UI", 9))
        btn.setMinimumHeight(32)
        btn.setStyleSheet(_CLOSE_BUTTON)
        btn.clicked.connect(self.hide_overlay)
        return btn

    # ── Status ────────────────────────────────────────────────────────────────

    def set_status(self, message: str, error: bool = False):
        """Update the response area placeholder / status line."""
        # We repurpose the stt_label for non-speech status messages too
        color = RED if error else SILVER
        self.stt_label.setStyleSheet(f"color: {color}; padding: 2px 4px;")
        self.stt_label.setText(message)
        self.stt_label.show()

    # ── Screenshot data ───────────────────────────────────────────────────────

    def update_screenshot(self, img_bytes: bytes, img_base64: str):
        self.screenshot_data = (img_bytes, img_base64)
        self._update_thumbnail(img_bytes)

    # ── Overlay show / hide ───────────────────────────────────────────────────

    def show_overlay(self, screenshot_data: Optional[tuple[bytes, str]] = None):
        if self.is_visible:
            return

        if screenshot_data:
            img_bytes, img_base64 = screenshot_data
            self.screenshot_data = screenshot_data
            self._update_thumbnail(img_bytes)

        # Transmutation animation — circle speeds up on show
        self.alchemy_circle.set_active(True)
        QTimer.singleShot(600, lambda: self.alchemy_circle.set_active(False))

        start = QRect(self.screen_width, 0, OVERLAY_WIDTH, self.screen_height)
        end   = QRect(self.screen_width - OVERLAY_WIDTH, 0, OVERLAY_WIDTH, self.screen_height)
        self.slide_animation.setStartValue(start)
        self.slide_animation.setEndValue(end)

        self.show()
        self.raise_()
        self.activateWindow()
        self.slide_animation.start()
        self.input_field.setFocus()
        self.is_visible = True
        self.visibility_changed.emit(True)
        logger.info("Overlay shown")

    def hide_overlay(self):
        if not self.is_visible:
            return
        start = self.geometry()
        end   = QRect(self.screen_width, 0, OVERLAY_WIDTH, self.screen_height)
        self.slide_animation.setStartValue(start)
        self.slide_animation.setEndValue(end)
        self.slide_animation.finished.connect(self._on_hide_finished)
        self.slide_animation.start()
        self.is_visible = False
        self.visibility_changed.emit(False)
        logger.info("Overlay hidden")

    def _on_hide_finished(self):
        self._refresh_timer.stop()
        self.hide()
        self.slide_animation.finished.disconnect(self._on_hide_finished)
        self.input_field.clear()
        self.response_area.clear()
        self.stt_label.hide()
        self.screenshot_data = None

    def _periodic_refresh(self):
        """Recapture a fresh screenshot every few seconds while overlay is open."""
        if self._refresh_capture_fn is None:
            return
        try:
            img_bytes, img_base64 = self._refresh_capture_fn()
            self.update_screenshot(img_bytes, img_base64)
            logger.debug("Periodic screenshot refresh")
        except Exception as e:
            logger.warning(f"Periodic refresh failed: {e}")

    # ── Animations ────────────────────────────────────────────────────────────

    def _setup_animations(self):
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(OVERLAY_ANIMATION_DURATION)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    # ── Listening state ───────────────────────────────────────────────────────

    def show_listening(self):
        self.listening_indicator.show()
        self.listening_indicator.start_animation()
        self.alchemy_circle.set_active(True)

    def hide_listening(self):
        self.listening_indicator.stop_animation()
        self.alchemy_circle.set_active(False)

    # ── Response helpers ──────────────────────────────────────────────────────

    def append_response(self, text: str):
        self.response_area.insertPlainText(text)
        sb = self.response_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_response(self, text: str):
        self.response_area.setPlainText(text)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_mic_clicked(self):
        self.mic_button.setEnabled(False)
        self.ask_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.set_status("🎤  Listening… speak now")
        self.show_listening()
        QTimer.singleShot(100, self._start_listening)

    def _start_listening(self):
        pass  # wired up in main.py via mic_button.clicked

    def _on_ask_clicked(self):
        question = self.input_field.toPlainText().strip()
        if not question:
            self.set_status("Please enter a question", error=True)
            return
        self.input_field.setEnabled(False)
        self.ask_button.setEnabled(False)
        self.mic_button.setEnabled(False)
        self.alchemy_circle.set_active(True)
        self.set_status("Transmuting…")
        self.question_submitted.emit(question)
        logger.info(f"Question submitted: {question[:60]}…")

    def enable_input(self):
        self.hide_listening()
        self.stt_label.hide()
        self.input_field.setEnabled(True)
        self.ask_button.setEnabled(True)
        self.mic_button.setEnabled(True)
        self.alchemy_circle.set_active(False)
        self.input_field.clear()
        self.input_field.setFocus()

    def keyPressEvent(self, event):
        ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        if event.key() == Qt.Key.Key_Escape:
            self.hide_overlay()
        elif ctrl and event.key() == Qt.Key.Key_R:
            self._periodic_refresh()
            event.accept()
        elif ctrl and event.key() == Qt.Key.Key_1:
            self._select_mode(ScreenshotMode.CURSOR_REGION)
            event.accept()
        elif ctrl and event.key() == Qt.Key.Key_2:
            self._select_mode(ScreenshotMode.ACTIVE_WINDOW)
            event.accept()
        elif ctrl and event.key() == Qt.Key.Key_3:
            self._select_mode(ScreenshotMode.FULL_SCREEN)
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.input_field.hasFocus() and self.input_field.toPlainText().strip():
                self._on_ask_clicked()
            event.accept()
        else:
            super().keyPressEvent(event)


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)

    overlay = EdwardOverlay()

    def on_q(q: str):
        overlay.set_response(f"Edward says: {q}")
        overlay.enable_input()

    overlay.question_submitted.connect(on_q)
    overlay.show_overlay()
    sys.exit(app.exec())
