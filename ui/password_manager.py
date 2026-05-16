"""Main password manager UI — credential list with add/edit/delete/copy"""

import sys
import math
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QWidget, QFrame
)
from PySide6.QtCore import Qt, QTimer, QEvent, QPointF
from PySide6.QtGui import QFont, QGuiApplication, QPainter, QPen, QBrush, QColor, QPolygonF

from vault import PasswordVault
from config import COLORS
from logger import get_logger

logger = get_logger(__name__)

_GOLD   = COLORS['gold']
_RED    = COLORS['red']
_BG     = COLORS['background']
_PANEL  = COLORS['panel']
_TEXT   = COLORS['text']
_SILVER = COLORS['silver']

_COL_SERVICE  = 0
_COL_USERNAME = 1
_COL_PASSWORD = 2


# ── Shared widget helpers ──────────────────────────────────────────────────────

class _AlchemyCircle(QWidget):
    def __init__(self, size: int = 56, parent=None):
        super().__init__(parent)
        self._sz = size
        self.setFixedSize(size, size)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._sz
        cx = cy = s / 2
        ro = s / 2 - 2
        ri, rh, rc = ro * 0.72, ro * 0.62, ro * 0.18
        lw = max(1.2, s / 42)

        gold = QColor(_GOLD)

        def pt(deg, r):
            a = math.radians(deg - 90)
            return QPointF(cx + r * math.cos(a), cy + r * math.sin(a))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(_BG)))
        p.drawEllipse(QPointF(cx, cy), ro, ro)

        p.setPen(QPen(gold, lw))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), ro, ro)
        p.drawEllipse(QPointF(cx, cy), ri, ri)
        p.drawEllipse(QPointF(cx, cy), rc, rc)

        for offsets in [(0, 120, 240), (60, 180, 300)]:
            p.drawPolygon(QPolygonF([pt(a, rh) for a in offsets]))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(gold))
        rn = max(2.0, s / 22)
        for angle in range(0, 360, 60):
            p.drawEllipse(pt(angle, rh), rn, rn)

        p.setPen(QPen(gold, lw))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(12):
            a = math.radians(i * 30 - 90)
            p.drawLine(
                QPointF(cx + (ro - 1) * math.cos(a), cy + (ro - 1) * math.sin(a)),
                QPointF(cx + (ro - 4) * math.cos(a), cy + (ro - 4) * math.sin(a)),
            )
        p.end()


