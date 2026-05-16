"""Modal dialog for unlocking the Edward password vault with a master password"""

import sys
import math
import base64
import hashlib
import sqlite3
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QWidget
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QFont, QPainter, QPen, QBrush, QColor, QPolygonF

from cryptography.fernet import Fernet, InvalidToken

from config import COLORS, VAULT_PATH
from vault import PasswordVault
from logger import get_logger

logger = get_logger(__name__)

_GOLD   = COLORS['gold']
_RED    = COLORS['red']
_BG     = COLORS['background']
_PANEL  = COLORS['panel']
_TEXT   = COLORS['text']
_SILVER = COLORS['silver']


# ── Alchemy Circle Widget ─────────────────────────────────────────────────────

class _AlchemyCircle(QWidget):
    """Draws an FMA-style transmutation circle using QPainter."""

    def __init__(self, size: int = 80, parent=None):
        super().__init__(parent)
        self._sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s  = self._sz
        cx = cy = s / 2
        ro = s / 2 - 2
        ri = ro * 0.72
        rh = ro * 0.62
        rc = ro * 0.18
        lw = max(1.5, s / 40)

        gold  = QColor(_GOLD)
        dark  = QColor(_BG)

        def pt(deg, r):
            a = math.radians(deg - 90)
            return QPointF(cx + r * math.cos(a), cy + r * math.sin(a))

        # Dark disk
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(dark))
        p.drawEllipse(QPointF(cx, cy), ro, ro)

        pen = QPen(gold, lw)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Outer ring
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        # Inner ring
        p.drawEllipse(QPointF(cx, cy), ri, ri)
        # Center circle
        p.drawEllipse(QPointF(cx, cy), rc, rc)

        # Two triangles (hexagram)
        for offsets in [(0, 120, 240), (60, 180, 300)]:
            poly = QPolygonF([pt(a, rh) for a in offsets])
            p.drawPolygon(poly)

        # Node dots
        p.setBrush(QBrush(gold))
        p.setPen(Qt.PenStyle.NoPen)
        rn = max(2.5, s / 20)
        for angle in range(0, 360, 60):
            p.drawEllipse(pt(angle, rh), rn, rn)

        # Tick marks (12)
        p.setPen(QPen(gold, lw))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(12):
            a = math.radians(i * 30 - 90)
            p.drawLine(
                QPointF(cx + (ro - 1) * math.cos(a), cy + (ro - 1) * math.sin(a)),
                QPointF(cx + (ro - 5) * math.cos(a), cy + (ro - 5) * math.sin(a)),
            )

        p.end()


# ── Password verification ─────────────────────────────────────────────────────

def _verify_password(password: str) -> bool:
    """Returns True if password decrypts an existing entry, or vault is empty/new."""
    try:
        key    = hashlib.pbkdf2_hmac('sha256', password.encode(), b'edward_salt', 100000)
        cipher = Fernet(base64.urlsafe_b64encode(key))
        with sqlite3.connect(VAULT_PATH) as conn:
            row = conn.execute(
                "SELECT password_encrypted FROM passwords LIMIT 1"
            ).fetchone()
        if row is None:
            return True
        cipher.decrypt(row[0])
        return True
    except InvalidToken:
        return False
    except Exception:
        return True  # vault DB doesn't exist yet — first-time setup


# ── Unlock Dialog ─────────────────────────────────────────────────────────────

class PasswordUnlockDialog(QDialog):
    """Modal dialog that asks for the master password before opening the vault."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vault: Optional[PasswordVault] = None
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        self.setWindowTitle("Edward — Unlock Vault")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(400, 310)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {_BG};
                border: 2px solid {_GOLD};
                border-radius: 8px;
            }}
        """)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QWidget()
        header.setStyleSheet(f"background-color: {_PANEL}; border-bottom: 2px solid {_GOLD};")
        header.setFixedHeight(100)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 10, 20, 10)
        h_layout.setSpacing(16)

        circle = _AlchemyCircle(size=72)
        h_layout.addWidget(circle)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("EDWARD'S VAULT")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {_GOLD}; background: transparent;")
        title_col.addWidget(title)

        sub = QLabel("Equivalent Exchange: Enter to access")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet(f"color: {_SILVER}; background: transparent;")
        title_col.addWidget(sub)

        h_layout.addLayout(title_col)
        h_layout.addStretch()
        root.addWidget(header)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet(f"background-color: {_BG};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 22, 28, 22)
        body_layout.setSpacing(14)

        prompt = QLabel("Master password")
        prompt.setStyleSheet(f"color: {_SILVER}; font-size: 12px;")
        body_layout.addWidget(prompt)

        # Password input row
        pw_row = QHBoxLayout()
        pw_row.setSpacing(8)

        self._pw_field = QLineEdit()
        self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_field.setFont(QFont("Segoe UI", 12))
        self._pw_field.setPlaceholderText("Enter master password…")
        self._pw_field.setMinimumHeight(42)
        self._pw_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {_PANEL};
                color: {_TEXT};
                border: 2px solid {_SILVER};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {_GOLD}; }}
        """)
        self._pw_field.returnPressed.connect(self._on_unlock)
        pw_row.addWidget(self._pw_field)

        self._toggle_btn = QPushButton("Show")
        self._toggle_btn.setFixedSize(56, 42)
        self._toggle_btn.setFont(QFont("Segoe UI", 9))
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_PANEL};
                color: {_SILVER};
                border: 1px solid {_SILVER};
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #252525; color: {_TEXT}; }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_echo)
        pw_row.addWidget(self._toggle_btn)

        body_layout.addLayout(pw_row)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet(f"color: {_RED}; font-size: 12px;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(self._error_label)

        body_layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 11))
        cancel_btn.setMinimumHeight(42)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_SILVER};
                border: 1px solid {_SILVER};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{ background-color: #1E1E1E; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        unlock_btn = QPushButton("⚡  Unlock")
        unlock_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        unlock_btn.setMinimumHeight(42)
        unlock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_GOLD};
                color: {_BG};
                border: none;
                border-radius: 6px;
                padding: 6px 20px;
            }}
            QPushButton:hover {{ background-color: #E5B52E; }}
            QPushButton:pressed {{ background-color: #C09020; }}
        """)
        unlock_btn.clicked.connect(self._on_unlock)
        btn_row.addWidget(unlock_btn)

        body_layout.addLayout(btn_row)
        root.addWidget(body)

    def _toggle_echo(self):
        if self._pw_field.echoMode() == QLineEdit.EchoMode.Password:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_btn.setText("Hide")
        else:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_btn.setText("Show")

    def _on_unlock(self):
        password = self._pw_field.text()
        if not password:
            self._error_label.setText("Please enter the master password.")
            return
        if not _verify_password(password):
            self._error_label.setText("Incorrect password. Try again.")
            self._pw_field.clear()
            self._pw_field.setFocus()
            logger.warning("PasswordUnlockDialog: wrong master password")
            return
        self._vault = PasswordVault(master_password=password)
        logger.info("PasswordUnlockDialog: vault unlocked")
        self.accept()

    def get_vault(self) -> Optional[PasswordVault]:
        return self._vault


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = PasswordUnlockDialog()
    if dlg.exec() == QDialog.DialogCode.Accepted:
        vault = dlg.get_vault()
        print(f"Unlocked. Entries: {len(vault.list_entries())}")
    else:
        print("Cancelled.")
    sys.exit(0)
