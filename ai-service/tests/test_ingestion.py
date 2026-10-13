import os
import pytest
from decimal import Decimal
import pymupdf

from app.ingestion.text_cleaner import TextCleaner
from app.ingestion.financial_normalizer import FinancialNormalizer
from app.ingestion.table_extractor import TableExtractor
from app.ingestion.chunker import SectionAwareChunker
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.indexing import IngestionPipeline
from app.services.postgres_service import DatabaseService
from app.services.chroma_service import ChromaService
from app.schemas.financial_fact import ScaleType, StatementType, ValidationStatus


def test_text_cleaner():
    cleaner = TextCleaner()
    # Test hyphenation across newline
    raw = "The company saw high profita-\n   bility in 2025."
    cleaned = cleaner.clean_text(raw)
    assert "profitability" in cleaned

    # Test section header detection
    sec = cleaner.identify_section_header("Item 1A. Risk Factors")
    assert sec == "risk_factors"

    sec2 = cleaner.identify_section_header("Item 7. Management's Discussion and Analysis")
    assert sec2 == "mda"


def test_financial_normalizer():
    normalizer = FinancialNormalizer()

    # Test scale detection
    context = "Consolidated Statements of Income (Amounts in thousands of USD)"
    scale = normalizer.detect_scale(context)
    assert scale == ScaleType.THOUSANDS

    # Test normalization: $120,000 in thousands -> 120,000,000
    fact = normalizer.normalize_fact(
        company_id="company_a",
        raw_metric="Total Net Sales",
        raw_value="120,000",
        fiscal_year=2025,
        context_text=context,
    )
    assert fact is not None
    assert fact.metric == "revenue"
    assert fact.value == Decimal("120000000")
    assert fact.scale == ScaleType.THOUSANDS
    assert fact.validation_status == ValidationStatus.VERIFIED

    # Test negative value in parentheses: (15,000) in thousands -> -15,000,000
    fact_neg = normalizer.normalize_fact(
        company_id="company_a",
        raw_metric="Net Income",
        raw_value="(15,000)",
        fiscal_year=2024,
        context_text=context,
    )
    assert fact_neg is not None
    assert fact_neg.metric == "net_income"
    assert fact_neg.value == Decimal("-15000000")


def test_table_extractor():
    extractor = TableExtractor()
    sample_text = """
Consolidated Statements of Income
(in millions of dollars)
Years Ended December 31, 2025 2024
Revenue $120 $100
Operating expenses 72 60
Net income 18 15
"""
    from app.schemas.document import DocumentPage
    page = DocumentPage(page_number=42, text=sample_text, raw_text=sample_text, has_tables=True)

    facts = extractor.extract_facts_from_page(
        page=page,
        company_id="company_a",
        document_id="doc_test_1",
        default_fiscal_year=2025,
    )

    metrics_found = {f.metric: f.value for f in facts if f.fiscal_year == 2025}
    assert "revenue" in metrics_found
    assert metrics_found["revenue"] == Decimal("120000000")
    assert metrics_found["net_income"] == Decimal("18000000")

    metrics_2024 = {f.metric: f.value for f in facts if f.fiscal_year == 2024}
    assert metrics_2024["revenue"] == Decimal("100000000")
    assert metrics_2024["net_income"] == Decimal("15000000")


def test_full_pipeline_with_generated_pdf(tmp_path):
    # 1. Generate a mock annual report PDF using PyMuPDF
    pdf_path = str(tmp_path / "sample_annual_report_2025.pdf")
    doc = pymupdf.open()

    # Page 1: Overview
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Company A Annual Report FY2025\nBusiness Overview\nCompany A develops cloud software solutions.", fontsize=12)

    # Page 2: MD&A
    p2 = doc.new_page()
    p2.insert_text(
        (50, 50),
        "Item 7. Management's Discussion and Analysis\n"
        "Revenue increased during FY2025 driven by cloud demand. Operating costs increased due to investments in expansion.",
        fontsize=12,
    )

    # Page 3: Financial Statement Table
    p3 = doc.new_page()
    table_content = (
        "Consolidated Statements of Income\n"
        "(Amounts in millions)\n"
        "For Year Ended 2025 2024\n"
        "Revenue 120 100\n"
        "Operating expenses 72 60\n"
        "Net income 18 15\n"
    )
    p3.insert_text((50, 50), table_content, fontsize=12)

    doc.save(pdf_path)
    doc.close()

    # 2. Run Ingestion Pipeline
    test_db = DatabaseService(db_url=f"sqlite:///{tmp_path}/test.db")
    test_chroma = ChromaService(persist_directory=str(tmp_path / "chroma_test"))

    pipeline = IngestionPipeline(db_service=test_db, chroma_service=test_chroma)
    result = pipeline.process_document(
        file_path=pdf_path,
        company_id="company_a",
        fiscal_year=2025,
        document_id="doc_a_2025",
    )

    assert result["total_pages"] == 3
    assert result["facts_extracted"] >= 4
    assert result["facts_saved"] >= 4
    assert result["chunks_indexed"] >= 1
    assert result["status"] == "completed"

    # Verify query facts from database
    stored_facts = test_db.query_facts(company_id="company_a", fiscal_years=[2024, 2025], verified_only=True)
    rev_2025 = next(f for f in stored_facts if f["metric"] == "revenue" and f["fiscal_year"] == 2025)
    assert rev_2025["value"] == 120000000.0

    # Verify semantic query from ChromaDB
    chroma_results = test_chroma.query("cloud demand and operating expansion", company_id="company_a")
    assert len(chroma_results) > 0
    assert "cloud" in chroma_results[0]["text"].lower()
