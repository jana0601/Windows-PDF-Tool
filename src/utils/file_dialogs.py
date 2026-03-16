from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QWidget


def pick_pdf(parent: QWidget, title: str = "Open PDF") -> str:
    path, _ = QFileDialog.getOpenFileName(parent, title, "", "PDF Files (*.pdf)")
    return path


def pick_pdfs(parent: QWidget, title: str = "Select PDF files") -> list[str]:
    paths, _ = QFileDialog.getOpenFileNames(parent, title, "", "PDF Files (*.pdf)")
    return paths


def save_pdf_as(parent: QWidget, title: str = "Save PDF", default_name: str = "") -> str:
    path, _ = QFileDialog.getSaveFileName(parent, title, default_name, "PDF Files (*.pdf)")
    return path


def pick_output_folder(parent: QWidget, title: str = "Select output folder") -> str:
    return QFileDialog.getExistingDirectory(parent, title)
