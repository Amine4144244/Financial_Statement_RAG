from typing import Dict, Any, List, Optional
import os

from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.table_extractor import TableExtractor
from app.ingestion.chunker import SectionAwareChunker
from app.services.chroma_service import ChromaService
from app.services.postgres_service import DatabaseService
from app.schemas.financial_fact import NormalizedFinancialFact


class IngestionPipeline:
    """End-to-end ingestion pipeline coordinating PDF parsing, fact extraction, and vector indexing."""

    def __init__(
        self,
        db_service: Optional[DatabaseService] = None,
        chroma_service: Optional[ChromaService] = None,
    ):
        self.pdf_loader = PDFLoader()
        self.table_extractor = TableExtractor()
        self.chunker = SectionAwareChunker()
        self.db_service = db_service or DatabaseService()
        self.chroma_service = chroma_service or ChromaService()

    def process_document(
        self,
        file_path: str,
        company_id: str,
        fiscal_year: int,
        document_id: Optional[str] = None,
        period_type: str = "FY",
        document_type: str = "annual_report",
    ) -> Dict[str, Any]:
        """Runs full ingestion on a financial document PDF."""
        # 1. Parse PDF pages and layout
        parsed_doc = self.pdf_loader.load_document(
            file_path=file_path,
            company_id=company_id,
            fiscal_year=fiscal_year,
            document_id=document_id,
            period_type=period_type,
            document_type=document_type,
        )

        doc_id = parsed_doc.metadata.document_id

        # 2. Extract structured financial facts from tables
        extracted_facts: List[NormalizedFinancialFact] = []
        for page in parsed_doc.pages:
            if page.has_tables or page.page_type.value == "financial_statement":
                facts = self.table_extractor.extract_facts_from_page(
                    page=page,
                    company_id=company_id,
                    document_id=doc_id,
                    default_fiscal_year=fiscal_year,
                )
                extracted_facts.extend(facts)

        # 3. Store structured facts in relational database
        facts_saved = 0
        if extracted_facts:
            facts_saved = self.db_service.save_facts(extracted_facts, document_id=doc_id)

        # 4. Chunk narrative sections
        narrative_chunks = self.chunker.chunk_document(parsed_doc)

        # 5. Index narrative chunks into vector database
        chunks_indexed = 0
        if narrative_chunks:
            chunks_indexed = self.chroma_service.upsert_chunks(narrative_chunks)

        return {
            "document_id": doc_id,
            "company_id": company_id,
            "fiscal_year": fiscal_year,
            "total_pages": parsed_doc.metadata.total_pages,
            "detected_statements": parsed_doc.detected_statement_pages,
            "facts_extracted": len(extracted_facts),
            "facts_saved": facts_saved,
            "chunks_indexed": chunks_indexed,
            "status": "completed",
        }
