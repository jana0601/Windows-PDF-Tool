from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
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
    rotatePagesRequested = Signal(str, int)
    reorderPagesRequested = Signal(str)

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

        layout.addWidget(QLabel("Rotate pages (e.g. 1,3-5):"))
        rotate_row = QHBoxLayout()
        self.rotate_pages_edit = QLineEdit()
        self.rotate_pages_edit.setPlaceholderText("1,3-5")
        self.rotate_angle = QComboBox()
        self.rotate_angle.addItems(["90", "180", "270"])
        rotate_btn = QPushButton("Rotate")
        rotate_btn.clicked.connect(
            lambda: self.rotatePagesRequested.emit(
                self.rotate_pages_edit.text().strip(),
                int(self.rotate_angle.currentText()),
            )
        )
        rotate_row.addWidget(self.rotate_pages_edit)
        rotate_row.addWidget(self.rotate_angle)
        rotate_row.addWidget(rotate_btn)
        layout.addLayout(rotate_row)

        layout.addWidget(QLabel("Reorder pages (full order, e.g. 3,1,2,4):"))
        reorder_row = QHBoxLayout()
        self.reorder_edit = QLineEdit()
        self.reorder_edit.setPlaceholderText("3,1,2,4")
        reorder_btn = QPushButton("Reorder")
        reorder_btn.clicked.connect(lambda: self.reorderPagesRequested.emit(self.reorder_edit.text().strip()))
        reorder_row.addWidget(self.reorder_edit)
        reorder_row.addWidget(reorder_btn)
        layout.addLayout(reorder_row)
        layout.addStretch(1)

    def set_preview_text(self, text: str) -> None:
        self.preview.setPlainText(text)
