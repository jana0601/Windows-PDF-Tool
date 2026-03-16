from __future__ import annotations

from typing import Any

import pymupdf as fitz
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QImage, QMouseEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QScrollArea, QWidget

from src.models.document_state import DocumentState


class PdfCanvas(QScrollArea):
    pageChanged = Signal(int, int)
    statusChanged = Signal(str)
    actionStateChanged = Signal(bool, bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = DocumentState()
        self._tool = "view"
        self._pen_width = 2.0
        self._draw_color = (255, 0, 0)
        self._text_note_text = "Note"
        self._text_note_size = 12.0
        self._start_px = QPoint()
        self._current_points: list[tuple[float, float]] = []
        self._dragging = False
        self._moving_text = False
        self._moving_text_action_idx: int | None = None
        self._moving_text_offset = (0.0, 0.0)
        self._preview_rect: tuple[float, float, float, float] | None = None
        self._preview_action: dict[str, Any] | None = None

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMouseTracking(True)
        self._label.installEventFilter(self)

        self.setWidget(self._label)
        self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def load_pdf(self, file_path: str) -> None:
        if self.state.document is not None:
            self.state.document.close()
        self.state.document = fitz.open(file_path)
        self.state.file_path = file_path
        self.state.current_page = 0
        self.state.zoom = 1.0
        self.state.reset_actions()
        self.render_page()

    def close_document(self) -> None:
        if self.state.document is not None:
            self.state.document.close()
        self.state = DocumentState()
        self._label.clear()
        self.actionStateChanged.emit(False, False)

    def set_tool(self, tool: str) -> None:
        self._tool = tool
        self.statusChanged.emit(f"Tool: {tool}")

    def set_draw_color(self, rgb: tuple[int, int, int]) -> None:
        self._draw_color = rgb
        self.statusChanged.emit(f"Color: rgb{rgb}")

    def set_text_note_template(self, text: str, size: float) -> None:
        self._text_note_text = text
        self._text_note_size = max(6.0, min(144.0, size))

    def set_zoom(self, zoom: float) -> None:
        self.state.zoom = max(0.25, min(5.0, zoom))
        self.render_page()

    def zoom_in(self) -> None:
        self.set_zoom(self.state.zoom * 1.2)

    def zoom_out(self) -> None:
        self.set_zoom(self.state.zoom / 1.2)

    def next_page(self) -> None:
        if not self.state.has_document:
            return
        if self.state.current_page + 1 < self.state.document.page_count:
            self.state.current_page += 1
            self.render_page()

    def prev_page(self) -> None:
        if not self.state.has_document:
            return
        if self.state.current_page > 0:
            self.state.current_page -= 1
            self.render_page()

    def goto_page(self, one_based: int) -> None:
        if not self.state.has_document:
            return
        idx = one_based - 1
        if 0 <= idx < self.state.document.page_count:
            self.state.current_page = idx
            self.render_page()

    def can_undo(self) -> bool:
        return len(self.state.actions) > 0

    def can_redo(self) -> bool:
        return len(self.state.redo_actions) > 0

    def undo(self) -> None:
        if not self.state.actions:
            return
        self.state.redo_actions.append(self.state.actions.pop())
        self.render_page()
        self.actionStateChanged.emit(self.can_undo(), self.can_redo())

    def redo(self) -> None:
        if not self.state.redo_actions:
            return
        self.state.actions.append(self.state.redo_actions.pop())
        self.render_page()
        self.actionStateChanged.emit(self.can_undo(), self.can_redo())

    def get_actions(self) -> list[dict[str, Any]]:
        return list(self.state.actions)

    def clear_actions(self) -> None:
        self.state.reset_actions()
        self.render_page()
        self.actionStateChanged.emit(False, False)

    def set_page_count_override(self, page_count: int) -> None:
        if not self.state.has_document:
            return
        if page_count <= 0:
            self.close_document()
            return
        self.state.current_page = min(self.state.current_page, page_count - 1)
        self.render_page()

    def render_page(self) -> None:
        if not self.state.has_document:
            self._label.clear()
            return
        page = self.state.document[self.state.current_page]
        matrix = fitz.Matrix(self.state.zoom, self.state.zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        qimage = QImage(
            pix.samples,
            pix.width,
            pix.height,
            pix.stride,
            QImage.Format.Format_RGB888,
        ).copy()
        canvas = QPixmap.fromImage(qimage)
        painter = QPainter(canvas)
        self._draw_actions_for_page(painter, self.state.current_page)
        if self._preview_action and self._preview_action.get("page") == self.state.current_page:
            self._draw_action(painter, self._preview_action)
        painter.end()
        self._label.setPixmap(canvas)
        self._label.resize(canvas.size())
        self.pageChanged.emit(self.state.current_page + 1, self.state.document.page_count)
        self.actionStateChanged.emit(self.can_undo(), self.can_redo())

    def _draw_actions_for_page(self, painter: QPainter, page_idx: int) -> None:
        for action in self.state.actions:
            if action.get("page") == page_idx:
                self._draw_action(painter, action)

    def _draw_action(self, painter: QPainter, action: dict[str, Any]) -> None:
        t = action.get("type")
        zoom = self.state.zoom
        color = action.get("color", (255, 0, 0))
        width = int(action.get("width", 2))
        if isinstance(color[0], float):
            color = tuple(int(c * 255) for c in color)
        pen = QPen(QColor(color[0], color[1], color[2]))
        pen.setColor(Qt.GlobalColor.black if t == "blackout" else QColor(color[0], color[1], color[2]))
        pen.setWidth(width)
        painter.setPen(pen)

        if t == "freehand":
            points = action.get("points", [])
            for p0, p1 in zip(points[:-1], points[1:]):
                painter.drawLine(QPointF(p0[0] * zoom, p0[1] * zoom), QPointF(p1[0] * zoom, p1[1] * zoom))
        elif t in {"rect", "blackout"}:
            x0, y0, x1, y1 = action["rect"]
            x0, y0, x1, y1 = x0 * zoom, y0 * zoom, x1 * zoom, y1 * zoom
            if t == "blackout":
                painter.fillRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0), Qt.GlobalColor.black)
            painter.drawRect(int(x0), int(y0), int(x1 - x0), int(y1 - y0))
        elif t == "text":
            x, y = action["point"]
            size = float(action.get("size", 12.0))
            font = QFont(painter.font())
            font.setPointSizeF(max(1.0, size * zoom))
            painter.setFont(font)
            painter.drawText(int(x * zoom), int(y * zoom), action.get("text", ""))

    def _to_doc_space(self, px: QPoint) -> tuple[float, float]:
        pix = self._label.pixmap()
        if pix is None:
            return px.x() / self.state.zoom, px.y() / self.state.zoom
        offset_x = max(0, (self._label.width() - pix.width()) // 2)
        offset_y = max(0, (self._label.height() - pix.height()) // 2)
        canvas_x = min(max(0, px.x() - offset_x), pix.width())
        canvas_y = min(max(0, px.y() - offset_y), pix.height())
        return canvas_x / self.state.zoom, canvas_y / self.state.zoom

    def eventFilter(self, obj: object, event: object) -> bool:
        if obj is self._label and isinstance(event, QMouseEvent) and self.state.has_document:
            if event.type() == QEvent.Type.MouseButtonPress:
                return self._on_press(event)
            if event.type() == QEvent.Type.MouseMove:
                return self._on_move(event)
            if event.type() == QEvent.Type.MouseButtonRelease:
                return self._on_release(event)
        return super().eventFilter(obj, event)

    def _on_press(self, event: QMouseEvent) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False
        if self._tool in {"view", "text"}:
            hit_idx = self._hit_test_text_action(event.position().toPoint())
            if hit_idx is not None:
                self._moving_text = True
                self._moving_text_action_idx = hit_idx
                action = self.state.actions[hit_idx]
                px = self._to_doc_space(event.position().toPoint())
                ax, ay = action["point"]
                self._moving_text_offset = (px[0] - ax, px[1] - ay)
                return True

        if self._tool not in {"freehand", "rect", "blackout", "text"}:
            return False
        self._dragging = True
        self._start_px = event.position().toPoint()
        self._preview_action = None
        if self._tool == "freehand":
            self._current_points = [self._to_doc_space(self._start_px)]
        elif self._tool == "text":
            note = self._text_note_text.strip()
            if note:
                point = self._to_doc_space(self._start_px)
                self._push_action(
                    {
                        "type": "text",
                        "page": self.state.current_page,
                        "point": point,
                        "text": note,
                        "color": tuple(c / 255.0 for c in self._draw_color),
                        "size": self._text_note_size,
                    }
                )
            self._dragging = False
            self.render_page()
        return True

    def _on_move(self, event: QMouseEvent) -> bool:
        if self._moving_text and self._moving_text_action_idx is not None:
            if 0 <= self._moving_text_action_idx < len(self.state.actions):
                action = self.state.actions[self._moving_text_action_idx]
                px = self._to_doc_space(event.position().toPoint())
                ox, oy = self._moving_text_offset
                action["point"] = (px[0] - ox, px[1] - oy)
                self.render_page()
            return True

        if not self._dragging:
            return False
        if self._tool == "freehand":
            self._current_points.append(self._to_doc_space(event.position().toPoint()))
            self._preview_action = {
                "type": "freehand",
                "page": self.state.current_page,
                "points": self._current_points,
                "color": tuple(c / 255.0 for c in self._draw_color),
                "width": self._pen_width,
            }
        elif self._tool in {"rect", "blackout"}:
            x0, y0 = self._to_doc_space(self._start_px)
            x1, y1 = self._to_doc_space(event.position().toPoint())
            self._preview_rect = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
            self._preview_action = {
                "type": self._tool,
                "page": self.state.current_page,
                "rect": self._preview_rect,
                "color": tuple(c / 255.0 for c in self._draw_color) if self._tool == "rect" else (0, 0, 0),
                "fill": (0, 0, 0),
                "width": self._pen_width,
            }
        self.render_page()
        return True

    def _on_release(self, event: QMouseEvent) -> bool:
        if self._moving_text:
            self._moving_text = False
            self._moving_text_action_idx = None
            self._moving_text_offset = (0.0, 0.0)
            self.render_page()
            return True

        if event.button() != Qt.MouseButton.LeftButton or not self._dragging:
            return False
        if self._tool == "freehand" and len(self._current_points) >= 2:
            self._push_action(
                {
                    "type": "freehand",
                    "page": self.state.current_page,
                    "points": self._current_points[:],
                    "color": tuple(c / 255.0 for c in self._draw_color),
                    "width": self._pen_width,
                }
            )
        elif self._tool in {"rect", "blackout"} and self._preview_rect:
            self._push_action(
                {
                    "type": self._tool,
                    "page": self.state.current_page,
                    "rect": self._preview_rect,
                    "color": tuple(c / 255.0 for c in self._draw_color) if self._tool == "rect" else (0, 0, 0),
                    "fill": (0, 0, 0),
                    "width": self._pen_width,
                }
            )
        self._dragging = False
        self._preview_rect = None
        self._preview_action = None
        self.render_page()
        return True

    def _push_action(self, action: dict[str, Any]) -> None:
        self.state.actions.append(action)
        self.state.redo_actions.clear()
        self.actionStateChanged.emit(self.can_undo(), self.can_redo())

    def _hit_test_text_action(self, px: QPoint) -> int | None:
        doc_x, doc_y = self._to_doc_space(px)
        for idx in range(len(self.state.actions) - 1, -1, -1):
            action = self.state.actions[idx]
            if action.get("type") != "text":
                continue
            if action.get("page") != self.state.current_page:
                continue
            text = str(action.get("text", ""))
            if not text:
                continue
            size = float(action.get("size", 12.0))
            font = QFont()
            font.setPointSizeF(max(1.0, size))
            metrics = QFontMetricsF(font)
            width = metrics.horizontalAdvance(text)
            height = metrics.height()
            x, y = action.get("point", (0.0, 0.0))
            # insert_text uses baseline y; convert to top-left box for hit testing.
            top = y - height
            if x <= doc_x <= x + width and top <= doc_y <= y:
                return idx
        return None
