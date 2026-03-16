from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class CompressPanel(QGroupBox):
    compressRequested = Signal(int, int, bool)
    previewRequested = Signal(int, int, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Compress PDF", parent)
        layout = QVBoxLayout(self)
        self.dpi = QSpinBox()
        self.dpi.setRange(72, 600)
        self.dpi.setValue(150)
        self.quality = QSpinBox()
        self.quality.setRange(20, 100)
        self.quality.setValue(75)
        self.grayscale = QCheckBox("Convert color to grayscale")
        run_btn = QPushButton("Compress Current PDF")
        preview_btn = QPushButton("Preview Compression")
        run_btn.clicked.connect(
            lambda: self.compressRequested.emit(
                int(self.dpi.value()),
                int(self.quality.value()),
                self.grayscale.isChecked(),
            )
        )
        preview_btn.clicked.connect(
            lambda: self.previewRequested.emit(
                int(self.dpi.value()),
                int(self.quality.value()),
                self.grayscale.isChecked(),
            )
        )
        layout.addWidget(QLabel("DPI"))
        layout.addWidget(self.dpi)
        layout.addWidget(QLabel("JPEG quality"))
        layout.addWidget(self.quality)
        layout.addWidget(self.grayscale)
        layout.addWidget(preview_btn)
        layout.addWidget(run_btn)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Preview: estimated output size for selected DPI/quality.")
        layout.addWidget(self.preview)
        layout.addStretch(1)

    def set_preview_text(self, text: str) -> None:
        self.preview.setPlainText(text)
