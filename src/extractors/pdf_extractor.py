"""PDF text and table extraction using pdfplumber + PyMuPDF."""
from __future__ import annotations

import io
from pathlib import Path

import pdfplumber
import fitz  # PyMuPDF

from src.models.schemas import ExtractionResult, PageText


class PDFExtractor:
    """Extracts text (with coordinates) and tables from PDF files."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    # ------------------------------------------------------------------
    def extract(self) -> ExtractionResult:
        pages: list[PageText] = []

        with pdfplumber.open(self.path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # --- Text ---
                text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""

                # --- Tables ---
                raw_tables = page.extract_tables()
                tables: list[list[list[str]]] = []
                for tbl in raw_tables:
                    normalized = [
                        [cell if cell is not None else "" for cell in row]
                        for row in tbl
                    ]
                    tables.append(normalized)

                pages.append(PageText(page_number=page_num, text=text, tables=tables))

        raw_text = "\n\n".join(p.text for p in pages)
        return ExtractionResult(
            source_file=str(self.path),
            total_pages=len(pages),
            pages=pages,
            raw_text=raw_text,
        )

    # ------------------------------------------------------------------
    @staticmethod
    def extract_from_bytes(data: bytes, filename: str = "upload.pdf") -> ExtractionResult:
        """Extract from in-memory bytes (useful for FastAPI UploadFile)."""
        tmp_path = Path(f"/tmp/{filename}")
        tmp_path.write_bytes(data)
        extractor = PDFExtractor(tmp_path)
        result = extractor.extract()
        tmp_path.unlink(missing_ok=True)
        return result

    # ------------------------------------------------------------------
    def get_text_with_bbox(self) -> list[dict]:
        """Return list of {page, text, bbox} for citation building."""
        results = []
        doc = fitz.open(str(self.path))
        for page_num, page in enumerate(doc, start=1):
            blocks = page.get_text("blocks")
            for block in blocks:
                x0, y0, x1, y1, text, *_ = block
                if text.strip():
                    results.append({
                        "page": page_num,
                        "text": text.strip(),
                        "bbox": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                    })
        doc.close()
        return results
