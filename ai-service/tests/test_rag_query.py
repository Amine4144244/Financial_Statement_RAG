import pytest
from decimal import Decimal

from app.retrieval.query_analyzer import QueryAnalyzer
from app.retrieval.query_router import QueryRouter, RouteDecision
from app.retrieval.financial_retriever import FinancialRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.generation.context_builder import ContextBuilder
from app.generation.answer_validator import AnswerValidator
from app.generation.citation_validator import CitationValidator
from app.generation.answer_generator import FinancialRAGOrchestrator
from app.services.postgres_service import DatabaseService
from app.services.chroma_service import ChromaService
from app.services.llm_service import LLMService
from app.schemas.financial_fact import NormalizedFinancialFact, ValidationStatus
from app.schemas.query import QueryIntent, Citation, CalculatedMetric
from app.ingestion.chunker import DocumentChunk


def test_query_analyzer_and_router():
    analyzer = QueryAnalyzer()
    q = "How did Company A's revenue and net profit margin change from 2024 to 2025, and what explains the changes?"
    res = analyzer.analyze_query(q)

    assert "company_a" in res.company_ids
    assert 2024 in res.fiscal_years
    assert 2025 in res.fiscal_years
    assert "revenue" in res.metrics
    assert "net_income" in res.metrics
    assert res.intent == QueryIntent.HYBRID_COMPARISON
    assert res.requires_sql is True
    assert res.requires_semantic_search is True
    assert res.requires_calculation is True

    route = QueryRouter.route_query(res)
    assert route == RouteDecision.HYBRID


def test_answer_and_citation_validators():
    facts = [
        {"metric": "revenue", "value": 120000000.0, "source_page": 42},
        {"metric": "net_income", "value": 18000000.0, "source_page": 42},
    ]
    calcs = [
        CalculatedMetric(name="net_profit_margin", company_id="company_a", fiscal_year=2025, value=15.0, unit="%"),
        CalculatedMetric(name="revenue_growth", company_id="company_a", fiscal_year=2025, value=20.0, unit="%"),
    ]
    citations = [
        Citation(document_id="doc1", company_id="company_a", fiscal_year=2025, page_number=42, excerpt="Growth details"),
    ]

    # Valid answer with matching numbers
    valid_text = "Revenue grew by 20.0% while net profit margin remained at 15.0%. Source [doc1_Page_42]."
    status, warnings = AnswerValidator.validate_answer(valid_text, facts, calcs)
    assert status == "verified"
    assert len(warnings) == 0

    valid_cits, c_warnings = CitationValidator.validate_citations(valid_text, citations)
    assert len(valid_cits) == 1
    assert valid_cits[0].page_number == 42

    # Hallucinated number (e.g. 99% margin)
    hallucinated_text = "Net profit margin was 99% due to expansion."
    status_bad, warnings_bad = AnswerValidator.validate_answer(hallucinated_text, facts, calcs)
    assert status_bad == "warnings"
    assert any("99" in w for w in warnings_bad)


def test_full_rag_orchestrator(tmp_path):
    # 1. Setup isolated test DB and ChromaDB
    db = DatabaseService(db_url=f"sqlite:///{tmp_path}/rag_query_test.db")
    facts = [
        NormalizedFinancialFact(company_id="company_a", metric="revenue", value=Decimal("100000000"), fiscal_year=2024, validation_status=ValidationStatus.VERIFIED),
        NormalizedFinancialFact(company_id="company_a", metric="revenue", value=Decimal("120000000"), fiscal_year=2025, validation_status=ValidationStatus.VERIFIED),
        NormalizedFinancialFact(company_id="company_a", metric="net_income", value=Decimal("15000000"), fiscal_year=2024, validation_status=ValidationStatus.VERIFIED),
        NormalizedFinancialFact(company_id="company_a", metric="net_income", value=Decimal("18000000"), fiscal_year=2025, validation_status=ValidationStatus.VERIFIED),
    ]
    db.save_facts(facts)

    chroma = ChromaService(persist_directory=str(tmp_path / "rag_chroma"))
    chunks = [
        DocumentChunk(
            chunk_id="chunk_a_2025_1",
            document_id="doc_a_2025",
            company_id="company_a",
            fiscal_year=2025,
            section="mda",
            page_start=42,
            page_end=42,
            text="Revenue growth was driven by cloud software demand, but operating costs increased due to market expansion.",
        )
    ]
    chroma.upsert_chunks(chunks)

    # 2. Wire orchestrator
    fin_retriever = FinancialRetriever(db_service=db)
    vec_retriever = VectorRetriever(chroma_service=chroma)
    llm = LLMService(api_key="mock_key_for_test")  # Triggers structured fallback

    orchestrator = FinancialRAGOrchestrator(
        financial_retriever=fin_retriever,
        vector_retriever=vec_retriever,
        llm_service=llm,
    )

    # 3. Execute hybrid query
    q = "Compare Company A's profitability in 2024 and 2025. Did net profit margin improve, and why?"
    response = orchestrator.answer_question(q)

    assert response.status == "completed"
    assert len(response.metrics_retrieved) >= 4
    assert len(response.calculations) >= 3

    # Check calculated ratios
    growth = next(c for c in response.calculations if c.name == "revenue_growth")
    assert growth.value == 20.0

    margin_2025 = next(c for c in response.calculations if c.name == "net_profit_margin" and c.fiscal_year == 2025)
    assert margin_2025.value == 15.0

    margin_diff = next(c for c in response.calculations if c.name == "net_margin_change_pp")
    assert margin_diff.value == 0.0

    # Citations
    assert len(response.citations) >= 1
    assert response.citations[0].page_number == 42
    assert "cloud" in response.citations[0].excerpt.lower()
