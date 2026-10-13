from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.services.postgres_service import DatabaseService
from app.finance.ratio_calculator import RatioCalculator
from app.ingestion.financial_normalizer import FinancialNormalizer
from app.schemas.query import CalculatedMetric


class FinancialRetriever:
    """Retrieves verified structured financial facts and computes deterministic ratios."""

    def __init__(self, db_service: Optional[DatabaseService] = None):
        self.db_service = db_service or DatabaseService()
        self.calculator = RatioCalculator()
        self.normalizer = FinancialNormalizer()

    def resolve_metric_keys(self, metric_names: List[str]) -> List[str]:
        """Resolves colloquial or alias metric names into canonical keys."""
        resolved = set()
        for name in metric_names:
            canonical = self.normalizer.normalize_metric_name(name)
            if canonical:
                resolved.add(canonical)
            else:
                # Add directly cleaned string if not in alias dictionary
                resolved.add(name.strip().lower().replace(" ", "_"))
        return list(resolved)

    def retrieve_financials(
        self,
        company_ids: List[str],
        fiscal_years: Optional[List[int]] = None,
        requested_metrics: Optional[List[str]] = None,
        include_calculated_ratios: bool = True,
        verified_only: bool = True,
    ) -> Dict[str, Any]:
        """Fetches structured facts and computes deterministic ratios for requested companies."""
        # Standardize metric keys
        canonical_metrics = self.resolve_metric_keys(requested_metrics) if requested_metrics else None

        # Add underlying metrics required for ratio calculations if needed
        query_metrics = set(canonical_metrics) if canonical_metrics else None
        if include_calculated_ratios and query_metrics is not None:
            # Add revenue, net_income, operating_income to compute margins if asked
            query_metrics.update(["revenue", "net_income", "operating_income", "gross_profit", "total_liabilities", "stockholders_equity"])

        all_facts: List[Dict[str, Any]] = []
        facts_by_comp_year: Dict[str, Dict[int, Dict[str, Decimal]]] = {}

        for comp_id in company_ids:
            facts = self.db_service.query_facts(
                company_id=comp_id,
                fiscal_years=fiscal_years,
                metrics=list(query_metrics) if query_metrics else None,
                verified_only=verified_only,
            )
            all_facts.extend(facts)

            if comp_id not in facts_by_comp_year:
                facts_by_comp_year[comp_id] = {}

            for f in facts:
                yr = f["fiscal_year"]
                if yr not in facts_by_comp_year[comp_id]:
                    facts_by_comp_year[comp_id][yr] = {}
                facts_by_comp_year[comp_id][yr][f["metric"]] = Decimal(str(f["value"]))

        # Compute ratios deterministically for each company
        all_calculations: List[CalculatedMetric] = []
        if include_calculated_ratios:
            for comp_id, yearly_facts in facts_by_comp_year.items():
                calcs = self.calculator.compute_all_metrics(comp_id, yearly_facts)
                all_calculations.extend(calcs)

        return {
            "facts": all_facts,
            "facts_by_company_and_year": facts_by_comp_year,
            "calculations": all_calculations,
        }