def _btn(text: str, color: str = _GOLD, text_color: str = _BG,
         ghost: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold if not ghost else QFont.Weight.Normal))
    b.setMinimumHeight(38)
    if ghost:
        b.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_SILVER};
                border: 1px solid {_SILVER};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{ background-color: #1E1E1E; color: {_TEXT}; }}
            QPushButton:disabled {{ color: #444; border-color: #333; }}
        """)
    else:
        hover = "#E5B52E" if color == _GOLD else "#CC2222"
        b.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:disabled {{ background-color: #333; color: #666; }}
        """)
    return b


def _input_style(focus: str = _GOLD) -> str:
    return f"""
        QLineEdit {{
            background-color: {_PANEL};
            color: {_TEXT};
            border: 2px solid {_SILVER};
            border-radius: 6px;
            padding: 7px 10px;
            font-size: 13px;
        }}
        QLineEdit:focus {{ border-color: {focus}; }}
    """


# ── Add / Edit sub-dialog ─────────────────────────────────────────────────────

class _EntryDialog(QDialog):
    def __init__(self, parent=None, service="", username="", password="", notes=""):
        super().__init__(parent)
        self._initial = dict(service=service, username=username,
                             password=password, notes=notes)
        self._editing = bool(service)
        self._setup()

    def _setup(self):
        self.setWindowTitle("Edit Credential" if self._editing else "Add Credential")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(420, 340)
        self.setStyleSheet(f"background-color: {_BG}; border: 2px solid {_GOLD}; border-radius: 8px;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header band
        header = QWidget()
        header.setStyleSheet(f"background-color: {_PANEL}; border-bottom: 2px solid {_GOLD};")
        header.setFixedHeight(54)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 0, 18, 0)
        title = QLabel("EDIT CREDENTIAL" if self._editing else "ADD CREDENTIAL")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {_GOLD}; background: transparent;")
        hl.addWidget(title)
        root.addWidget(header)

        # Form body
        body = QWidget()
        body.setStyleSheet(f"background-color: {_BG};")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 18, 24, 18)
        bl.setSpacing(10)

        def row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {_SILVER}; font-size: 11px;")
            bl.addWidget(lbl)
            bl.addWidget(widget)

        self._service_field = QLineEdit(self._initial['service'])
        self._service_field.setStyleSheet(_input_style())
        self._service_field.setPlaceholderText("e.g. Gmail")
        if self._editing:
            self._service_field.setReadOnly(True)
        row("Service", self._service_field)

        self._username_field = QLineEdit(self._initial['username'])
        self._username_field.setStyleSheet(_input_style())
        self._username_field.setPlaceholderText("e.g. user@example.com")
        if self._editing:
            self._username_field.setReadOnly(True)
        row("Username / Email", self._username_field)

        # Password with show/hide
        pw_row = QHBoxLayout()
        pw_row.setSpacing(8)
        self._pw_field = QLineEdit(self._initial['password'])
        self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_field.setStyleSheet(_input_style())
        pw_row.addWidget(self._pw_field)
        self._show_btn = QPushButton("Show")
        self._show_btn.setFixedSize(56, 38)
        self._show_btn.setFont(QFont("Segoe UI", 9))
        self._show_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {_PANEL}; color: {_SILVER};
                           border: 1px solid {_SILVER}; border-radius: 6px; }}
            QPushButton:hover {{ background-color: #252525; }}
        """)
        self._show_btn.clicked.connect(self._toggle_echo)
        pw_row.addWidget(self._show_btn)

        pw_label = QLabel("Password")
        pw_label.setStyleSheet(f"color: {_SILVER}; font-size: 11px;")
        bl.addWidget(pw_label)
        bl.addLayout(pw_row)

        self._notes_field = QLineEdit(self._initial['notes'])
        self._notes_field.setStyleSheet(_input_style(_SILVER))
        self._notes_field.setPlaceholderText("Optional notes")
        row("Notes (optional)", self._notes_field)

        bl.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = _btn("Cancel", ghost=True)
        cancel.clicked.connect(self.reject)
        save = _btn("Save")
        save.clicked.connect(self._on_save)
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        bl.addLayout(btn_row)
        root.addWidget(body)

    def _toggle_echo(self):
        if self._pw_field.echoMode() == QLineEdit.EchoMode.Password:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_btn.setText("Hide")
        else:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_btn.setText("Show")

    def _on_save(self):
        if not self._service_field.text().strip():
            self._service_field.setFocus(); return
        if not self._username_field.text().strip():
            self._username_field.setFocus(); return
        if not self._pw_field.text():
            self._pw_field.setFocus(); return
        self.accept()

    def values(self) -> dict:
        return {
            "service":  self._service_field.text().strip(),
            "username": self._username_field.text().strip(),
            "password": self._pw_field.text(),
            "notes":    self._notes_field.text().strip(),
        }


# ── Main password manager dialog ──────────────────────────────────────────────

class PasswordManagerDialog(QDialog):
    _AUTO_LOCK_MS = 5 * 60 * 1000

    def __init__(self, vault: PasswordVault, parent=None):
        super().__init__(parent)
        self._vault = vault
        self._remaining = self._AUTO_LOCK_MS // 1000
        self._setup_window()
        self._setup_ui()
        self._setup_timers()
        self._load_entries()
        self.installEventFilter(self)

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("Edward — Password Vault")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.resize(680, 520)
        self.setMinimumSize(600, 440)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {_BG};
                border: 2px solid {_GOLD};
                border-radius: 8px;
            }}
        """)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_search_bar())
        root.addWidget(self._build_table(), stretch=1)
        root.addWidget(self._build_divider())
        root.addWidget(self._build_footer())

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setStyleSheet(f"background-color: {_PANEL}; border-bottom: 2px solid {_GOLD};")
        header.setFixedHeight(80)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 8, 20, 8)
        hl.setSpacing(16)

        circle = _AlchemyCircle(size=56)
        hl.addWidget(circle)

        col = QVBoxLayout()
        col.setSpacing(2)

        title = QLabel("EDWARD'S VAULT")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {_GOLD}; background: transparent;")
        col.addWidget(title)

        tagline = QLabel("All secrets stored locally — never leaves your machine")
        tagline.setFont(QFont("Segoe UI", 9))
        tagline.setStyleSheet(f"color: {_SILVER}; background: transparent;")
        col.addWidget(tagline)

        hl.addLayout(col)
        hl.addStretch()

        # Auto-lock countdown in header
        self._lock_label = QLabel("Auto-lock 5:00")
        self._lock_label.setFont(QFont("Segoe UI", 9))
        self._lock_label.setStyleSheet(f"color: {_SILVER}; background: transparent;")
        hl.addWidget(self._lock_label)

        return header

    def _build_search_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(f"background-color: {_BG};")
        bar.setFixedHeight(52)
        hl = QHBoxLayout(bar)
        hl.setContentsMargins(20, 8, 20, 8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search credentials…")
        self._search.setFont(QFont("Segoe UI", 11))
        self._search.setStyleSheet(_input_style(_SILVER))
        self._search.textChanged.connect(self._filter_table)
        hl.addWidget(self._search)

        return bar

    def _build_table(self) -> QTableWidget:
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Service", "Username", "Password"])
        h = self._table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 110)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(False)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {_BG};
                alternate-background-color: #111111;
                color: {_TEXT};
                gridline-color: transparent;
                border: none;
                font-size: 12px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid #1E1E1E;
            }}
            QTableWidget::item:selected {{
                background-color: {_RED};
                color: {_TEXT};
            }}
            QHeaderView::section {{
                background-color: {_PANEL};
                color: {_SILVER};
                border: none;
                border-bottom: 2px solid {_GOLD};
                padding: 8px 12px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QScrollBar:vertical {{
                background: {_BG};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #333;
                border-radius: 4px;
            }}
        """)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        return self._table

    def _build_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {_GOLD};")
        line.setFixedHeight(2)
        return line

    def _build_footer(self) -> QWidget:
        footer = QWidget()
        footer.setStyleSheet(f"background-color: {_PANEL};")
        footer.setFixedHeight(62)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(8)

        self._add_btn = _btn("+ Add")
        self._add_btn.clicked.connect(self._on_add)
        fl.addWidget(self._add_btn)

        self._edit_btn = _btn("Edit", ghost=True)
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit)
        fl.addWidget(self._edit_btn)

        self._delete_btn = _btn("Delete", color=_RED, text_color=_TEXT)
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete)
        fl.addWidget(self._delete_btn)

        self._copy_btn = _btn("Copy Password", ghost=True)
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._on_copy)
        fl.addWidget(self._copy_btn)

        fl.addStretch()

        hint = QLabel("Double-click row to copy password")
        hint.setStyleSheet(f"color: #444; font-size: 10px; background: transparent;")
        fl.addWidget(hint)

        close_btn = _btn("Close", ghost=True)
        close_btn.clicked.connect(self.accept)
        fl.addWidget(close_btn)

        return footer

    # ── Auto-lock ─────────────────────────────────────────────────────────────

    def _setup_timers(self):
        self._lock_timer = QTimer(self)
        self._lock_timer.setSingleShot(True)
        self._lock_timer.timeout.connect(self._auto_lock)
        self._lock_timer.start(self._AUTO_LOCK_MS)

        self._countdown = QTimer(self)
        self._countdown.timeout.connect(self._tick)
        self._countdown.start(1000)

    def _tick(self):
        self._remaining = max(0, self._remaining - 1)
        m, s = divmod(self._remaining, 60)
        color = _RED if self._remaining < 60 else _SILVER
        self._lock_label.setText(f"Auto-lock {m}:{s:02d}")
        self._lock_label.setStyleSheet(f"color: {color}; background: transparent; font-size: 9px;")

    def _reset_lock(self):
        self._remaining = self._AUTO_LOCK_MS // 1000
        self._lock_timer.start(self._AUTO_LOCK_MS)

    def _auto_lock(self):
        self._countdown.stop()
        self._table.setRowCount(0)
        logger.info("Vault auto-locked due to inactivity")
        self.reject()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.KeyPress, QEvent.Type.Wheel):
            self._reset_lock()
        return super().eventFilter(obj, event)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_entries(self):
        self._table.setRowCount(0)
        for entry in self._vault.list_entries():
            self._insert_row(entry['service'], entry['username'])

    def _insert_row(self, service: str, username: str):
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setRowHeight(row, 38)
        self._table.setItem(row, _COL_SERVICE,  QTableWidgetItem(service))
        self._table.setItem(row, _COL_USERNAME, QTableWidgetItem(username))
        self._table.setItem(row, _COL_PASSWORD, QTableWidgetItem("••••••••"))

    def _filter_table(self, text: str):
        text = text.lower()
        for row in range(self._table.rowCount()):
            service  = self._table.item(row, _COL_SERVICE).text().lower()
            username = self._table.item(row, _COL_USERNAME).text().lower()
            self._table.setRowHidden(row, text not in service and text not in username)

    def _selected_row(self) -> int:
        rows = self._table.selectedItems()
        return rows[0].row() if rows else -1

    def _row_data(self, row: int) -> tuple:
        return (
            self._table.item(row, _COL_SERVICE).text(),
            self._table.item(row, _COL_USERNAME).text(),
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_selection_changed(self):
        has = self._selected_row() >= 0
        self._edit_btn.setEnabled(has)
        self._delete_btn.setEnabled(has)
        self._copy_btn.setEnabled(has)

    def _on_double_click(self, index):
        self._copy_password(index.row())

    def _copy_password(self, row: int):
        service, username = self._row_data(row)
        entry = self._vault.get_password(service, username)
        if entry:
            QGuiApplication.clipboard().setText(entry['password'])
            logger.info(f"Password copied: {service}/{username}")

    def _on_copy(self):
        row = self._selected_row()
        if row >= 0:
            self._copy_password(row)

    def _on_add(self):
        dlg = _EntryDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        v = dlg.values()
        if self._vault.add_password(v['service'], v['username'], v['password'], v['notes']):
            self._insert_row(v['service'], v['username'])

    def _on_edit(self):
        row = self._selected_row()
        if row < 0:
            return
        service, username = self._row_data(row)
        entry = self._vault.get_password(service, username)
        if not entry:
            return
        dlg = _EntryDialog(self, service=service, username=username,
                           password=entry['password'], notes=entry.get('notes', ''))
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        v = dlg.values()
        self._vault.add_password(v['service'], v['username'], v['password'], v['notes'])

    def _on_delete(self):
        row = self._selected_row()
        if row < 0:
            return
        service, username = self._row_data(row)

        confirm = QDialog(self)
        confirm.setWindowTitle("Confirm Delete")
        confirm.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        confirm.setModal(True)
        confirm.setFixedSize(340, 150)
        confirm.setStyleSheet(f"background-color: {_BG}; border: 1px solid {_RED};")
        cl = QVBoxLayout(confirm)
        cl.setContentsMargins(20, 16, 20, 16)
        msg = QLabel(f"Delete <b>{service}</b> / {username}?")
        msg.setStyleSheet(f"color: {_TEXT}; font-size: 13px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(msg)
        cl.addStretch()
        br = QHBoxLayout()
        br.setSpacing(8)
        cancel = _btn("Cancel", ghost=True)
        cancel.clicked.connect(confirm.reject)
        delete = _btn("Delete", color=_RED, text_color=_TEXT)
        delete.clicked.connect(confirm.accept)
        br.addWidget(cancel)
        br.addWidget(delete)
        cl.addLayout(br)

        if confirm.exec() != QDialog.DialogCode.Accepted:
            return
        if self._vault.delete_password(service, username):
            self._table.removeRow(row)


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    from ui.password_unlock_dialog import PasswordUnlockDialog

    app = QApplication(sys.argv)
    unlock = PasswordUnlockDialog()
    if unlock.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)
    manager = PasswordManagerDialog(unlock.get_vault())
    manager.exec()
    sys.exit(0)
