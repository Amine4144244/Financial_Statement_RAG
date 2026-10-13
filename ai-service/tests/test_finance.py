import pytest
from decimal import Decimal

from app.finance.ratio_calculator import RatioCalculator
from app.finance.metrics import SUPPORTED_RATIOS
from app.finance.comparison import FinancialComparison
from app.retrieval.financial_retriever import FinancialRetriever
from app.services.postgres_service import DatabaseService
from app.schemas.financial_fact import NormalizedFinancialFact, ValidationStatus, ScaleType


def test_ratio_calculator_basic_metrics():
    # Scenario: FY2024 Revenue = $100M, Net Income = $15M
    #           FY2025 Revenue = $120M, Net Income = $18M
    rev_2024 = Decimal("100000000")
    rev_2025 = Decimal("120000000")
    ni_2024 = Decimal("15000000")
    ni_2025 = Decimal("18000000")

    # 1. YoY Revenue Growth
    rev_growth = RatioCalculator.yoy_growth(rev_2025, rev_2024)
    assert rev_growth == Decimal("20.00")

    # 2. YoY Net Income Growth
    ni_growth = RatioCalculator.yoy_growth(ni_2025, ni_2024)
    assert ni_growth == Decimal("20.00")

    # 3. Net Profit Margin
    margin_2024 = RatioCalculator.profit_margin(ni_2024, rev_2024)
    margin_2025 = RatioCalculator.profit_margin(ni_2025, rev_2025)
    assert margin_2024 == Decimal("15.00")
    assert margin_2025 == Decimal("15.00")

    # 4. Net Margin Change in Percentage Points (pp)
    margin_diff_pp = RatioCalculator.percentage_point_diff(margin_2025, margin_2024)
    assert margin_diff_pp == Decimal("0.00")


def test_edge_cases_and_zero_division():
    # Division by zero revenue
    assert RatioCalculator.profit_margin(Decimal("1000"), Decimal("0")) is None

    # Zero previous baseline growth
    assert RatioCalculator.yoy_growth(Decimal("1000"), Decimal("0")) is None

    # None values
    assert RatioCalculator.profit_margin(None, Decimal("1000")) is None
    assert RatioCalculator.yoy_growth(Decimal("1000"), None) is None

    # Debt-to-Equity with negative/zero equity
    assert RatioCalculator.debt_to_equity(Decimal("5000"), Decimal("0")) is None
    assert RatioCalculator.debt_to_equity(Decimal("5000"), Decimal("-1000")) is None
    assert RatioCalculator.debt_to_equity(Decimal("5000"), Decimal("2500")) == Decimal("2.00")

    # Current ratio
    assert RatioCalculator.current_ratio(Decimal("2000"), Decimal("1000")) == Decimal("2.00")
    assert RatioCalculator.current_ratio(Decimal("2000"), Decimal("0")) is None


def test_financial_retriever_with_db(tmp_path):
    # Setup test DB and seed facts
    db = DatabaseService(db_url=f"sqlite:///{tmp_path}/finance_test.db")
    facts = [
        NormalizedFinancialFact(
            company_id="company_test",
            metric="revenue",
            value=Decimal("100000000"),
            fiscal_year=2024,
            validation_status=ValidationStatus.VERIFIED,
        ),
        NormalizedFinancialFact(
            company_id="company_test",
            metric="revenue",
            value=Decimal("120000000"),
            fiscal_year=2025,
            validation_status=ValidationStatus.VERIFIED,
        ),
        NormalizedFinancialFact(
            company_id="company_test",
            metric="net_income",
            value=Decimal("15000000"),
            fiscal_year=2024,
            validation_status=ValidationStatus.VERIFIED,
        ),
        NormalizedFinancialFact(
            company_id="company_test",
            metric="net_income",
            value=Decimal("18000000"),
            fiscal_year=2025,
            validation_status=ValidationStatus.VERIFIED,
        ),
    ]
    db.save_facts(facts)

    retriever = FinancialRetriever(db_service=db)

    # Test alias resolution: 'net sales' -> 'revenue', 'net profit' -> 'net_income'
    keys = retriever.resolve_metric_keys(["Net Sales", "Total Net Profit"])
    assert "revenue" in keys
    assert "net_income" in keys

    # Test retrieval and automatic deterministic calculations
    res = retriever.retrieve_financials(
        company_ids=["company_test"],
        fiscal_years=[2024, 2025],
        requested_metrics=["revenue", "net_income"],
        include_calculated_ratios=True,
    )

    assert len(res["facts"]) == 4
    calculations = res["calculations"]
    assert len(calculations) > 0

    # Verify computed ratio objects
    growth_calc = next(c for c in calculations if c.name == "revenue_growth")
    assert growth_calc.value == 20.0
    assert growth_calc.fiscal_year == 2025

    margin_calc_2025 = next(c for c in calculations if c.name == "net_profit_margin" and c.fiscal_year == 2025)
    assert margin_calc_2025.value == 15.0

    margin_change_calc = next(c for c in calculations if c.name == "net_margin_change_pp")
    assert margin_change_calc.value == 0.0


def test_financial_comparison():
    data = {
        2024: {"revenue": Decimal("100000000"), "net_income": Decimal("15000000")},
        2025: {"revenue": Decimal("120000000"), "net_income": Decimal("18000000")},
    }

    comp = FinancialComparison.compare_periods(
        company_id="company_a",
        base_year=2024,
        target_year=2025,
        metrics_data=data,
    )

    assert comp["company_id"] == "company_a"
    assert comp["margins"]["base_net_margin"] == 15.0
    assert comp["margins"]["target_net_margin"] == 15.0
    assert comp["margins"]["margin_change_percentage_points"] == 0.0

    # Chart series
    series = FinancialComparison.prepare_chart_series("company_a", data)
    assert len(series) == 2
    assert series[0]["year"] == 2024
    assert series[0]["revenue"] == 100000000.0
    assert series[1]["year"] == 2025
    assert series[1]["revenue"] == 120000000.0
