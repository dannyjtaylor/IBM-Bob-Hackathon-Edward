"""Floating bottom-right indicator shown when Edward is transmuting (processing)."""

import math
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
    Shows a spinning alchemy arc and '⚡ Transmuting…' in Edward's gold/red.
    Call show_acting() / hide_acting() to animate in/out.
    """

    def __init__(self):
        super().__init__(None)
        self._arc_angle: int  = 0
        self._ring_angle: int = 0

        self._setup_window()
        self._setup_ui()
        self._setup_animations()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)
        self.setFixedSize(240, 52)
        self._reposition()

    def _reposition(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - self.width() - 20,
                  screen.height() - self.height() - 60)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(50, 0, 14, 0)

        self._label = QLabel("⚡  Transmuting…")
        self._label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {COLORS['gold']}; background: transparent;")
        layout.addWidget(self._label)

    def _setup_animations(self):
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
        self._arc_angle  = (self._arc_angle  + 7) % 360
        self._ring_angle = (self._ring_angle  - 4) % 360
        self.update()

    # ── Public API ────────────────────────────────────────────────────────────

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

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark pill background
        bg = QColor(COLORS['panel'])
        bg.setAlpha(230)
        painter.setBrush(bg)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 6, 6)

        # ── Alchemy circle spinner (left side) ────────────────────────────
        cx, cy = 25, self.height() // 2
        r_out  = 14
        r_in   = 9

        gold = QColor(COLORS['gold'])
        red  = QColor(COLORS['red'])

        # Outer ring (clockwise)
        pen_out = QPen(gold, 2)
        pen_out.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_out)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(cx - r_out), int(cy - r_out),
                        int(r_out * 2), int(r_out * 2),
                        (-self._arc_angle) * 16, 270 * 16)

        # Inner ring (counter-clockwise, red)
        pen_in = QPen(red, 1)
        pen_in.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_in)
        painter.drawArc(int(cx - r_in), int(cy - r_in),
                        int(r_in * 2), int(r_in * 2),
                        self._ring_angle * 16, 200 * 16)

        # Tick marks on outer ring (6 marks)
        for i in range(6):
            angle = math.radians(i * 60 + self._arc_angle)
            inner = r_out * 0.75
            x1 = cx + inner * math.cos(angle)
            y1 = cy + inner * math.sin(angle)
            x2 = cx + r_out  * math.cos(angle)
            y2 = cy + r_out  * math.sin(angle)
            pen_tick = QPen(gold, 1)
            painter.setPen(pen_tick)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        painter.end()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ActingIndicator()
    w.show_acting()
    sys.exit(app.exec())
