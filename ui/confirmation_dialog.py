"""
Confirmation Dialog
UI component for confirming computer actions
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtGui import QFont

from config import COLORS
from logger import get_logger

logger = get_logger(__name__)


class ConfirmationDialog(QDialog):
    """
    Dialog for confirming computer actions.
    Shows action details and allows user to approve or deny.
    """
    
    # Signals
    confirmed = pyqtSignal()  # Emitted when user approves
    denied = pyqtSignal()     # Emitted when user denies
    
    def __init__(self, parent=None):
        """Initialize the confirmation dialog"""
        super().__init__(parent)
        
        self.setWindowTitle("Edward - Confirm Action")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        self._setup_ui()
        self._apply_styles()
        
        logger.info("Confirmation dialog initialized")
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Warning icon and title
        title_layout = QHBoxLayout()
        
        warning_label = QLabel("⚠️")
        warning_label.setFont(QFont("Segoe UI", 32))
        title_layout.addWidget(warning_label)
        
        title = QLabel("Action Confirmation Required")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Description
        self.description_label = QLabel()
        self.description_label.setFont(QFont("Segoe UI", 11))
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # Details section
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        
        details_title = QLabel("Action Details:")
        details_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        details_layout.addWidget(details_title)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setFont(QFont("Consolas", 9))
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_frame)
        
        # Warning message
        warning_text = QLabel(
            "⚠️ This action will modify your system. "
            "Please review carefully before proceeding."
        )
        warning_text.setFont(QFont("Segoe UI", 9))
        warning_text.setWordWrap(True)
        layout.addWidget(warning_text)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.deny_button = QPushButton("Deny")
        self.deny_button.setMinimumWidth(100)
        self.deny_button.setMinimumHeight(35)
        self.deny_button.clicked.connect(self._on_deny)
        button_layout.addWidget(self.deny_button)
        
        self.approve_button = QPushButton("Approve")
        self.approve_button.setMinimumWidth(100)
        self.approve_button.setMinimumHeight(35)
        self.approve_button.clicked.connect(self._on_approve)
        self.approve_button.setDefault(True)
        button_layout.addWidget(self.approve_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _apply_styles(self):
        """Apply dark theme styles"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['dark_bg']};
                color: {COLORS['text']};
            }}
            
            QLabel {{
                color: {COLORS['text']};
            }}
            
            QTextEdit {{
                background-color: {COLORS['input_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px;
            }}
            
            QFrame {{
                background-color: {COLORS['input_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            
            QPushButton {{
                background-color: {COLORS['button_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11pt;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {COLORS['button_hover']};
                border-color: {COLORS['gold']};
            }}
            
            QPushButton:pressed {{
                background-color: {COLORS['button_pressed']};
            }}
            
            QPushButton#approve {{
                background-color: #2d5016;
                border-color: #4a7c2c;
            }}
            
            QPushButton#approve:hover {{
                background-color: #3d6b1f;
                border-color: #5a9c3c;
            }}
            
            QPushButton#deny {{
                background-color: #5c1616;
                border-color: #8c2c2c;
            }}
            
            QPushButton#deny:hover {{
                background-color: #7c2626;
                border-color: #ac3c3c;
            }}
        """)
        
        self.approve_button.setObjectName("approve")
        self.deny_button.setObjectName("deny")
    
    def set_action(self, description: str, details: dict):
        """
        Set the action to confirm.
        
        Args:
            description: Human-readable description
            details: Dictionary of action parameters
        """
        self.description_label.setText(description)
        
        # Format details
        details_text = ""
        for key, value in details.items():
            # Truncate long values
            if isinstance(value, str) and len(value) > 200:
                value = value[:200] + "..."
            details_text += f"{key}: {value}\n"
        
        self.details_text.setPlainText(details_text.strip())
        
        logger.info(f"Confirmation dialog set: {description}")
    
    def _on_approve(self):
        """Handle approve button click"""
        logger.info("Action approved by user")
        self.confirmed.emit()
        self.accept()
    
    def _on_deny(self):
        """Handle deny button click"""
        logger.info("Action denied by user")
        self.denied.emit()
        self.reject()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self._on_deny()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self._on_approve()
        else:
            super().keyPressEvent(event)


# Example usage
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = ConfirmationDialog()
    dialog.set_action(
        "Create file 'test.txt' with 150 characters",
        {
            "file_path": "C:/Users/Jackson/Desktop/test.txt",
            "content": "Hello World!\nThis is a test file created by Edward.",
            "action_type": "create_file"
        }
    )
    
    def on_confirmed():
        print("✓ Action confirmed!")
    
    def on_denied():
        print("✗ Action denied!")
    
    dialog.confirmed.connect(on_confirmed)
    dialog.denied.connect(on_denied)
    
    dialog.exec()
    
    sys.exit(0)

# Made with Bob
