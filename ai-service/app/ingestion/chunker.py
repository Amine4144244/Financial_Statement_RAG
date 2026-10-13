import re
from typing import List, Dict, Any, Optional

from app.schemas.document import ParsedDocument, DocumentPage, PageType


class DocumentChunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        company_id: str,
        fiscal_year: int,
        section: str,
        page_start: int,
        page_end: int,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.company_id = company_id
        self.fiscal_year = fiscal_year
        self.section = section
        self.page_start = page_start
        self.page_end = page_end
        self.text = text
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "company_id": self.company_id,
            "fiscal_year": self.fiscal_year,
            "section": self.section,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "text": self.text,
            "metadata": self.metadata,
        }


class SectionAwareChunker:
    """Partitions financial documents into semantic narrative chunks respecting section boundaries."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, parsed_doc: ParsedDocument) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        meta = parsed_doc.metadata

        # Attempt to use LlamaIndex SentenceSplitter
        splitter = self._get_splitter()

        # Group pages by section
        current_section = "general_overview"
        section_pages: Dict[str, List[DocumentPage]] = {}

        for page in parsed_doc.pages:
            # Check if this page introduces a new section
            detected_sec = self._detect_section(page)
            if detected_sec:
                current_section = detected_sec

            # Skip financial statement table pages from narrative chunking
            # (they are already extracted as structured facts)
            if page.page_type == PageType.FINANCIAL_STATEMENT and not page.text.strip():
                continue

            if current_section not in section_pages:
                section_pages[current_section] = []
            section_pages[current_section].append(page)

        # Split narrative text within each section
        for section_name, pages in section_pages.items():
            if not pages:
                continue

            section_text_blocks = []
            page_map = []  # Tracks character index to page number

            for p in pages:
                if not p.text.strip():
                    continue
                start_char = len(section_text_blocks)
                section_text_blocks.append(p.text)
                page_map.append((start_char, p.page_number))

            full_section_text = "\n\n".join(section_text_blocks)
            if not full_section_text.strip():
                continue

            split_texts = splitter(full_section_text)

            for idx, text_chunk in enumerate(split_texts):
                if not text_chunk.strip():
                    continue

                chunk_id = f"{meta.document_id}_{section_name}_{idx+1:04d}"
                page_start = pages[0].page_number
                page_end = pages[-1].page_number

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=meta.document_id,
                        company_id=meta.company_id,
                        fiscal_year=meta.fiscal_year,
                        section=section_name,
                        page_start=page_start,
                        page_end=page_end,
                        text=text_chunk.strip(),
                        metadata={
                            "company_id": meta.company_id,
                            "fiscal_year": meta.fiscal_year,
                            "section": section_name,
                            "document_id": meta.document_id,
                        },
                    )
                )

        return chunks

    def _get_splitter(self):
        """Returns a chunk splitting function, using LlamaIndex if available, or regex fallback."""
        try:
            from llama_index.core.node_parser import SentenceSplitter
            llama_splitter = SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            return lambda text: llama_splitter.split_text(text)
        except ImportError:
            # Fallback sentence-based splitting
            return self._fallback_split

    def _fallback_split(self, text: str) -> List[str]:
        # Split into sentences using punctuation boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = []
        current_len = 0

        target_chars = self.chunk_size * 4  # rough approximation 4 chars/token

        for sent in sentences:
            sent_len = len(sent)
            if current_len + sent_len > target_chars and current_chunk:
                chunks.append(" ".join(current_chunk))
                # Overlap: keep the last sentence
                current_chunk = [current_chunk[-1], sent] if len(current_chunk) > 1 else [sent]
                current_len = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sent)
                current_len += sent_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _detect_section(self, page: DocumentPage) -> Optional[str]:
        text_lower = (page.raw_text or page.text).lower()
        if re.search(r"management'?s\s+discussion\s+and\s+analysis", text_lower):
            return "mda"
        if re.search(r"item\s+1a[\.:\s\-]+risk\s+factors", text_lower):
            return "risk_factors"
        if re.search(r"business\s+overview|description\s+of\s+business", text_lower):
            return "business_overview"
        if re.search(r"notes\s+to\s+(?:consolidated\s+)?financial\s+statements?", text_lower):
            return "notes"
        return None
