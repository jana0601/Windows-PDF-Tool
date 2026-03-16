from __future__ import annotations

import io
import os
import tempfile
from dataclasses import dataclass

import pymupdf as fitz
from PIL import Image

@dataclass
class CompressResult:
    input_bytes: int
    output_bytes: int
    mode: str
    target_met: bool


def compress_pdf(
    input_file: str,
    output_file: str,
    dpi: int,
    quality: int,
    grayscale: bool = False,
) -> CompressResult:
    input_size = os.path.getsize(input_file)
    out_bytes = _compress_raster_custom(input_file, output_file, dpi=dpi, quality=quality, grayscale=grayscale)
    mode = f"dpi={dpi},q={quality}"
    if grayscale:
        mode += ",grayscale"
    return CompressResult(
        input_bytes=input_size,
        output_bytes=out_bytes,
        mode=mode,
        target_met=True,
    )

def preview_compress(
    input_file: str,
    dpi: int,
    quality: int,
    grayscale: bool = False,
) -> CompressResult:
    with tempfile.TemporaryDirectory() as td:
        temp_path = os.path.join(td, "compress_preview.pdf")
        return compress_pdf(
            input_file,
            temp_path,
            dpi=dpi,
            quality=quality,
            grayscale=grayscale,
        )


def _build_raster_pdf_bytes(src_doc: fitz.Document, dpi: int, quality: int, grayscale: bool = False) -> bytes:
    out = fitz.open()
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)
    try:
        for page in src_doc:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if grayscale:
                image = image.convert("L").convert("RGB")
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=quality, optimize=True)
            jpg = buf.getvalue()

            dst = out.new_page(width=page.rect.width, height=page.rect.height)
            dst.insert_image(dst.rect, stream=jpg, keep_proportion=False)

        return out.tobytes(garbage=4, deflate=True, clean=True)
    finally:
        out.close()


def _compress_raster_custom(input_file: str, output_file: str, dpi: int, quality: int, grayscale: bool) -> int:
    src = fitz.open(input_file)
    try:
        payload = _build_raster_pdf_bytes(src, dpi=dpi, quality=quality, grayscale=grayscale)
    finally:
        src.close()
    with open(output_file, "wb") as fh:
        fh.write(payload)
    return len(payload)
