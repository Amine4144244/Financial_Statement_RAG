import os
import re
from typing import List, Dict, Any, Optional

from app.schemas.document import (
    ParsedDocument,
    DocumentPage,
    DocumentMetadata,
    PageType,
)
from app.ingestion.text_cleaner import TextCleaner


class PDFLoader:
    """Extracts text, metadata, and structural layout from financial PDFs."""

    def __init__(self):
        self.cleaner = TextCleaner()

    def load_document(
        self,
        file_path: str,
        company_id: str,
        fiscal_year: int,
        document_id: Optional[str] = None,
        period_type: str = "FY",
        document_type: str = "annual_report",
    ) -> ParsedDocument:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at path: {file_path}")

        filename = os.path.basename(file_path)
        meta = DocumentMetadata(
            document_id=document_id or f"doc_{company_id}_{fiscal_year}",
            company_id=company_id,
            fiscal_year=fiscal_year,
            period_type=period_type,
            document_type=document_type,
            original_filename=filename,
            storage_path=os.path.abspath(file_path),
        )

        pages = self._extract_pages(file_path)
        meta.total_pages = len(pages)

        # Classify statements and pages
        statement_pages: Dict[str, List[int]] = {
            "income_statement": [],
            "balance_sheet": [],
            "cash_flow": [],
            "notes": [],
            "mda": [],
            "risk_factors": [],
        }

        for page in pages:
            # Check for known financial statements
            raw_lower = page.raw_text.lower() if page.raw_text else page.text.lower()
            
            if re.search(r"consolidated\s+statements?\s+of\s+(?:income|operations|earnings)", raw_lower):
                page.page_type = PageType.FINANCIAL_STATEMENT
                statement_pages["income_statement"].append(page.page_number)
            elif re.search(r"consolidated\s+balance\s+sheets?|statement\s+of\s+financial\s+position", raw_lower):
                page.page_type = PageType.FINANCIAL_STATEMENT
                statement_pages["balance_sheet"].append(page.page_number)
            elif re.search(r"consolidated\s+statements?\s+of\s+cash\s+flows?", raw_lower):
                page.page_type = PageType.FINANCIAL_STATEMENT
                statement_pages["cash_flow"].append(page.page_number)
            elif re.search(r"notes\s+to\s+(?:consolidated\s+)?financial\s+statements?", raw_lower):
                page.page_type = PageType.NOTES_TO_ACCOUNTS
                statement_pages["notes"].append(page.page_number)
            elif re.search(r"management'?s\s+discussion\s+and\s+analysis", raw_lower):
                page.page_type = PageType.NARRATIVE
                statement_pages["mda"].append(page.page_number)
            elif re.search(r"item\s+1a[\.:\s\-]+risk\s+factors", raw_lower):
                page.page_type = PageType.NARRATIVE
                statement_pages["risk_factors"].append(page.page_number)
            else:
                # If page contains lots of tabular numbers, mark financial statement
                number_density = len(re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b", raw_lower))
                if number_density > 15:
                    page.page_type = PageType.FINANCIAL_STATEMENT
                    page.has_tables = True
                else:
                    page.page_type = PageType.NARRATIVE

        return ParsedDocument(
            metadata=meta,
            pages=pages,
            detected_statement_pages=statement_pages,
        )

    def _extract_pages(self, file_path: str) -> List[DocumentPage]:
        # Try PyMuPDF (fitz) first
        try:
            import fitz  # type: ignore[import-not-found, import-untyped]
            return self._extract_with_pymupdf(file_path, fitz)
        except ImportError:
            pass

        # Fallback to pypdf
        try:
            import pypdf  # type: ignore[import-not-found, import-untyped]
            return self._extract_with_pypdf(file_path, pypdf)
        except ImportError:
            raise RuntimeError("Neither pymupdf nor pypdf is installed to extract PDF text.")

    def _extract_with_pymupdf(self, file_path: str, fitz_module) -> List[DocumentPage]:
        doc = fitz_module.open(file_path)
        pages: List[DocumentPage] = []

        for page_idx, page in enumerate(doc):
            page_num = page_idx + 1
            raw_text = page.get_text("text") or ""
            cleaned = self.cleaner.clean_text(raw_text)

            # Check if page has tables via search or layout blocks
            has_tables = bool(re.search(r"\b\d{1,3}(?:,\d{3})+\b", raw_text))

            pages.append(
                DocumentPage(
                    page_number=page_num,
                    text=cleaned,
                    raw_text=raw_text,
                    has_tables=has_tables,
                    metadata={"extractor": "pymupdf"}
                )
            )

        doc.close()
        return pages

    def _extract_with_pypdf(self, file_path: str, pypdf_module) -> List[DocumentPage]:
        reader = pypdf_module.PdfReader(file_path)
        pages: List[DocumentPage] = []

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            cleaned = self.cleaner.clean_text(raw_text)
            has_tables = bool(re.search(r"\b\d{1,3}(?:,\d{3})+\b", raw_text))

            pages.append(
                DocumentPage(
                    page_number=page_num,
                    text=cleaned,
                    raw_text=raw_text,
                    has_tables=has_tables,
                    metadata={"extractor": "pypdf"}
                )
            )

        return pages
