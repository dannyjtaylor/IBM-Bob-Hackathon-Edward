"""Modal dialog for unlocking the Edward password vault with a master password"""

import sys
import base64
import hashlib
import sqlite3
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from cryptography.fernet import Fernet, InvalidToken

from config import COLORS, VAULT_PATH
from vault import PasswordVault
from logger import get_logger

logger = get_logger(__name__)

_LABEL_STYLE = f"color: {COLORS['text']}; font-size: 13px;"
_ERROR_STYLE = f"color: {COLORS['red']}; font-size: 12px;"


def _verify_password(password: str) -> bool:
    """Returns True if password decrypts an existing entry, or vault is empty/new."""
    try:
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'edward_salt', 100000)
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


class PasswordUnlockDialog(QDialog):
    """
    Modal dialog that asks for the master password.
    Call get_vault() after exec() returns Accepted to retrieve the open vault.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vault: Optional[PasswordVault] = None
        self._setup_window()
        self._setup_ui()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("Unlock Password Vault")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.setFixedSize(380, 220)
        self.setStyleSheet(f"background-color: {COLORS['panel']};")

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Password Vault")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['gold']};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._make_label("Master password"))

        # Password row
        pw_row = QHBoxLayout()
        pw_row.setSpacing(6)

        self._pw_field = QLineEdit()
        self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_field.setFont(QFont("Segoe UI", 11))
        self._pw_field.setPlaceholderText("Enter master password…")
        self._pw_field.setStyleSheet(self._input_style())
        self._pw_field.returnPressed.connect(self._on_unlock)
        pw_row.addWidget(self._pw_field)

        self._toggle_btn = QPushButton("Show")
        self._toggle_btn.setFixedWidth(52)
        self._toggle_btn.setFont(QFont("Segoe UI", 9))
        self._toggle_btn.setStyleSheet(self._ghost_btn_style())
        self._toggle_btn.clicked.connect(self._toggle_echo)
        pw_row.addWidget(self._toggle_btn)

        layout.addLayout(pw_row)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet(_ERROR_STYLE)
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._error_label)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 11))
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet(self._ghost_btn_style(full=True))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        unlock_btn = QPushButton("Unlock")
        unlock_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        unlock_btn.setMinimumHeight(40)
        unlock_btn.setStyleSheet(self._primary_btn_style())
        unlock_btn.clicked.connect(self._on_unlock)
        btn_row.addWidget(unlock_btn)

        layout.addLayout(btn_row)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(_LABEL_STYLE)
        return lbl

    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['silver']};
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 13px;
            }}
            QLineEdit:focus {{ border-color: {COLORS['gold']}; }}
        """

    def _ghost_btn_style(self, full: bool = False) -> str:
        w = "" if full else "min-width: 52px;"
        return f"""
            QPushButton {{
                background-color: {COLORS['background']};
                color: {COLORS['silver']};
                border: 1px solid {COLORS['silver']};
                border-radius: 5px;
                padding: 6px 10px;
                {w}
            }}
            QPushButton:hover {{ background-color: #2A2A2A; }}
        """

    def _primary_btn_style(self) -> str:
        return f"""
            QPushButton {{
                background-color: {COLORS['gold']};
                color: {COLORS['background']};
                border: none;
                border-radius: 5px;
                padding: 6px 10px;
            }}
            QPushButton:hover {{ background-color: #E5B52E; }}
            QPushButton:pressed {{ background-color: #C09020; }}
        """

    def _toggle_echo(self):
        if self._pw_field.echoMode() == QLineEdit.EchoMode.Password:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_btn.setText("Hide")
        else:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_btn.setText("Show")

    # ── Logic ─────────────────────────────────────────────────────────────────

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
