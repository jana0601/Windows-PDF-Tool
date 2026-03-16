from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class PageOpsPanel(QGroupBox):
    deletePagesRequested = Signal(str)
    previewRequested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Page Operations", parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Pages to delete (e.g. 2,4-6):"))
        row = QHBoxLayout()
        self.pages_edit = QLineEdit()
        self.pages_edit.setPlaceholderText("1,3-5")
        preview_btn = QPushButton("Preview")
        btn = QPushButton("Delete Pages")
        preview_btn.clicked.connect(lambda: self.previewRequested.emit(self.pages_edit.text().strip()))
        btn.clicked.connect(lambda: self.deletePagesRequested.emit(self.pages_edit.text().strip()))
        row.addWidget(self.pages_edit)
        row.addWidget(preview_btn)
        row.addWidget(btn)
        layout.addLayout(row)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Preview: pages to delete and remaining pages.")
        layout.addWidget(self.preview)
        layout.addStretch(1)

    def set_preview_text(self, text: str) -> None:
        self.preview.setPlainText(text)
