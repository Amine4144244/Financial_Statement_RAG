from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from app.schemas.query import FinancialAnswerResponse
from app.generation.answer_generator import FinancialRAGOrchestrator

router = APIRouter(prefix="/internal/rag", tags=["RAG Query"])
orchestrator = FinancialRAGOrchestrator()


class RAGQueryRequest(BaseModel):
    question: str = Field(..., description="Natural language financial analysis question")
    company_ids: Optional[List[str]] = Field(default=None, description="Optional target company IDs")
    fiscal_years: Optional[List[int]] = Field(default=None, description="Optional fiscal years")


@router.post("/query", response_model=FinancialAnswerResponse)
def execute_rag_query(req: RAGQueryRequest) -> FinancialAnswerResponse:
    try:
        response = orchestrator.answer_question(
            question=req.question,
            company_ids=req.company_ids,
            fiscal_years=req.fiscal_years,
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
