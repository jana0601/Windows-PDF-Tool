from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QGroupBox, QPushButton, QVBoxLayout, QWidget


class AnnotatePanel(QGroupBox):
    toolSelected = Signal(str)
    colorSelected = Signal(tuple)
    undoClicked = Signal()
    redoClicked = Signal()
    clearClicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Annotate", parent)
        layout = QVBoxLayout(self)

        for label, tool in [
            ("View", "view"),
            ("Freehand", "freehand"),
            ("Rectangle", "rect"),
            ("Text Note", "text"),
            ("Blackout", "blackout"),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, t=tool: self.toolSelected.emit(t))
            layout.addWidget(btn)

        self.color_btn = QPushButton("Pick Color")
        self.color_btn.clicked.connect(self._pick_color)
        layout.addWidget(self.color_btn)

        undo_btn = QPushButton("Undo")
        redo_btn = QPushButton("Redo")
        clear_btn = QPushButton("Clear Annotations")
        undo_btn.clicked.connect(self.undoClicked.emit)
        redo_btn.clicked.connect(self.redoClicked.emit)
        clear_btn.clicked.connect(self.clearClicked.emit)
        layout.addWidget(undo_btn)
        layout.addWidget(redo_btn)
        layout.addWidget(clear_btn)
        layout.addStretch(1)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(parent=self)
        if not color.isValid():
            return
        rgb = (color.red(), color.green(), color.blue())
        self.color_btn.setStyleSheet(
            f"background-color: rgb({rgb[0]}, {rgb[1]}, {rgb[2]});"
            f"color: {'white' if color.lightness() < 128 else 'black'};"
        )
        self.colorSelected.emit(rgb)
