"""
Animated Transmutation Circle Widget
Draws a FullMetal Alchemist-style alchemy circle with QPainter.
Outer ring rotates clockwise, inner ring counter-clockwise.
"""

import math
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF

from config import COLORS


class AlchemyCircle(QWidget):
    """
    Self-animating alchemy circle.
    Call set_active(True) to speed up and turn the inner hexagram red
    (used to signal that Edward is 'transmuting').
    """

    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self._outer_angle  = 0.0
        self._inner_angle  = 0.0
        self._active       = False
        self._pulse        = 0.0    # 0→1 glow pulse when active
        self._pulse_dir    = 1

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(16)   # ~60 fps

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def set_active(self, active: bool):
        self._active = active

    # ── Animation tick ────────────────────────────────────────────────────────

    def _tick(self):
        speed = 2.0 if self._active else 0.4
        self._outer_angle = (self._outer_angle + speed)        % 360
        self._inner_angle = (self._inner_angle - speed * 0.65) % 360

        if self._active:
            self._pulse += 0.04 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse = 1.0; self._pulse_dir = -1
            elif self._pulse <= 0.0:
                self._pulse = 0.0; self._pulse_dir = 1
        else:
            self._pulse = 0.0

        self.update()

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w   = self.width()
        h   = self.height()
        cx  = w / 2
        cy  = h / 2
        r   = min(cx, cy) - 2
        lw  = max(1.0, w / 40)   # line width scales with widget size

        gold     = QColor(COLORS['gold'])
        gold_dim = QColor(COLORS['gold'])
        gold_dim.setAlphaF(0.35)
        red      = QColor(COLORS['red'])

        # ── Outer ring (rotates clockwise) ─────────────────────────────────
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._outer_angle)
        painter.translate(-cx, -cy)

        pen = QPen(gold, lw)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # 18 tick marks (every 20°; longer every 3rd)
        for i in range(18):
            a     = math.radians(i * 20)
            inner = r * (0.80 if i % 3 == 0 else 0.88)
            x1    = cx + inner * math.cos(a)
            y1    = cy + inner * math.sin(a)
            x2    = cx + r     * math.cos(a)
            y2    = cy + r     * math.sin(a)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        painter.restore()

        # ── Inner ring (counter-rotates) ───────────────────────────────────
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._inner_angle)
        painter.translate(-cx, -cy)

        r2  = r * 0.70
        pen2 = QPen(gold, lw * 0.75)
        painter.setPen(pen2)
        painter.drawEllipse(QPointF(cx, cy), r2, r2)

        # 6 notches on inner ring
        for i in range(6):
            a     = math.radians(i * 60)
            inner = r2 * 0.86
            x1    = cx + inner * math.cos(a)
            y1    = cy + inner * math.sin(a)
            x2    = cx + r2    * math.cos(a)
            y2    = cy + r2    * math.sin(a)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        painter.restore()

        # ── Hexagram (two triangles, static) ──────────────────────────────
        r3      = r * 0.58
        hex_col = red if self._active else gold_dim
        if self._active:
            # Pulse the alpha
            hex_col = QColor(COLORS['red'])
            hex_col.setAlphaF(0.5 + 0.5 * self._pulse)
        hex_pen = QPen(hex_col, lw * 0.7)
        painter.setPen(hex_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        def _triangle(offset_deg: float):
            pts = QPolygonF()
            for k in range(3):
                a = math.radians(k * 120 + offset_deg)
                pts.append(QPointF(cx + r3 * math.cos(a), cy + r3 * math.sin(a)))
            painter.drawPolygon(pts)

        _triangle(-90)   # pointing up
        _triangle(90)    # pointing down

        # ── Centre dot ────────────────────────────────────────────────────
        r4      = r * 0.13
        dot_col = QColor(COLORS['red']) if self._active else gold
        if self._active:
            dot_col.setAlphaF(0.6 + 0.4 * self._pulse)
        painter.setBrush(QBrush(dot_col))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r4, r4)

        painter.end()


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = QWidget()
    w.setStyleSheet("background: #0D0D0D;")
    w.resize(300, 300)

    circle = AlchemyCircle(240, w)
    circle.move(30, 30)
    circle.start()
    circle.show()
    w.show()

    import time
    from PySide6.QtCore import QTimer as QT
    def toggle():
        circle.set_active(not circle._active)
    QT.singleShot(3000, toggle)

    sys.exit(app.exec())
