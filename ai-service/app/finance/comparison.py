from decimal import Decimal
from typing import Dict, List, Any, Optional

from app.finance.ratio_calculator import RatioCalculator


class FinancialComparison:
    """Provides comparative financial analysis across fiscal years and companies."""

    @staticmethod
    def compare_periods(
        company_id: str,
        base_year: int,
        target_year: int,
        metrics_data: Dict[int, Dict[str, Decimal]],
    ) -> Dict[str, Any]:
        """Compares financial metrics between two fiscal years for the same company."""
        base_facts = metrics_data.get(base_year, {})
        target_facts = metrics_data.get(target_year, {})

        comparison_rows = []
        all_metrics = set(base_facts.keys()) | set(target_facts.keys())

        for metric in sorted(all_metrics):
            base_val = base_facts.get(metric)
            target_val = target_facts.get(metric)

            row = {
                "metric": metric,
                "base_year": base_year,
                "base_value": float(base_val) if base_val is not None else None,
                "target_year": target_year,
                "target_value": float(target_val) if target_val is not None else None,
                "absolute_change": float(target_val - base_val) if (target_val is not None and base_val is not None) else None,
                "percentage_change": float(RatioCalculator.yoy_growth(target_val, base_val)) if (target_val is not None and base_val is not None) else None,
            }
            comparison_rows.append(row)

        # Margin comparisons
        base_rev = base_facts.get("revenue")
        target_rev = target_facts.get("revenue")
        base_ni = base_facts.get("net_income")
        target_ni = target_facts.get("net_income")

        base_margin = RatioCalculator.profit_margin(base_ni, base_rev) if (base_rev and base_ni) else None
        target_margin = RatioCalculator.profit_margin(target_ni, target_rev) if (target_rev and target_ni) else None
        margin_diff_pp = RatioCalculator.percentage_point_diff(target_margin, base_margin) if (base_margin and target_margin) else None

        return {
            "company_id": company_id,
            "base_year": base_year,
            "target_year": target_year,
            "rows": comparison_rows,
            "margins": {
                "base_net_margin": float(base_margin) if base_margin is not None else None,
                "target_net_margin": float(target_margin) if target_margin is not None else None,
                "margin_change_percentage_points": float(margin_diff_pp) if margin_diff_pp is not None else None,
            },
        }

    @staticmethod
    def prepare_chart_series(
        company_id: str,
        facts_by_year: Dict[int, Dict[str, Decimal]],
    ) -> List[Dict[str, Any]]:
        """Prepares annual data points formatted for Recharts or dashboard graphs."""
        series = []
        for year in sorted(facts_by_year.keys()):
            data = facts_by_year[year]
            rev = data.get("revenue")
            ni = data.get("net_income")
            op_inc = data.get("operating_income")

            margin = RatioCalculator.profit_margin(ni, rev) if (rev and ni) else None

            point = {
                "year": year,
                "revenue": float(rev) if rev is not None else 0.0,
                "net_income": float(ni) if ni is not None else 0.0,
                "operating_income": float(op_inc) if op_inc is not None else 0.0,
                "net_profit_margin": float(margin) if margin is not None else 0.0,
            }
            series.append(point)
        return series
