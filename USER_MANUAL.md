# Windows PDF Tool - User Manual

## 1. What This Software Does

Windows PDF Tool is a desktop app for common PDF editing and conversion tasks:

- View PDF files page by page
- Add annotations (freehand, rectangle, text note)
- Blackout/redact sensitive content
- Delete selected pages
- Merge multiple PDFs
- Compress PDF with custom settings (DPI, JPEG quality, grayscale)
- Export PDF pages to image files (PNG/JPG)

---

## 2. Start the Application

### If you use the built EXE

1. Open the `dist/WindowsPDFTool/` folder.
2. Double-click `WindowsPDFTool.exe`.

### If you run from source

1. Install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Start app:

```powershell
python src/main.py
```

---

## 3. Interface Overview

- **Left panel**: feature tabs (`Annotate`, `Pages`, `Merge`, `Compress`, `Export`)
- **Right panel**: PDF preview area
- **Top of preview**: page navigation and zoom controls
- **Bottom status bar**: current status and page count

You can drag the divider between left and right panels to resize them.

---

## 4. Basic Workflow

1. Click `Open PDF`.
2. Perform actions (annotate/delete/compress/export/etc.).
3. Save output when prompted.

Important: most operations save to a **new output file**. Your original file is kept unless you explicitly overwrite.

---

## 5. Annotate and Redact

Open the `Annotate` tab.

### Tools

- `View`: normal viewing mode
- `Freehand`: draw with mouse
- `Rectangle`: draw box annotations
- `Text Note`: add custom text with selected font size
- `Blackout`: redact sensitive area
- `Pick Color`: choose annotation color (blackout remains black)

### Text note workflow

1. Click `Text Note`.
2. Enter text and font size.
3. Click on PDF to place it.
4. Drag text to reposition if needed.

### Undo/Redo/Clear

- `Undo`: remove last annotation action
- `Redo`: reapply last undone action
- `Clear Annotations`: remove all current unsaved annotations

### Redaction behavior

Blackout uses true redaction on save/processing, so underlying content in redacted area is removed and should not be copyable/searchable.

---

## 6. Delete Pages

Open `Pages` tab.

1. Enter pages in format like:
   - `2`
   - `1,3,7`
   - `4-8`
   - `1,3-5,9`
2. Click `Preview` to see delete result.
3. Click `Delete Pages`.
4. Choose output file path.

Delete operation uses the current preview state, so unsaved annotations are included.

---

## 7. Merge PDFs

Open `Merge` tab.

1. Click `Add Files` and select 2+ PDFs.
2. Arrange order using:
   - `Up`
   - `Down`
   - `Remove`
3. Click `Preview` to check merge order and total pages.
4. Click `Merge` and choose output path.

---

## 8. Compress PDF

Open `Compress` tab.

1. Set desired:
   - `DPI` (resolution)
   - `JPEG quality`
   - `Convert color to grayscale` (optional)
2. Click `Preview Compression` to estimate size.
3. Click `Compress Current PDF` and choose output file.

Compression uses the current preview state, so unsaved annotations are included.

Guideline:

- Smaller size: lower DPI + lower quality
- Better visual quality: higher DPI + higher quality
- Extra size reduction: enable grayscale

---

## 9. Export PDF to Images

Open `Export` tab.

1. Choose output format (`png` or `jpg`).
2. Set DPI.
3. Optional page filter (example: `1,3-5`).
4. Click `Export Images`.
5. Select output folder.

Export uses the current preview state, so unsaved annotations are included.

---

## 10. Navigation and Zoom

- `< Prev` / `Next >`: switch pages
- `Go`: jump to page number
- `+` / `-`: zoom in/out

---

## 11. Troubleshooting

### App does not start (EXE)

- Make sure you run from full folder `dist/WindowsPDFTool/` (do not move EXE alone).
- If blocked by Windows SmartScreen, choose `More info` -> `Run anyway` (if trusted source).

### Cannot save output

- Check if output file is open in another program (Acrobat/Edge).
- Save to a different path or filename.

### Compression result not small enough

- Lower DPI first (for example 150 -> 110 -> 96).
- Then lower JPEG quality (for example 75 -> 65 -> 55).
- Enable grayscale if color is not required.

### Redaction still visible in old file

- Redaction applies to output created by save/export/compress/delete flow.
- Ensure you open and check the new output file.

---

## 12. Quick Best Practices

- Always keep your original PDF as backup.
- Use `Preview` before destructive operations.
- For redaction, review final output and search/copy test sensitive text.
- Use descriptive output filenames for different versions.
