from decimal import Decimal
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class ValidationStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


class ScaleType(str, Enum):
    EXACT = "exact"
    THOUSANDS = "thousands"
    MILLIONS = "millions"
    BILLIONS = "billions"


class StatementType(str, Enum):
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    NOTES = "notes"
    UNKNOWN = "unknown"


class NormalizedFinancialFact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    document_id: Optional[str] = None
    metric: str = Field(..., description="Normalized metric key, e.g. 'revenue', 'net_income'")
    value: Decimal = Field(..., description="Exact scaled numerical value, e.g. 120000000.00")
    raw_value: Optional[str] = None
    currency: str = "USD"
    unit: str = "USD"
    scale: ScaleType = ScaleType.EXACT
    fiscal_year: int
    period_type: str = "FY"
    source_id: Optional[str] = None
    source_page: Optional[int] = None
    statement_type: StatementType = StatementType.UNKNOWN
    validation_status: ValidationStatus = ValidationStatus.PENDING
    is_restated: bool = False
    notes: Optional[str] = None

    @field_validator("metric")
    @classmethod
    def clean_metric_name(cls, v: str) -> str:
        cleaned = v.strip().lower().replace(" ", "_").replace("-", "_")
        return cleaned

    @field_validator("value", mode="before")
    @classmethod
    def parse_decimal_value(cls, v: Any) -> Decimal:
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            cleaned = v.replace(",", "").replace("$", "").strip()
            # Handle negative parentheses: (15,000) -> -15000
            if cleaned.startswith("(") and cleaned.endswith(")"):
                cleaned = "-" + cleaned[1:-1].strip()
            return Decimal(cleaned)
        raise ValueError(f"Cannot parse value {v} to Decimal")


class FinancialSource(BaseModel):
    id: str = Field(..., description="Stable source identifier, e.g. 'doc123_p42_tab1'")
    document_id: str
    page_number: int
    section_name: Optional[str] = None
    table_identifier: Optional[str] = None
    raw_snippet: Optional[str] = None
