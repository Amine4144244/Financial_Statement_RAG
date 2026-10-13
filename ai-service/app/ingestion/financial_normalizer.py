import re
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

from app.schemas.financial_fact import (
    NormalizedFinancialFact,
    ValidationStatus,
    ScaleType,
    StatementType,
)


class FinancialNormalizer:
    """Normalizes raw financial metrics, scales, and figures into standardized facts."""

    # Standard canonical metrics and their common line-item aliases
    METRIC_ALIASES: Dict[str, List[str]] = {
        "revenue": [
            "total revenue",
            "revenues",
            "net sales",
            "total net sales",
            "sales",
            "operating revenues",
            "revenue",
        ],
        "net_income": [
            "net income",
            "net income (loss)",
            "net earnings",
            "net profit",
            "net income attributable to company",
            "net income attributable to stockholders",
        ],
        "operating_income": [
            "operating income",
            "operating profit",
            "operating earnings",
            "income from operations",
            "operating income (loss)",
        ],
        "operating_expenses": [
            "total operating expenses",
            "operating expenses",
            "operating costs and expenses",
            "total costs and expenses",
        ],
        "cost_of_revenue": [
            "cost of revenue",
            "cost of revenues",
            "cost of sales",
            "cost of goods sold",
            "cogs",
        ],
        "gross_profit": [
            "gross profit",
            "gross margin",
        ],
        "total_assets": [
            "total assets",
        ],
        "total_liabilities": [
            "total liabilities",
        ],
        "stockholders_equity": [
            "total stockholders' equity",
            "total shareholders' equity",
            "stockholders' equity",
            "shareholders' equity",
            "total equity",
        ],
        "operating_cash_flow": [
            "net cash provided by operating activities",
            "cash provided by operating activities",
            "net cash from operating activities",
            "cash generated from operations",
        ],
        "capital_expenditures": [
            "payments for property, plant and equipment",
            "capital expenditures",
            "additions to property, plant and equipment",
        ],
    }

    SCALE_MULTIPLIERS = {
        ScaleType.BILLIONS: Decimal("1000000000"),
        ScaleType.MILLIONS: Decimal("1000000"),
        ScaleType.THOUSANDS: Decimal("1000"),
        ScaleType.EXACT: Decimal("1"),
    }

    def detect_scale(self, context_text: str) -> ScaleType:
        """Inspects table headers, titles, or page snippets to detect currency scale."""
        text_lower = context_text.lower()
        if re.search(r"\b(?:in\s+billions?|amounts\s+in\s+billions?)\b", text_lower):
            return ScaleType.BILLIONS
        if re.search(r"\b(?:in\s+millions?|amounts\s+in\s+millions?|\$\s*in\s*millions?)\b", text_lower):
            return ScaleType.MILLIONS
        if re.search(r"\b(?:in\s+thousands?|amounts\s+in\s+thousands?|\$\s*in\s*thousands?)\b", text_lower):
            return ScaleType.THOUSANDS
        return ScaleType.EXACT

    def normalize_metric_name(self, raw_label: str) -> Optional[str]:
        """Maps a raw line-item label to a canonical metric key."""
        cleaned = raw_label.strip().lower()
        cleaned = re.sub(r"[:\d\.\*]+$", "", cleaned).strip()

        # Specific compound checks
        if "cost of" in cleaned or "cost of sales" in cleaned or "cost of goods" in cleaned:
            return "cost_of_revenue"

        if "sales and marketing" in cleaned or "selling and marketing" in cleaned or "selling, general" in cleaned:
            return "operating_expenses"

        # Direct exact match
        for canonical_name, aliases in self.METRIC_ALIASES.items():
            for alias in aliases:
                if alias == cleaned:
                    return canonical_name

        # Strip common prefixes like 'total ', 'consolidated '
        stripped = re.sub(r"^(?:total|consolidated)\s+", "", cleaned).strip()
        for canonical_name, aliases in self.METRIC_ALIASES.items():
            for alias in aliases:
                if alias == stripped:
                    return canonical_name

        # Word boundary matching
        for canonical_name, aliases in self.METRIC_ALIASES.items():
            for alias in aliases:
                if alias == "sales" and ("marketing" in cleaned or "general" in cleaned):
                    continue
                if re.search(rf"\b{re.escape(alias)}\b", cleaned) or re.search(rf"\b{re.escape(alias)}\b", stripped):
                    return canonical_name

        return None

    def normalize_fact(
        self,
        company_id: str,
        raw_metric: str,
        raw_value: str,
        fiscal_year: int,
        context_text: str = "",
        document_id: Optional[str] = None,
        source_id: Optional[str] = None,
        source_page: Optional[int] = None,
        statement_type: StatementType = StatementType.UNKNOWN,
        period_type: str = "FY",
        currency: str = "USD",
    ) -> Optional[NormalizedFinancialFact]:
        canonical_metric = self.normalize_metric_name(raw_metric)
        if not canonical_metric:
            return None

        # Clean value string
        cleaned_val = raw_value.replace(",", "").replace("$", "").strip()
        if not cleaned_val:
            return None

        # Detect negative format: (120) or -120
        is_negative = False
        if cleaned_val.startswith("(") and cleaned_val.endswith(")"):
            cleaned_val = cleaned_val[1:-1].strip()
            is_negative = True
        elif cleaned_val.startswith("-"):
            cleaned_val = cleaned_val[1:].strip()
            is_negative = True

        try:
            parsed_decimal = Decimal(cleaned_val)
            if is_negative:
                parsed_decimal = -parsed_decimal
        except Exception:
            return None

        # Detect scale and apply multiplier
        scale = self.detect_scale(context_text)
        multiplier = self.SCALE_MULTIPLIERS.get(scale, Decimal("1"))
        scaled_value = parsed_decimal * multiplier

        # Basic validity checks
        validation_status = ValidationStatus.VERIFIED
        notes = None

        if canonical_metric in ["revenue", "total_assets"] and scaled_value <= 0:
            validation_status = ValidationStatus.PENDING_REVIEW
            notes = f"Unusual non-positive value for {canonical_metric}: {scaled_value}"

        return NormalizedFinancialFact(
            company_id=company_id,
            document_id=document_id,
            metric=canonical_metric,
            value=scaled_value,
            raw_value=raw_value,
            currency=currency,
            unit=currency,
            scale=scale,
            fiscal_year=fiscal_year,
            period_type=period_type,
            source_id=source_id,
            source_page=source_page,
            statement_type=statement_type,
            validation_status=validation_status,
            notes=notes,
        )
