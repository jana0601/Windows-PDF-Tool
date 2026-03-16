from __future__ import annotations

from pathlib import Path

import pymupdf as fitz


def export_pdf_to_images(
    input_pdf: str,
    output_dir: str,
    image_format: str = "png",
    dpi: int = 150,
    one_based_pages: list[int] | None = None,
) -> list[str]:
    image_format = image_format.lower()
    ext = "jpg" if image_format in {"jpg", "jpeg"} else "png"
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    doc = fitz.open(input_pdf)
    try:
        if one_based_pages:
            targets = [p - 1 for p in one_based_pages if 1 <= p <= doc.page_count]
        else:
            targets = list(range(doc.page_count))

        for idx in targets:
            page = doc[idx]
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            path = output / f"page_{idx + 1:04d}.{ext}"
            pix.save(str(path))
            created.append(str(path))
    finally:
        doc.close()

    return created
