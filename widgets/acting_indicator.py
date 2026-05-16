"""Floating bottom-right corner indicator shown when Edward is executing an action"""

import sys
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from config import COLORS
from logger import get_logger

logger = get_logger(__name__)


class ActingIndicator(QWidget):
    """
    Frameless top-level window pinned to bottom-right corner.
    Shows a spinning arc and 'Edward is acting...' in red (#B22222).
    Call show_acting() / hide_acting() to animate in/out.
    """

    def __init__(self):
        super().__init__(None)
        self._arc_angle: int = 0

        self._setup_window()
        self._setup_ui()
        self._setup_animations()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)
        self.setFixedSize(224, 48)
        self._reposition()

    def _reposition(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.width() - self.width() - 20,
            screen.height() - self.height() - 60,
        )

    # ── UI ───────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(42, 0, 14, 0)
        layout.setSpacing(0)

        self._label = QLabel("Edward is acting...")
        self._label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {COLORS['red']}; background: transparent;")
        layout.addWidget(self._label)

    # ── Animations ───────────────────────────────────────────────────────────

    def _setup_animations(self):
        # Spinner driven by a 60-fps timer
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick)
        self._spinner_timer.setInterval(16)

        self._fade_in = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in.setDuration(300)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade_out = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out.setDuration(300)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self.hide)

    def _tick(self):
        self._arc_angle = (self._arc_angle + 6) % 360
        self.update()

    # ── Public API ───────────────────────────────────────────────────────────

    def show_acting(self):
        self._reposition()
        self.show()
        self._fade_out.stop()
        self._fade_in.setStartValue(self.windowOpacity())
        self._fade_in.start()
        self._spinner_timer.start()
        logger.debug("ActingIndicator: shown")

    def hide_acting(self):
        self._spinner_timer.stop()
        self._fade_in.stop()
        self._fade_out.setStartValue(self.windowOpacity())
        self._fade_out.start()
        logger.debug("ActingIndicator: hidden")

    # ── Painting ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark pill background
        bg = QColor(COLORS['panel'])
        bg.setAlpha(238)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

        # Spinner arc (270° sweep, rotating)
        cx, cy = 21, self.height() // 2
        r = 10
        pen = QPen(QColor(COLORS['red']))
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Qt arc angles: positive = counter-clockwise, units = 1/16 degree
        painter.drawArc(cx - r, cy - r, r * 2, r * 2, (-self._arc_angle) * 16, 270 * 16)

        painter.end()


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ActingIndicator()
    w.show_acting()
    sys.exit(app.exec())
