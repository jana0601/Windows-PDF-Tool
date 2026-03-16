from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MergePanel(QGroupBox):
    addFilesRequested = Signal()
    clearFilesRequested = Signal()
    moveUpRequested = Signal()
    moveDownRequested = Signal()
    removeRequested = Signal()
    previewRequested = Signal()
    mergeRequested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Merge PDFs", parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Merge order (top to bottom):"))
        self.files_list = QListWidget()
        layout.addWidget(self.files_list)

        row = QHBoxLayout()
        add_btn = QPushButton("Add Files")
        clear_btn = QPushButton("Clear")
        up_btn = QPushButton("Up")
        down_btn = QPushButton("Down")
        remove_btn = QPushButton("Remove")
        preview_btn = QPushButton("Preview")
        merge_btn = QPushButton("Merge")
        add_btn.clicked.connect(self.addFilesRequested.emit)
        clear_btn.clicked.connect(self.clearFilesRequested.emit)
        up_btn.clicked.connect(self.moveUpRequested.emit)
        down_btn.clicked.connect(self.moveDownRequested.emit)
        remove_btn.clicked.connect(self.removeRequested.emit)
        preview_btn.clicked.connect(self.previewRequested.emit)
        merge_btn.clicked.connect(self.mergeRequested.emit)
        row.addWidget(add_btn)
        row.addWidget(clear_btn)
        row.addWidget(up_btn)
        row.addWidget(down_btn)
        row.addWidget(remove_btn)
        row.addWidget(preview_btn)
        row.addWidget(merge_btn)
        layout.addLayout(row)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Preview: combined page count, file order, and output summary.")
        layout.addWidget(self.preview)

    def set_files(self, files: list[str]) -> None:
        self.files_list.clear()
        self.files_list.addItems(files)

    def current_row(self) -> int:
        return self.files_list.currentRow()

    def set_preview_text(self, text: str) -> None:
        self.preview.setPlainText(text)
