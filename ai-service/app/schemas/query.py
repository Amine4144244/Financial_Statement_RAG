from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    FACTUAL_METRIC = "factual_metric"
    RATIO_CALCULATION = "ratio_calculation"
    NARRATIVE_EXPLANATION = "narrative_explanation"
    HYBRID_COMPARISON = "hybrid_comparison"
    UNKNOWN = "unknown"


class StructuredQuery(BaseModel):
    original_question: str
    intent: QueryIntent = QueryIntent.UNKNOWN
    company_ids: List[str] = Field(default_factory=list)
    fiscal_years: List[int] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    requires_sql: bool = False
    requires_semantic_search: bool = False
    requires_calculation: bool = False


class Citation(BaseModel):
    document_id: str
    company_id: str
    fiscal_year: int
    page_number: int
    section: Optional[str] = None
    chunk_id: Optional[str] = None
    source_id: Optional[str] = None
    excerpt: str


class CalculatedMetric(BaseModel):
    name: str
    company_id: str
    fiscal_year: int
    value: float
    unit: str = "%"
    formula: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class FinancialAnswerResponse(BaseModel):
    question: str
    answer: str
    intent: QueryIntent
    status: str = "completed"
    metrics_retrieved: List[Dict[str, Any]] = Field(default_factory=list)
    calculations: List[CalculatedMetric] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    validation_status: str = "verified"  # 'verified', 'warnings', 'unsupported'
    validation_warnings: List[str] = Field(default_factory=list)
