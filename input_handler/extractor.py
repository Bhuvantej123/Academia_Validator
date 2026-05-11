"""
input_handler/extractor.py
Extracts plain text from PDF, DOCX, and TXT files.
"""

import io
from pathlib import Path
from logger import get_logger

log = get_logger(__name__)


class TextExtractor:
    """Unified text extractor supporting .pdf, .docx, .txt."""

    def extract(self, file_path: str | Path, file_type: str | None = None) -> str:
        path = Path(file_path)
        ext = (file_type or path.suffix).lower()

        log.info(f"Extracting text from: {path.name}  (type={ext})")

        if ext == ".pdf":
            return self._extract_pdf(path)
        elif ext == ".docx":
            return self._extract_docx(path)
        elif ext == ".txt":
            return self._extract_txt(path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    # ─── Private helpers ──────────────────────────────────────────

    def _extract_pdf(self, path: Path) -> str:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            pages = [page.get_text("text") for page in doc]
            doc.close()
            text = "\n".join(pages)
            log.debug(f"PDF extracted: {len(text)} chars from {doc.page_count} pages")
            return text
        except ImportError:
            # Fallback: pdfminer
            log.warning("PyMuPDF not found — falling back to pdfminer")
            return self._extract_pdf_pdfminer(path)

    def _extract_pdf_pdfminer(self, path: Path) -> str:
        from pdfminer.high_level import extract_text as pm_extract
        return pm_extract(str(path))

    def _extract_docx(self, path: Path) -> str:
        from docx import Document
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        log.debug(f"DOCX extracted: {len(text)} chars, {len(paragraphs)} paragraphs")
        return text

    def _extract_txt(self, path: Path) -> str:
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                text = path.read_text(encoding=enc)
                log.debug(f"TXT extracted: {len(text)} chars (encoding={enc})")
                return text
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("Failed to decode TXT with common encodings")


# ─── Singleton ────────────────────────────────────────────────────
extractor = TextExtractor()
