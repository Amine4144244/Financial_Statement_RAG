from typing import Optional, Dict, Any, List

from app.schemas.query import (
    FinancialAnswerResponse,
    QueryIntent,
    Citation,
    CalculatedMetric,
)
from app.retrieval.query_analyzer import QueryAnalyzer
from app.retrieval.query_router import QueryRouter, RouteDecision
from app.retrieval.financial_retriever import FinancialRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.generation.context_builder import ContextBuilder
from app.generation.answer_validator import AnswerValidator
from app.generation.citation_validator import CitationValidator
from app.services.llm_service import LLMService


class FinancialRAGOrchestrator:
    """Full hybrid RAG pipeline coordinating query analysis, dual retrieval, calculation, generation, and verification."""

    def __init__(
        self,
        financial_retriever: Optional[FinancialRetriever] = None,
        vector_retriever: Optional[VectorRetriever] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.analyzer = QueryAnalyzer()
        self.router = QueryRouter()
        self.financial_retriever = financial_retriever or FinancialRetriever()
        self.vector_retriever = vector_retriever or VectorRetriever()
        self.llm_service = llm_service or LLMService()
        self.context_builder = ContextBuilder()
        self.answer_validator = AnswerValidator()
        self.citation_validator = CitationValidator()

    def answer_question(
        self,
        question: str,
        company_ids: Optional[List[str]] = None,
        fiscal_years: Optional[List[int]] = None,
    ) -> FinancialAnswerResponse:
        # 1. Analyze query
        structured_query = self.analyzer.analyze_query(question)

        # Merge with user-supplied parameters if provided
        target_companies = company_ids if company_ids else structured_query.company_ids
        target_years = fiscal_years if fiscal_years else structured_query.fiscal_years

        # 2. Route query
        route = self.router.route_query(structured_query)

        # 3. Retrieve structured facts and calculate ratios
        retrieved_facts = []
        calculations = []
        if route in [RouteDecision.SQL_ONLY, RouteDecision.HYBRID]:
            fin_result = self.financial_retriever.retrieve_financials(
                company_ids=target_companies,
                fiscal_years=target_years if target_years else None,
                requested_metrics=structured_query.metrics if structured_query.metrics else None,
                include_calculated_ratios=True,
            )
            retrieved_facts = fin_result["facts"]
            calculations = fin_result["calculations"]

        # 4. Retrieve semantic narrative passages
        passages = []
        citations = []
        if route in [RouteDecision.SEMANTIC_ONLY, RouteDecision.HYBRID]:
            subqueries = self.router.generate_semantic_subqueries(structured_query)
            passages = self.vector_retriever.retrieve_passages(
                query=question,
                subqueries=subqueries,
                company_ids=target_companies,
                fiscal_years=target_years if target_years else None,
                top_k=5,
            )
            citations = self.vector_retriever.to_citations(passages)

        # 5. Build evidence prompt context
        evidence = self.context_builder.build_evidence_context(
            question=question,
            facts=retrieved_facts,
            calculations=calculations,
            passages=passages,
        )

        # 6. Generate answer using LLM
        generated_text = self.llm_service.generate_response(
            system_prompt=evidence["system_prompt"],
            user_prompt=evidence["user_prompt"],
        )

        # 7. Validate answer and citations
        val_status, val_warnings = self.answer_validator.validate_answer(
            generated_text=generated_text,
            verified_facts=retrieved_facts,
            calculations=calculations,
        )

        valid_citations, cit_warnings = self.citation_validator.validate_citations(
            generated_text=generated_text,
            retrieved_citations=citations,
            retrieved_facts=retrieved_facts,
        )
        val_warnings.extend(cit_warnings)

        return FinancialAnswerResponse(
            question=question,
            answer=generated_text,
            intent=structured_query.intent,
            status="completed",
            metrics_retrieved=retrieved_facts,
            calculations=calculations,
            citations=valid_citations,
            validation_status=val_status,
            validation_warnings=val_warnings,
        )
