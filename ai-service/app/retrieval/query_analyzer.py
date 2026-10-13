import re
from typing import List, Dict, Optional, Tuple, Set

from app.schemas.query import StructuredQuery, QueryIntent
from app.ingestion.financial_normalizer import FinancialNormalizer


class QueryAnalyzer:
    """Analyzes natural language financial queries into structured parameters."""

    KNOWN_COMPANIES = {
        "company a": "company_a",
        "company_a": "company_a",
        "microsoft": "msft",
        "msft": "msft",
        "apple": "aapl",
        "aapl": "aapl",
        "amazon": "amzn",
        "amzn": "amzn",
        "google": "googl",
        "alphabet": "googl",
        "googl": "googl",
    }

    def __init__(self):
        self.normalizer = FinancialNormalizer()

    def analyze_query(self, question: str) -> StructuredQuery:
        q_lower = question.lower()

        # 1. Extract companies
        extracted_companies = self._extract_companies(q_lower)

        # 2. Extract fiscal years
        extracted_years = self._extract_years(q_lower)

        # 3. Extract metrics
        extracted_metrics = self._extract_metrics(q_lower)

        # 4. Determine intent and flags
        intent, requires_sql, requires_semantic, requires_calc = self._determine_intent(
            q_lower, extracted_metrics, len(extracted_years)
        )

        return StructuredQuery(
            original_question=question,
            intent=intent,
            company_ids=extracted_companies,
            fiscal_years=extracted_years,
            metrics=extracted_metrics,
            requires_sql=requires_sql,
            requires_semantic_search=requires_semantic,
            requires_calculation=requires_calc,
        )

    def _extract_companies(self, text: str) -> List[str]:
        companies = set()
        for name, comp_id in self.KNOWN_COMPANIES.items():
            if re.search(r"\b" + re.escape(name) + r"\b", text):
                companies.add(comp_id)
        # Default fallback if question says "the company" or generic
        if not companies:
            companies.add("company_a")
        return sorted(list(companies))

    def _extract_years(self, text: str) -> List[int]:
        # Match 4-digit years between 2000 and 2035
        matches = re.findall(r"\b(20[0-3]\d)\b", text)
        years = sorted(list({int(y) for y in matches}))
        return years

    def _extract_metrics(self, text: str) -> List[str]:
        metrics = set()
        for canonical, aliases in self.normalizer.METRIC_ALIASES.items():
            for alias in aliases:
                if re.search(r"\b" + re.escape(alias) + r"\b", text):
                    metrics.add(canonical)
                    break

        # Additional check for ratios and margins
        if re.search(r"\b(?:net\s+profit\s+margin|net\s+margin|profit\s+margin)\b", text):
            metrics.add("net_income")
            metrics.add("revenue")
        if re.search(r"\b(?:operating\s+margin)\b", text):
            metrics.add("operating_income")
            metrics.add("revenue")
        if re.search(r"\b(?:gross\s+margin)\b", text):
            metrics.add("gross_profit")
            metrics.add("revenue")

        return sorted(list(metrics))

    def _determine_intent(
        self, text: str, metrics: List[str], num_years: int
    ) -> Tuple[QueryIntent, bool, bool, bool]:
        narrative_patterns = [
            r"\bwhy\b",
            r"\bexplain[a-z]*\b",
            r"\breason[a-z]*\b",
            r"\bfactor[a-z]*\b",
            r"\bdriver[a-z]*\b",
            r"\bcause[a-z]*\b",
            r"\brisk[a-z]*\b",
            r"\bstrateg[a-z]*\b",
            r"\bcommentar[a-z]*\b",
        ]
        calculation_patterns = [
            r"\bgrowth\b",
            r"\bmargin[a-z]*\b",
            r"\bratio[a-z]*\b",
            r"\bchange[a-z]*\b",
            r"\bcompar[a-z]*\b",
            r"\bcalculat[a-z]*\b",
            r"\bimprov[a-z]*\b",
            r"\bdeclin[a-z]*\b",
            r"\bpercentage[a-z]*\b",
        ]

        has_narrative = any(re.search(pat, text) for pat in narrative_patterns)
        has_calculation = any(re.search(pat, text) for pat in calculation_patterns) or (num_years > 1)
        has_metrics = bool(metrics) or bool(re.search(r"\b(?:financials?|numbers?|revenue|income|expenses?|profit)\b", text))

        if has_narrative and (has_calculation or has_metrics):
            return QueryIntent.HYBRID_COMPARISON, True, True, True
        elif has_narrative:
            return QueryIntent.NARRATIVE_EXPLANATION, False, True, False
        elif has_calculation:
            return QueryIntent.RATIO_CALCULATION, True, False, True
        elif has_metrics:
            return QueryIntent.FACTUAL_METRIC, True, False, False

        # Default fallback: hybrid
        return QueryIntent.HYBRID_COMPARISON, True, True, True
