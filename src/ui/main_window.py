from __future__ import annotations

from pathlib import Path
import tempfile

import pymupdf as fitz
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.pdf_compress_service import compress_pdf, preview_compress
from src.services.pdf_edit_service import default_output_path, save_deleted_pages, save_with_actions
from src.services.pdf_export_service import export_pdf_to_images
from src.services.pdf_merge_service import merge_pdfs
from src.ui.pdf_canvas import PdfCanvas
from src.ui.tools.annotate_panel import AnnotatePanel
from src.ui.tools.compress_panel import CompressPanel
from src.ui.tools.export_panel import ExportPanel
from src.ui.tools.merge_panel import MergePanel
from src.ui.tools.page_ops_panel import PageOpsPanel
from src.utils.file_dialogs import pick_output_folder, pick_pdf, pick_pdfs, save_pdf_as


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Windows PDF Tool")
        self.resize(1280, 820)

        self.merge_files: list[str] = []
        self._main_splitter: QSplitter | None = None

        self.canvas = PdfCanvas(self)
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        self.page_label = QLabel("Page: 0/0")
        self.status.addPermanentWidget(self.page_label)

        self.annotate_panel = AnnotatePanel()
        self.page_panel = PageOpsPanel()
        self.merge_panel = MergePanel()
        self.compress_panel = CompressPanel()
        self.export_panel = ExportPanel()

        self._build_ui()
        self._wire_events()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        tabs = QTabWidget()
        tabs.addTab(self.annotate_panel, "Annotate")
        tabs.addTab(self.page_panel, "Pages")
        tabs.addTab(self.merge_panel, "Merge")
        tabs.addTab(self.compress_panel, "Compress")
        tabs.addTab(self.export_panel, "Export")
        left_layout.addWidget(tabs)

        self.open_btn = QPushButton("Open PDF")
        self.save_btn = QPushButton("Save As")
        left_layout.addWidget(self.open_btn)
        left_layout.addWidget(self.save_btn)

        nav = QWidget()
        nav_layout = QHBoxLayout(nav)
        self.prev_btn = QPushButton("< Prev")
        self.next_btn = QPushButton("Next >")
        self.zoom_out_btn = QPushButton("-")
        self.zoom_in_btn = QPushButton("+")
        self.page_edit = QLineEdit()
        self.page_edit.setPlaceholderText("Page #")
        self.goto_btn = QPushButton("Go")
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(QLabel("Zoom"))
        nav_layout.addWidget(self.zoom_out_btn)
        nav_layout.addWidget(self.zoom_in_btn)
        nav_layout.addWidget(self.page_edit)
        nav_layout.addWidget(self.goto_btn)
        nav_layout.addStretch(1)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.addWidget(nav)
        center_layout.addWidget(self.canvas)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self._main_splitter = splitter
        root_layout.addWidget(splitter)
        QTimer.singleShot(0, self._apply_initial_splitter_sizes)

    def _wire_events(self) -> None:
        self.open_btn.clicked.connect(self.open_pdf)
        self.save_btn.clicked.connect(self.save_as)
        self.prev_btn.clicked.connect(self.canvas.prev_page)
        self.next_btn.clicked.connect(self.canvas.next_page)
        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        self.goto_btn.clicked.connect(self.goto_page)
        self.canvas.pageChanged.connect(self._on_page_changed)
        self.canvas.statusChanged.connect(self.status.showMessage)

        self.annotate_panel.toolSelected.connect(self.select_annotate_tool)
        self.annotate_panel.colorSelected.connect(self.canvas.set_draw_color)
        self.annotate_panel.undoClicked.connect(self.canvas.undo)
        self.annotate_panel.redoClicked.connect(self.canvas.redo)
        self.annotate_panel.clearClicked.connect(self.canvas.clear_actions)

        self.page_panel.deletePagesRequested.connect(self.delete_pages)
        self.page_panel.previewRequested.connect(self.preview_page_delete)

        self.merge_panel.addFilesRequested.connect(self.add_merge_files)
        self.merge_panel.clearFilesRequested.connect(self.clear_merge_files)
        self.merge_panel.moveUpRequested.connect(self.move_merge_file_up)
        self.merge_panel.moveDownRequested.connect(self.move_merge_file_down)
        self.merge_panel.removeRequested.connect(self.remove_merge_file)
        self.merge_panel.previewRequested.connect(self.preview_merge_files)
        self.merge_panel.mergeRequested.connect(self.merge_pdf_files)

        self.compress_panel.compressRequested.connect(self.compress_current_pdf)
        self.compress_panel.previewRequested.connect(self.preview_compress_current_pdf)
        self.export_panel.exportRequested.connect(self.export_images)

    def open_pdf(self) -> None:
        path = pick_pdf(self)
        if not path:
            return
        try:
            self.canvas.load_pdf(path)
            self.status.showMessage(f"Opened: {path}", 4000)
        except Exception as exc:
            self._error(f"Failed to open PDF:\n{exc}")

    def select_annotate_tool(self, tool: str) -> None:
        if tool != "text":
            self.canvas.set_tool(tool)
            return
        text, ok = QInputDialog.getText(self, "Text note", "Enter note text:")
        if not ok or not text.strip():
            return
        size, ok = QInputDialog.getDouble(self, "Font size", "Font size:", 12.0, 6.0, 144.0, 1)
        if not ok:
            return
        self.canvas.set_text_note_template(text.strip(), size)
        self.canvas.set_tool("text")

    def save_as(self) -> None:
        state = self.canvas.state
        if not state.file_path:
            self._error("Open a PDF before saving.")
            return
        default_path = default_output_path(state.file_path, "edited")
        output = save_pdf_as(self, "Save edited PDF", default_path)
        if not output:
            return
        if Path(output).exists() and not self._confirm("Output exists. Overwrite?"):
            return
        try:
            save_with_actions(state.file_path, output, self.canvas.get_actions())
            self.status.showMessage(f"Saved: {output}", 5000)
        except Exception as exc:
            self._error(f"Failed to save PDF:\n{exc}")

    def goto_page(self) -> None:
        text = self.page_edit.text().strip()
        if not text.isdigit():
            return
        self.canvas.goto_page(int(text))

    def delete_pages(self, page_range_text: str) -> None:
        state = self.canvas.state
        if not state.file_path:
            self._error("Open a PDF before deleting pages.")
            return
        pages = parse_page_range(page_range_text)
        if not pages:
            self._error("Enter pages to delete, e.g. 2,4-6")
            return
        if not self._confirm(f"Delete pages: {pages}? This action creates a new output file."):
            return
        output = save_pdf_as(self, "Save PDF after deleting pages", default_output_path(state.file_path, "pages_deleted"))
        if not output:
            return
        if Path(output).exists() and not self._confirm("Output exists. Overwrite?"):
            return
        temp_pdf: str | None = None
        try:
            source_pdf, temp_pdf = self._source_pdf_for_current_view()
            save_deleted_pages(source_pdf, output, pages)
            self.canvas.load_pdf(output)
            self.status.showMessage(f"Saved with deleted pages: {output}", 5000)
        except Exception as exc:
            self._error(f"Failed to delete pages:\n{exc}")
        finally:
            self._cleanup_temp_pdf(temp_pdf)

    def add_merge_files(self) -> None:
        files = pick_pdfs(self, "Select PDFs to merge")
        if not files:
            return
        self.merge_files.extend(files)
        # Keep order while removing duplicates.
        self.merge_files = list(dict.fromkeys(self.merge_files))
        self.merge_panel.set_files(self.merge_files)
        self.preview_merge_files()

    def clear_merge_files(self) -> None:
        self.merge_files.clear()
        self.merge_panel.set_files([])
        self.merge_panel.set_preview_text("")

    def move_merge_file_up(self) -> None:
        idx = self.merge_panel.current_row()
        if idx <= 0 or idx >= len(self.merge_files):
            return
        self.merge_files[idx - 1], self.merge_files[idx] = self.merge_files[idx], self.merge_files[idx - 1]
        self.merge_panel.set_files(self.merge_files)
        self.merge_panel.files_list.setCurrentRow(idx - 1)
        self.preview_merge_files()

    def move_merge_file_down(self) -> None:
        idx = self.merge_panel.current_row()
        if idx < 0 or idx >= len(self.merge_files) - 1:
            return
        self.merge_files[idx + 1], self.merge_files[idx] = self.merge_files[idx], self.merge_files[idx + 1]
        self.merge_panel.set_files(self.merge_files)
        self.merge_panel.files_list.setCurrentRow(idx + 1)
        self.preview_merge_files()

    def remove_merge_file(self) -> None:
        idx = self.merge_panel.current_row()
        if idx < 0 or idx >= len(self.merge_files):
            return
        self.merge_files.pop(idx)
        self.merge_panel.set_files(self.merge_files)
        self.merge_panel.files_list.setCurrentRow(min(idx, len(self.merge_files) - 1))
        self.preview_merge_files()

    def preview_merge_files(self) -> None:
        if not self.merge_files:
            self.merge_panel.set_preview_text("No files selected.")
            return
        lines: list[str] = []
        total_pages = 0
        for i, path in enumerate(self.merge_files, start=1):
            page_count = self._pdf_page_count(path)
            total_pages += max(0, page_count)
            lines.append(f"{i}. {Path(path).name} ({page_count if page_count >= 0 else '?'} pages)")
        lines.append("")
        lines.append(f"Total files: {len(self.merge_files)}")
        lines.append(f"Estimated merged pages: {total_pages}")
        self.merge_panel.set_preview_text("\n".join(lines))

    def merge_pdf_files(self) -> None:
        if len(self.merge_files) < 2:
            self._error("Select at least two PDFs to merge.")
            return
        output = save_pdf_as(self, "Save merged PDF", "merged_output.pdf")
        if not output:
            return
        if Path(output).exists() and not self._confirm("Output exists. Overwrite?"):
            return
        try:
            merge_pdfs(self.merge_files, output)
            self.status.showMessage(f"Merged PDF saved: {output}", 5000)
        except Exception as exc:
            self._error(f"Failed to merge PDFs:\n{exc}")

    def compress_current_pdf(self, dpi: int, quality: int, grayscale: bool) -> None:
        state = self.canvas.state
        if not state.file_path:
            self._error("Open a PDF before compressing.")
            return
        output = save_pdf_as(
            self,
            "Save compressed PDF",
            default_output_path(state.file_path, "compressed_custom"),
        )
        if not output:
            return
        if Path(output).exists() and not self._confirm("Output exists. Overwrite?"):
            return
        temp_pdf: str | None = None
        try:
            source_pdf, temp_pdf = self._source_pdf_for_current_view()
            result = compress_pdf(
                source_pdf,
                output,
                dpi=dpi,
                quality=quality,
                grayscale=grayscale,
            )
            self.status.showMessage(
                f"Compressed PDF saved: {output} ({format_mb(result.output_bytes)} MB, mode={result.mode})",
                7000,
            )
        except Exception as exc:
            self._error(f"Failed to compress PDF:\n{exc}")
        finally:
            self._cleanup_temp_pdf(temp_pdf)

    def preview_compress_current_pdf(self, dpi: int, quality: int, grayscale: bool) -> None:
        state = self.canvas.state
        if not state.file_path:
            self._error("Open a PDF before compression preview.")
            return
        temp_pdf: str | None = None
        try:
            source_pdf, temp_pdf = self._source_pdf_for_current_view()
            result = preview_compress(
                source_pdf,
                dpi=dpi,
                quality=quality,
                grayscale=grayscale,
            )
            ratio = 0.0
            if result.input_bytes > 0:
                ratio = 100.0 * (1.0 - (result.output_bytes / result.input_bytes))
            lines = [
                f"Input size: {format_mb(result.input_bytes)} MB",
                f"Estimated output: {format_mb(result.output_bytes)} MB",
                f"Reduction: {ratio:.2f}%",
                f"Mode: {result.mode}",
                f"DPI: {dpi}",
                f"JPEG quality: {quality}",
                f"Grayscale: {'Yes' if grayscale else 'No'}",
            ]
            self.compress_panel.set_preview_text("\n".join(lines))
        except Exception as exc:
            self._error(f"Compression preview failed:\n{exc}")
        finally:
            self._cleanup_temp_pdf(temp_pdf)

    def export_images(self, image_format: str, dpi: int, page_range_text: str) -> None:
        state = self.canvas.state
        if not state.file_path:
            self._error("Open a PDF before exporting images.")
            return
        output_dir = pick_output_folder(self, "Select image output folder")
        if not output_dir:
            return
        pages = parse_page_range(page_range_text) if page_range_text else None
        try:
            source_pdf = state.file_path
            actions = self.canvas.get_actions()
            temp_pdf: str | None = None
            if actions:
                temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                temp_pdf = temp_file.name
                temp_file.close()
                save_with_actions(state.file_path, temp_pdf, actions)
                source_pdf = temp_pdf

            created = export_pdf_to_images(
                source_pdf,
                output_dir,
                image_format=image_format,
                dpi=dpi,
                one_based_pages=pages,
            )
            self.status.showMessage(f"Exported {len(created)} image(s) to {output_dir}", 6000)
        except Exception as exc:
            self._error(f"Failed to export images:\n{exc}")
        finally:
            if "temp_pdf" in locals() and temp_pdf and Path(temp_pdf).exists():
                try:
                    Path(temp_pdf).unlink(missing_ok=True)
                except Exception:
                    pass

    def _confirm(self, text: str) -> bool:
        return (
            QMessageBox.question(self, "Confirm", text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            == QMessageBox.StandardButton.Yes
        )

    def _error(self, text: str) -> None:
        QMessageBox.critical(self, "Error", text)

    def _on_page_changed(self, current: int, total: int) -> None:
        self.page_label.setText(f"Page: {current}/{total}")

    def preview_page_delete(self, page_range_text: str) -> None:
        state = self.canvas.state
        if not state.file_path:
            self.page_panel.set_preview_text("Open a PDF to preview page deletion.")
            return
        total = self._pdf_page_count(state.file_path)
        if total <= 0:
            self.page_panel.set_preview_text("Unable to read page count.")
            return
        pages = parse_page_range(page_range_text)
        valid_delete = [p for p in pages if 1 <= p <= total]
        remaining = total - len(set(valid_delete))
        lines = [
            f"Current pages: {total}",
            f"Delete pages: {valid_delete if valid_delete else 'None'}",
            f"Remaining pages: {remaining}",
        ]
        if remaining <= 0:
            lines.append("Warning: deleting all pages is not allowed.")
        self.page_panel.set_preview_text("\n".join(lines))

    def _pdf_page_count(self, path: str) -> int:
        try:
            with fitz.open(path) as doc:
                return doc.page_count
        except Exception:
            return -1

    def _apply_initial_splitter_sizes(self) -> None:
        if self._main_splitter is None:
            return
        total = max(1, self.width())
        left = min(260, max(220, int(total * 0.22)))
        right = max(500, total - left - 40)
        self._main_splitter.setSizes([left, right])

    def _source_pdf_for_current_view(self) -> tuple[str, str | None]:
        state = self.canvas.state
        actions = self.canvas.get_actions()
        if not actions:
            return state.file_path or "", None
        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        temp_pdf = temp_file.name
        temp_file.close()
        save_with_actions(state.file_path or "", temp_pdf, actions)
        return temp_pdf, temp_pdf

    def _cleanup_temp_pdf(self, temp_pdf: str | None) -> None:
        if temp_pdf and Path(temp_pdf).exists():
            try:
                Path(temp_pdf).unlink(missing_ok=True)
            except Exception:
                pass


def parse_page_range(page_text: str) -> list[int]:
    raw = page_text.strip()
    if not raw:
        return []
    pages: set[int] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            bits = token.split("-", 1)
            if len(bits) != 2 or (not bits[0].isdigit()) or (not bits[1].isdigit()):
                continue
            start, end = int(bits[0]), int(bits[1])
            if start > end:
                start, end = end, start
            for p in range(start, end + 1):
                pages.add(p)
        elif token.isdigit():
            pages.add(int(token))
    return sorted(p for p in pages if p > 0)


def format_mb(size_bytes: int) -> str:
    return f"{size_bytes / (1024 * 1024):.2f}"
