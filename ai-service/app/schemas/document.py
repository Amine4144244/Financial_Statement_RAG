from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class PageType(str, Enum):
    NARRATIVE = "narrative"
    FINANCIAL_STATEMENT = "financial_statement"
    NOTES_TO_ACCOUNTS = "notes_to_accounts"
    SCANNED = "scanned"
    UNKNOWN = "unknown"


class DocumentPage(BaseModel):
    page_number: int = Field(..., ge=1, description="1-based page number")
    text: str = Field(..., description="Cleaned narrative or raw text on the page")
    raw_text: Optional[str] = None
    page_type: PageType = PageType.UNKNOWN
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    has_tables: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentMetadata(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    company_name: Optional[str] = None
    fiscal_year: int
    period_type: str = "FY"
    document_type: str = "annual_report"
    original_filename: str
    total_pages: int = 0
    storage_path: Optional[str] = None


class ParsedDocument(BaseModel):
    metadata: DocumentMetadata
    pages: List[DocumentPage] = Field(default_factory=list)
    detected_statement_pages: Dict[str, List[int]] = Field(
        default_factory=dict,
        description="Maps statement names (e.g. 'income_statement') to list of page numbers"
    )
