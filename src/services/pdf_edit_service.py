from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pymupdf as fitz


def default_output_path(input_path: str, suffix: str) -> str:
    src = Path(input_path)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(src.with_name(f"{src.stem}_{suffix}_{stamp}.pdf"))


def open_pdf(path: str) -> fitz.Document:
    return fitz.open(path)


def save_with_actions(
    source_pdf_path: str,
    output_pdf_path: str,
    actions: list[dict[str, Any]],
) -> None:
    doc = fitz.open(source_pdf_path)
    try:
        _apply_actions(doc, actions)
        doc.save(output_pdf_path)
    finally:
        doc.close()


def save_deleted_pages(
    source_pdf_path: str,
    output_pdf_path: str,
    one_based_pages_to_delete: list[int],
) -> None:
    doc = fitz.open(source_pdf_path)
    try:
        zero_based = sorted({p - 1 for p in one_based_pages_to_delete if p > 0}, reverse=True)
        for page_idx in zero_based:
            if 0 <= page_idx < doc.page_count:
                doc.delete_page(page_idx)
        if doc.page_count == 0:
            raise ValueError("Cannot delete all pages from a PDF.")
        doc.save(output_pdf_path)
    finally:
        doc.close()


def save_rotated_pages(
    source_pdf_path: str,
    output_pdf_path: str,
    one_based_pages_to_rotate: list[int],
    angle: int,
) -> None:
    if angle not in {90, 180, 270}:
        raise ValueError("Rotation angle must be 90, 180, or 270.")
    doc = fitz.open(source_pdf_path)
    try:
        for one_based in sorted(set(one_based_pages_to_rotate)):
            idx = one_based - 1
            if 0 <= idx < doc.page_count:
                page = doc[idx]
                current = page.rotation
                page.set_rotation((current + angle) % 360)
        doc.save(output_pdf_path)
    finally:
        doc.close()


def save_reordered_pages(
    source_pdf_path: str,
    output_pdf_path: str,
    one_based_new_order: list[int],
) -> None:
    src = fitz.open(source_pdf_path)
    dst = fitz.open()
    try:
        page_count = src.page_count
        expected = list(range(1, page_count + 1))
        if sorted(one_based_new_order) != expected:
            raise ValueError("Reorder sequence must include each page exactly once.")

        for one_based in one_based_new_order:
            idx = one_based - 1
            dst.insert_pdf(src, from_page=idx, to_page=idx)
        dst.save(output_pdf_path)
    finally:
        dst.close()
        src.close()


def _apply_actions(doc: fitz.Document, actions: list[dict[str, Any]]) -> None:
    redaction_pages: set[int] = set()
    for action in actions:
        page_idx = int(action["page"])
        if not (0 <= page_idx < doc.page_count):
            continue
        page = doc[page_idx]
        action_type = action.get("type")

        if action_type == "freehand":
            points = action.get("points", [])
            color = tuple(action.get("color", (1, 0, 0)))
            width = float(action.get("width", 2.0))
            for p0, p1 in zip(points[:-1], points[1:]):
                page.draw_line(fitz.Point(*p0), fitz.Point(*p1), color=color, width=width)

        elif action_type in {"rect", "blackout"}:
            rect = fitz.Rect(*action["rect"])
            color = tuple(action.get("color", (1, 0, 0)))
            width = float(action.get("width", 2.0))
            if action_type == "blackout":
                # True redaction: remove text/content under the rectangle.
                page.add_redact_annot(rect, fill=(0, 0, 0))
                redaction_pages.add(page_idx)
            else:
                page.draw_rect(rect, color=color, width=width)

        elif action_type == "text":
            text = str(action.get("text", "")).strip()
            if not text:
                continue
            pt = fitz.Point(*action["point"])
            color = tuple(action.get("color", (1, 0, 0)))
            size = float(action.get("size", 12))
            page.insert_text(pt, text, fontsize=size, color=color)

    for page_idx in sorted(redaction_pages):
        if 0 <= page_idx < doc.page_count:
            doc[page_idx].apply_redactions()
