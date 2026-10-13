from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel


class MetricType(str, Enum):
    PERCENTAGE = "percentage"
    PERCENTAGE_POINTS = "percentage_points"
    RATIO = "ratio"
    CURRENCY = "currency"


class FinancialRatioDefinition(BaseModel):
    key: str
    name: str
    category: str  # profitability, liquidity, solvency, growth
    metric_type: MetricType
    formula_description: str
    required_metrics: list[str]
    description: str


# Canonical registry of supported calculated financial indicators
SUPPORTED_RATIOS: Dict[str, FinancialRatioDefinition] = {
    "revenue_growth": FinancialRatioDefinition(
        key="revenue_growth",
        name="Year-over-Year Revenue Growth",
        category="growth",
        metric_type=MetricType.PERCENTAGE,
        formula_description="((Revenue_t - Revenue_t-1) / Revenue_t-1) * 100",
        required_metrics=["revenue"],
        description="Percentage change in total revenue between two consecutive fiscal periods.",
    ),
    "net_income_growth": FinancialRatioDefinition(
        key="net_income_growth",
        name="Year-over-Year Net Income Growth",
        category="growth",
        metric_type=MetricType.PERCENTAGE,
        formula_description="((NetIncome_t - NetIncome_t-1) / NetIncome_t-1) * 100",
        required_metrics=["net_income"],
        description="Percentage change in net income between two consecutive fiscal periods.",
    ),
    "gross_margin": FinancialRatioDefinition(
        key="gross_margin",
        name="Gross Profit Margin",
        category="profitability",
        metric_type=MetricType.PERCENTAGE,
        formula_description="(Gross Profit / Revenue) * 100",
        required_metrics=["gross_profit", "revenue"],
        description="Proportion of revenue left over after subtracting cost of goods sold.",
    ),
    "operating_margin": FinancialRatioDefinition(
        key="operating_margin",
        name="Operating Profit Margin",
        category="profitability",
        metric_type=MetricType.PERCENTAGE,
        formula_description="(Operating Income / Revenue) * 100",
        required_metrics=["operating_income", "revenue"],
        description="Measurement of what proportion of revenue is made into operating profit.",
    ),
    "net_profit_margin": FinancialRatioDefinition(
        key="net_profit_margin",
        name="Net Profit Margin",
        category="profitability",
        metric_type=MetricType.PERCENTAGE,
        formula_description="(Net Income / Revenue) * 100",
        required_metrics=["net_income", "revenue"],
        description="Percentage of revenue remaining after all operating expenses, interest, and taxes.",
    ),
    "margin_change": FinancialRatioDefinition(
        key="margin_change",
        name="Net Profit Margin Change",
        category="profitability",
        metric_type=MetricType.PERCENTAGE_POINTS,
        formula_description="Margin_t - Margin_t-1 (in percentage points)",
        required_metrics=["net_income", "revenue"],
        description="Direct change in profit margin expressed in percentage points (pp).",
    ),
    "debt_to_equity": FinancialRatioDefinition(
        key="debt_to_equity",
        name="Debt to Equity Ratio",
        category="solvency",
        metric_type=MetricType.RATIO,
        formula_description="Total Liabilities / Stockholders Equity",
        required_metrics=["total_liabilities", "stockholders_equity"],
        description="Evaluates a company's financial leverage by dividing liabilities by equity.",
    ),
    "current_ratio": FinancialRatioDefinition(
        key="current_ratio",
        name="Current Ratio",
        category="liquidity",
        metric_type=MetricType.RATIO,
        formula_description="Current Assets / Current Liabilities",
        required_metrics=["current_assets", "current_liabilities"],
        description="Measures ability to pay short-term obligations due within one year.",
    ),
}
