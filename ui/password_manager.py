"""Main password manager UI — credential list with add/edit/delete/copy"""

import sys
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QCheckBox, QFormLayout,
    QWidget
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QFont, QGuiApplication

from vault import PasswordVault
from config import COLORS
from logger import get_logger

logger = get_logger(__name__)

_COL_SERVICE  = 0
_COL_USERNAME = 1
_COL_PASSWORD = 2

_PANEL_STYLE = f"background-color: {COLORS['panel']};"
_TEXT_STYLE  = f"color: {COLORS['text']}; font-size: 13px;"


def _input_style(focus_color: str = COLORS['gold']) -> str:
    return f"""
        QLineEdit {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            border: 2px solid {COLORS['silver']};
            border-radius: 5px;
            padding: 7px 10px;
            font-size: 13px;
        }}
        QLineEdit:focus {{ border-color: {focus_color}; }}
    """


def _primary_btn(color: str = COLORS['gold']) -> str:
    return f"""
        QPushButton {{
            background-color: {color};
            color: {COLORS['background'] if color == COLORS['gold'] else COLORS['text']};
            border: none; border-radius: 5px;
            padding: 7px 14px; font-size: 12px; font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {'#E5B52E' if color == COLORS['gold'] else '#CC2222'}; }}
        QPushButton:disabled {{ background-color: #444; color: #777; }}
    """


def _ghost_btn() -> str:
    return f"""
        QPushButton {{
            background-color: {COLORS['background']};
            color: {COLORS['silver']};
            border: 1px solid {COLORS['silver']};
            border-radius: 5px;
            padding: 7px 14px; font-size: 12px;
        }}
        QPushButton:hover {{ background-color: #2A2A2A; }}
    """


# ── Add / Edit sub-dialog ─────────────────────────────────────────────────────

