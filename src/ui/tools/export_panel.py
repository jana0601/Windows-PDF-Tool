from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ExportPanel(QGroupBox):
    exportRequested = Signal(str, int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("PDF to Image", parent)
        layout = QVBoxLayout(self)

        self.format_box = QComboBox()
        self.format_box.addItems(["png", "jpg"])
        self.dpi_box = QSpinBox()
        self.dpi_box.setRange(72, 600)
        self.dpi_box.setValue(150)
        self.pages_edit = QLineEdit()
        self.pages_edit.setPlaceholderText("All pages or 1,3-5")

        layout.addWidget(QLabel("Image format"))
        layout.addWidget(self.format_box)
        layout.addWidget(QLabel("DPI"))
        layout.addWidget(self.dpi_box)
        layout.addWidget(QLabel("Pages"))
        layout.addWidget(self.pages_edit)

        row = QHBoxLayout()
        btn = QPushButton("Export Images")
        btn.clicked.connect(
            lambda: self.exportRequested.emit(
                self.format_box.currentText(),
                self.dpi_box.value(),
                self.pages_edit.text().strip(),
            )
        )
        row.addWidget(btn)
        layout.addLayout(row)
        layout.addStretch(1)
