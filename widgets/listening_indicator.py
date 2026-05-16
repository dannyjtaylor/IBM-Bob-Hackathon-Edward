"""Animated pulsing orb shown when Edward is actively listening for speech"""

import sys
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QRadialGradient

from config import COLORS
from logger import get_logger

logger = get_logger(__name__)


class ListeningIndicator(QWidget):
    """
    Pulsing orb embedded in EdwardOverlay.
    Gold (#DAA520) while active, fades in/out with 300ms transitions.
    Call start_animation() / stop_animation() to control visibility.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self.setStyleSheet("background: transparent;")

        self._pulse_val: float = 0.0
        self._opacity_val: float = 0.0
        self._active: bool = False

        self._setup_animations()

    # ── Qt properties (required for QPropertyAnimation) ──────────────────────

    def _get_pulse(self) -> float:
        return self._pulse_val

    def _set_pulse(self, v: float) -> None:
        self._pulse_val = v
        self.update()

    pulse = Property(float, _get_pulse, _set_pulse)

    def _get_opacity(self) -> float:
        return self._opacity_val

    def _set_opacity(self, v: float) -> None:
        self._opacity_val = v
        self.update()

    opacity = Property(float, _get_opacity, _set_opacity)

    # ── Animations ───────────────────────────────────────────────────────────

    def _setup_animations(self):
        self._pulse_anim = QPropertyAnimation(self, b"pulse")
        self._pulse_anim.setDuration(1200)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._pulse_anim.setLoopCount(-1)

        self._fade_in = QPropertyAnimation(self, b"opacity")
        self._fade_in.setDuration(300)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade_out = QPropertyAnimation(self, b"opacity")
        self._fade_out.setDuration(300)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self.hide)

    def start_animation(self):
        self._active = True
        self._fade_out.stop()
        self._pulse_anim.start()
        self._fade_in.start()
        logger.debug("ListeningIndicator: started")

    def stop_animation(self):
        self._active = False
        self._pulse_anim.stop()
        self._fade_in.stop()
        self._fade_out.setStartValue(self._opacity_val)
        self._fade_out.setEndValue(0.0)
        self._fade_out.start()
        logger.debug("ListeningIndicator: stopped")

    # ── Painting ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        if self._opacity_val < 0.01:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity_val)

        cx, cy = self.width() / 2, self.height() / 2
        color = QColor(COLORS['gold']) if self._active else QColor(COLORS['silver'])

        # Outer pulse ring — expands and fades as pulse goes 0→1
        if self._active:
            ring_r = 30 + self._pulse_val * 26
            ring_color = QColor(COLORS['gold'])
            ring_color.setAlphaF(0.28 * (1.0 - self._pulse_val))
            painter.setBrush(ring_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                int(cx - ring_r), int(cy - ring_r),
                int(ring_r * 2), int(ring_r * 2)
            )

        # Core orb with radial gradient (slightly off-center highlight)
        core_r = 26 + (self._pulse_val * 4 if self._active else 0)
        grad = QRadialGradient(cx - core_r * 0.2, cy - core_r * 0.2, core_r)
        grad.setColorAt(0.0, color.lighter(160))
        grad.setColorAt(0.65, color)
        grad.setColorAt(1.0, color.darker(130))

        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            int(cx - core_r), int(cy - core_r),
            int(core_r * 2), int(core_r * 2)
        )
        painter.end()


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = QWidget()
    w.setStyleSheet("background: #1A1A1A;")
    w.resize(200, 200)

    indicator = ListeningIndicator(w)
    indicator.move(40, 40)
    indicator.show()
    indicator.start_animation()

    w.show()
    sys.exit(app.exec())
