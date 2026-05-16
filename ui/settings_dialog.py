"""Settings dialog for configuring Edward — General, Voice, Hotkeys, Advanced tabs"""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QWidget, QLabel, QLineEdit, QPushButton,
    QCheckBox, QSlider, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from dotenv import set_key, load_dotenv

from config import COLORS, PROJECT_ROOT
from logger import get_logger

logger = get_logger(__name__)

ENV_PATH = PROJECT_ROOT / ".env"

_PANEL  = f"background-color: {COLORS['panel']};"
_SILVER = f"color: {COLORS['silver']}; font-size: 12px;"
_TEXT   = f"color: {COLORS['text']};"
_GOLD   = f"color: {COLORS['gold']};"


def _h(text: str, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    lbl.setStyleSheet(_TEXT)
    return lbl


def _lbl(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(_SILVER)
    return lbl


def _field(placeholder: str = "", echo_password: bool = False) -> QLineEdit:
    f = QLineEdit()
    f.setPlaceholderText(placeholder)
    f.setFont(QFont("Segoe UI", 11))
    if echo_password:
        f.setEchoMode(QLineEdit.EchoMode.Password)
    f.setStyleSheet(f"""
        QLineEdit {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            border: 2px solid {COLORS['silver']};
            border-radius: 5px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        QLineEdit:focus {{ border-color: {COLORS['gold']}; }}
        QLineEdit:read-only {{ color: {COLORS['silver']}; border-color: #333; }}
    """)
    return f


def _check(label: str) -> QCheckBox:
    cb = QCheckBox(label)
    cb.setFont(QFont("Segoe UI", 11))
    cb.setStyleSheet(f"""
        QCheckBox {{ color: {COLORS['text']}; spacing: 8px; }}
        QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 3px;
            border: 2px solid {COLORS['silver']}; background: {COLORS['background']}; }}
        QCheckBox::indicator:checked {{ background: {COLORS['gold']}; border-color: {COLORS['gold']}; }}
    """)
    return cb


def _combo(options: list[str]) -> QComboBox:
    cb = QComboBox()
    cb.addItems(options)
    cb.setFont(QFont("Segoe UI", 11))
    cb.setStyleSheet(f"""
        QComboBox {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            border: 2px solid {COLORS['silver']};
            border-radius: 5px;
            padding: 5px 10px;
        }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['panel']};
            color: {COLORS['text']};
            selection-background-color: {COLORS['gold']};
            selection-color: {COLORS['background']};
        }}
    """)
    return cb


def _primary_btn(label: str, color: str = COLORS['gold']) -> QPushButton:
    btn = QPushButton(label)
    btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    btn.setMinimumHeight(38)
    text_color = COLORS['background'] if color == COLORS['gold'] else COLORS['text']
    btn.setStyleSheet(f"""
        QPushButton {{ background-color: {color}; color: {text_color};
            border: none; border-radius: 5px; padding: 6px 16px; }}
        QPushButton:hover {{ background-color: {'#E5B52E' if color == COLORS['gold'] else '#CC2222'}; }}
    """)
    return btn


def _ghost_btn(label: str) -> QPushButton:
    btn = QPushButton(label)
    btn.setFont(QFont("Segoe UI", 11))
    btn.setMinimumHeight(38)
    btn.setStyleSheet(f"""
        QPushButton {{ background-color: {COLORS['background']}; color: {COLORS['silver']};
            border: 1px solid {COLORS['silver']}; border-radius: 5px; padding: 6px 16px; }}
        QPushButton:hover {{ background-color: #2A2A2A; }}
    """)
    return btn


def _tab_widget() -> QWidget:
    w = QWidget()
    w.setStyleSheet(_PANEL)
    return w


def _form() -> QFormLayout:
    f = QFormLayout()
    f.setSpacing(14)
    f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    f.setContentsMargins(20, 20, 20, 10)
    return f


# ── Settings dialog ───────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    """
    Tabbed settings dialog.  Reads from .env on open, writes back on Save.
    Most changes require an app restart; the dialog notes this where relevant.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        load_dotenv(ENV_PATH, override=True)
        self._setup_window()
        self._setup_ui()
        self._load()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("Edward — Settings")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.resize(520, 460)
        self.setStyleSheet(_PANEL)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['gold']}; padding: 16px 20px 8px 20px;")
        root.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background: {COLORS['panel']}; }}
            QTabBar::tab {{
                background: {COLORS['background']}; color: {COLORS['silver']};
                padding: 8px 18px; font-size: 12px; border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{ color: {COLORS['gold']}; border-bottom: 2px solid {COLORS['gold']}; }}
            QTabBar::tab:hover {{ color: {COLORS['text']}; }}
        """)

        self._tabs.addTab(self._build_general(),  "General")
        self._tabs.addTab(self._build_voice(),    "Voice")
        self._tabs.addTab(self._build_hotkeys(),  "Hotkeys")
        self._tabs.addTab(self._build_advanced(), "Advanced")
        root.addWidget(self._tabs, stretch=1)

        # Bottom bar
        bar = QHBoxLayout()
        bar.setContentsMargins(20, 12, 20, 16)
        bar.setSpacing(10)
        bar.addStretch()

        cancel = _ghost_btn("Cancel")
        cancel.clicked.connect(self.reject)
        bar.addWidget(cancel)

        save = _primary_btn("Save")
        save.clicked.connect(self._on_save)
        bar.addWidget(save)

        root.addLayout(bar)

    # ── General tab ───────────────────────────────────────────────────────────

    def _build_general(self) -> QWidget:
        tab = _tab_widget()
        form = _form()
        tab.setLayout(form)

        self._username = _field("e.g. Jackson")
        form.addRow(_lbl("Your name"), self._username)

        note = _lbl("More themes coming soon")
        note.setStyleSheet(f"color: #555; font-size: 11px; font-style: italic;")
        form.addRow(_lbl("Theme"), note)

        return tab

    # ── Voice tab ─────────────────────────────────────────────────────────────

    def _build_voice(self) -> QWidget:
        tab = _tab_widget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 10)
        layout.setSpacing(14)

        self._tts_enabled = _check("Enable text-to-speech (ElevenLabs)")
        layout.addWidget(self._tts_enabled)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._voice_id = _field("ElevenLabs voice ID")
        form.addRow(_lbl("Voice ID"), self._voice_id)

        self._stt_model = _combo(["tiny", "base", "small", "medium", "large"])
        form.addRow(_lbl("STT model (Whisper)"), self._stt_model)

        layout.addLayout(form)
        layout.addSpacing(8)

        self._wake_enabled = _check("Enable wake word detection")
        layout.addWidget(self._wake_enabled)

        # Threshold slider
        slider_row = QHBoxLayout()
        slider_lbl = _lbl("Wake word sensitivity")
        slider_row.addWidget(slider_lbl)

        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setRange(0, 100)
        self._threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._threshold_slider.setTickInterval(10)
        self._threshold_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height: 4px; background: #333; border-radius: 2px; }}
            QSlider::handle:horizontal {{
                width: 14px; height: 14px; margin: -5px 0;
                background: {COLORS['gold']}; border-radius: 7px;
            }}
            QSlider::sub-page:horizontal {{ background: {COLORS['gold']}; border-radius: 2px; }}
        """)
        slider_row.addWidget(self._threshold_slider, stretch=1)

        self._threshold_val = QLabel("0.50")
        self._threshold_val.setStyleSheet(f"color: {COLORS['gold']}; font-size: 12px; min-width: 36px;")
        self._threshold_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        slider_row.addWidget(self._threshold_val)

        self._threshold_slider.valueChanged.connect(
            lambda v: self._threshold_val.setText(f"{v / 100:.2f}")
        )
        layout.addLayout(slider_row)
        layout.addStretch()

        return tab

    # ── Hotkeys tab ───────────────────────────────────────────────────────────

    def _build_hotkeys(self) -> QWidget:
        tab = _tab_widget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 10)
        layout.setSpacing(14)

        self._hotkey_enabled = _check("Enable global hotkey")
        layout.addWidget(self._hotkey_enabled)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        hotkey_display = _field()
        hotkey_display.setText("Win + Shift + E")
        hotkey_display.setReadOnly(True)
        form.addRow(_lbl("Current hotkey"), hotkey_display)

        layout.addLayout(form)

        note = QLabel("Custom hotkey rebinding requires a restart and is not yet configurable from this UI.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: #555; font-size: 11px; font-style: italic;")
        layout.addWidget(note)

        layout.addStretch()
        return tab

    # ── Advanced tab ──────────────────────────────────────────────────────────

    def _build_advanced(self) -> QWidget:
        tab = _tab_widget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 16, 20, 10)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._bob_url = _field("http://localhost:8000")
        form.addRow(_lbl("Bob API URL"), self._bob_url)

        self._bob_key = _field("API key", echo_password=True)
        form.addRow(_lbl("Bob API key"), self._bob_key)

        self._ollama_url = _field("http://localhost:11434")
        form.addRow(_lbl("Ollama URL"), self._ollama_url)

        self._ollama_model = _field("e.g. llava:13b")
        form.addRow(_lbl("Ollama model"), self._ollama_model)

        layout.addLayout(form)

        self._debug_mode = _check("Enable debug logging")
        layout.addWidget(self._debug_mode)

        layout.addStretch()

        clear_btn = _primary_btn("Clear Conversation History", color=COLORS['red'])
        clear_btn.clicked.connect(self._on_clear_history)
        layout.addWidget(clear_btn)

        return tab

    # ── Load / Save ───────────────────────────────────────────────────────────

    def _load(self):
        self._username.setText(os.getenv("USER_NAME", ""))
        self._tts_enabled.setChecked(os.getenv("TTS_ENABLED", "false").lower() == "true")
        self._voice_id.setText(os.getenv("ELEVENLABS_VOICE_ID", ""))
        stt = os.getenv("STT_MODEL", "base")
        idx = self._stt_model.findText(stt)
        self._stt_model.setCurrentIndex(max(idx, 0))
        self._wake_enabled.setChecked(os.getenv("WAKE_WORD_ENABLED", "true").lower() == "true")
        threshold = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
        self._threshold_slider.setValue(int(threshold * 100))
        self._hotkey_enabled.setChecked(os.getenv("HOTKEY_ENABLED", "true").lower() == "true")
        self._bob_url.setText(os.getenv("IBM_BOB_API_URL", "http://localhost:8000"))
        self._bob_key.setText(os.getenv("IBM_BOB_API_KEY", ""))
        self._ollama_url.setText(os.getenv("OLLAMA_URL", "http://localhost:11434"))
        self._ollama_model.setText(os.getenv("OLLAMA_MODEL", ""))
        self._debug_mode.setChecked(os.getenv("DEBUG_MODE", "false").lower() == "true")

    def _save_env(self, key: str, value: str):
        set_key(str(ENV_PATH), key, value)
        os.environ[key] = value

    def _on_save(self):
        self._save_env("USER_NAME",            self._username.text().strip() or "User")
        self._save_env("TTS_ENABLED",          str(self._tts_enabled.isChecked()).lower())
        self._save_env("ELEVENLABS_VOICE_ID",  self._voice_id.text().strip())
        self._save_env("STT_MODEL",            self._stt_model.currentText())
        self._save_env("WAKE_WORD_ENABLED",    str(self._wake_enabled.isChecked()).lower())
        self._save_env("WAKE_WORD_THRESHOLD",  f"{self._threshold_slider.value() / 100:.2f}")
        self._save_env("HOTKEY_ENABLED",       str(self._hotkey_enabled.isChecked()).lower())
        self._save_env("IBM_BOB_API_URL",      self._bob_url.text().strip())
        self._save_env("IBM_BOB_API_KEY",      self._bob_key.text().strip())
        self._save_env("OLLAMA_URL",           self._ollama_url.text().strip())
        self._save_env("OLLAMA_MODEL",         self._ollama_model.text().strip())
        self._save_env("DEBUG_MODE",           str(self._debug_mode.isChecked()).lower())

        logger.info("Settings saved to .env")
        self.accept()

    def _on_clear_history(self):
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Clear History")
        confirm.setText("Delete all conversation history? This cannot be undone.")
        confirm.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        confirm.setDefaultButton(QMessageBox.StandardButton.Cancel)
        confirm.setStyleSheet(_PANEL + f" color: {COLORS['text']};")
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            return
        try:
            from database import EdwardDatabase
            EdwardDatabase().clear_history()
            logger.info("Conversation history cleared from settings")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = SettingsDialog()
    dlg.exec()
    sys.exit(0)