class _EntryDialog(QDialog):
    """Shared dialog for adding and editing a vault entry."""

    def __init__(self, parent=None, service: str = "", username: str = "",
                 password: str = "", notes: str = ""):
        super().__init__(parent)
        self._initial = dict(service=service, username=username,
                             password=password, notes=notes)
        self._setup_window(editing=bool(service))
        self._setup_ui()
        self._populate()

    def _setup_window(self, editing: bool):
        self.setWindowTitle("Edit Entry" if editing else "Add Entry")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setStyleSheet(_PANEL_STYLE)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        lbl_style = f"color: {COLORS['silver']}; font-size: 12px;"

        def make_label(text):
            l = QLabel(text)
            l.setStyleSheet(lbl_style)
            return l

        self._service_field = QLineEdit()
        self._service_field.setStyleSheet(_input_style())
        self._service_field.setPlaceholderText("e.g. Gmail")
        form.addRow(make_label("Service"), self._service_field)

        self._username_field = QLineEdit()
        self._username_field.setStyleSheet(_input_style())
        self._username_field.setPlaceholderText("e.g. user@example.com")
        form.addRow(make_label("Username"), self._username_field)

        # Password row with show/hide toggle
        pw_row = QWidget()
        pw_h = QHBoxLayout(pw_row)
        pw_h.setContentsMargins(0, 0, 0, 0)
        pw_h.setSpacing(6)

        self._pw_field = QLineEdit()
        self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw_field.setStyleSheet(_input_style())
        pw_h.addWidget(self._pw_field)

        self._show_btn = QPushButton("Show")
        self._show_btn.setFixedWidth(50)
        self._show_btn.setFont(QFont("Segoe UI", 9))
        self._show_btn.setStyleSheet(_ghost_btn())
        self._show_btn.clicked.connect(self._toggle_echo)
        pw_h.addWidget(self._show_btn)

        form.addRow(make_label("Password"), pw_row)

        self._notes_field = QLineEdit()
        self._notes_field.setStyleSheet(_input_style(COLORS['silver']))
        self._notes_field.setPlaceholderText("Optional notes")
        form.addRow(make_label("Notes"), self._notes_field)

        layout.addLayout(form)
        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel = QPushButton("Cancel")
        cancel.setFont(QFont("Segoe UI", 11))
        cancel.setMinimumHeight(38)
        cancel.setStyleSheet(_ghost_btn())
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)

        save = QPushButton("Save")
        save.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        save.setMinimumHeight(38)
        save.setStyleSheet(_primary_btn())
        save.clicked.connect(self._on_save)
        btn_row.addWidget(save)

        layout.addLayout(btn_row)

    def _populate(self):
        self._service_field.setText(self._initial['service'])
        self._username_field.setText(self._initial['username'])
        self._pw_field.setText(self._initial['password'])
        self._notes_field.setText(self._initial['notes'])
        if self._initial['service']:
            self._service_field.setReadOnly(True)
            self._username_field.setReadOnly(True)

    def _toggle_echo(self):
        if self._pw_field.echoMode() == QLineEdit.EchoMode.Password:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_btn.setText("Hide")
        else:
            self._pw_field.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_btn.setText("Show")

    def _on_save(self):
        if not self._service_field.text().strip():
            self._service_field.setFocus()
            return
        if not self._username_field.text().strip():
            self._username_field.setFocus()
            return
        if not self._pw_field.text():
            self._pw_field.setFocus()
            return
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
    """
    Full-featured credential list.
    Requires an already-unlocked PasswordVault instance.
    """

    def __init__(self, vault: PasswordVault, parent=None):
        super().__init__(parent)
        self._vault = vault
        self._setup_window()
        self._setup_ui()
        self._load_entries()

    # ── Window ────────────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("Edward — Password Vault")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.resize(620, 480)
        self.setStyleSheet(_PANEL_STYLE)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header
        title = QLabel("Password Vault")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['gold']};")
        layout.addWidget(title)

        # Search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by service or username…")
        self._search.setFont(QFont("Segoe UI", 11))
        self._search.setStyleSheet(_input_style(COLORS['silver']))
        self._search.textChanged.connect(self._filter_table)
        layout.addWidget(self._search)

        # Table
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Service", "Username", "Password"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 100)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                gridline-color: #2A2A2A;
                border: 1px solid {COLORS['silver']};
                border-radius: 5px;
                font-size: 12px;
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['gold']};
                color: {COLORS['background']};
            }}
            QTableWidget::item:alternate {{
                background-color: #161616;
            }}
            QHeaderView::section {{
                background-color: {COLORS['panel']};
                color: {COLORS['silver']};
                border: none;
                padding: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(self._table, stretch=1)

        # Double-click hint
        hint = QLabel("Double-click a row to copy the password to clipboard")
        hint.setStyleSheet(f"color: {COLORS['silver']}; font-size: 11px;")
        layout.addWidget(hint)

        # Button bar
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._add_btn = QPushButton("Add")
        self._add_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._add_btn.setMinimumHeight(38)
        self._add_btn.setStyleSheet(_primary_btn())
        self._add_btn.clicked.connect(self._on_add)
        btn_row.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setFont(QFont("Segoe UI", 11))
        self._edit_btn.setMinimumHeight(38)
        self._edit_btn.setEnabled(False)
        self._edit_btn.setStyleSheet(_ghost_btn())
        self._edit_btn.clicked.connect(self._on_edit)
        btn_row.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setFont(QFont("Segoe UI", 11))
        self._delete_btn.setMinimumHeight(38)
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet(_primary_btn(COLORS['red']))
        self._delete_btn.clicked.connect(self._on_delete)
        btn_row.addWidget(self._delete_btn)

        self._copy_btn = QPushButton("Copy Password")
        self._copy_btn.setFont(QFont("Segoe UI", 11))
        self._copy_btn.setMinimumHeight(38)
        self._copy_btn.setEnabled(False)
        self._copy_btn.setStyleSheet(_ghost_btn())
        self._copy_btn.clicked.connect(self._on_copy)
        btn_row.addWidget(self._copy_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFont(QFont("Segoe UI", 11))
        close_btn.setMinimumHeight(38)
        close_btn.setStyleSheet(_ghost_btn())
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_entries(self):
        self._table.setRowCount(0)
        for entry in self._vault.list_entries():
            self._insert_row(entry['service'], entry['username'])

    def _insert_row(self, service: str, username: str):
        row = self._table.rowCount()
        self._table.insertRow(row)
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

    # ── Slot handlers ─────────────────────────────────────────────────────────

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
            logger.info(f"Password copied for {service}/{username}")

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
            logger.info(f"Entry added: {v['service']}/{v['username']}")

    def _on_edit(self):
        row = self._selected_row()
        if row < 0:
            return
        service, username = self._row_data(row)
        entry = self._vault.get_password(service, username)
        if not entry:
            return
        dlg = _EntryDialog(self,
                           service=service, username=username,
                           password=entry['password'], notes=entry.get('notes', ''))
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        v = dlg.values()
        self._vault.add_password(v['service'], v['username'], v['password'], v['notes'])
        logger.info(f"Entry updated: {service}/{username}")

    def _on_delete(self):
        row = self._selected_row()
        if row < 0:
            return
        service, username = self._row_data(row)
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Delete Entry")
        confirm.setText(f"Delete {service} / {username}?")
        confirm.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        confirm.setDefaultButton(QMessageBox.StandardButton.Cancel)
        confirm.setStyleSheet(_PANEL_STYLE + f" color: {COLORS['text']};")
        if confirm.exec() != QMessageBox.StandardButton.Yes:
            return
        if self._vault.delete_password(service, username):
            self._table.removeRow(row)
            logger.info(f"Entry deleted: {service}/{username}")


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    from ui.password_unlock_dialog import PasswordUnlockDialog

    app = QApplication(sys.argv)

    unlock = PasswordUnlockDialog()
    if unlock.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    vault = unlock.get_vault()
    manager = PasswordManagerDialog(vault)
    manager.exec()
    sys.exit(0)
