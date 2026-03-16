from __future__ import annotations

from pypdf import PdfWriter


def merge_pdfs(input_files: list[str], output_file: str) -> None:
    writer = PdfWriter()
    try:
        for path in input_files:
            writer.append(path)
        with open(output_file, "wb") as fh:
            writer.write(fh)
    finally:
        writer.close()
