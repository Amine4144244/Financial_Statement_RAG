from decimal import Decimal, ROUND_HALF_UP, DivisionByZero, InvalidOperation
from typing import Dict, Any, Optional, List, Tuple
from app.schemas.query import CalculatedMetric


class CalculationError(Exception):
    """Custom exception raised when financial arithmetic cannot be completed."""
    pass


class RatioCalculator:
    """Deterministic financial ratio calculator using exact Decimal arithmetic."""

    @staticmethod
    def to_decimal(val: Any) -> Optional[Decimal]:
        if val is None:
            return None
        if isinstance(val, Decimal):
            return val
        try:
            return Decimal(str(val))
        except (InvalidOperation, ValueError):
            return None

    @classmethod
    def yoy_growth(cls, current_val: Any, previous_val: Any, places: int = 2) -> Optional[Decimal]:
        """Calculates YoY percentage growth: ((curr - prev) / abs(prev)) * 100."""
        curr = cls.to_decimal(current_val)
        prev = cls.to_decimal(previous_val)

        if curr is None or prev is None:
            return None
        if prev == Decimal("0"):
            return None  # Cannot compute percentage growth from a zero baseline

        change = curr - prev
        # Use abs(prev) so that moving from -10 to +10 is positive growth
        growth = (change / abs(prev)) * Decimal("100")
        return growth.quantize(Decimal(f"1e-{places}"), rounding=ROUND_HALF_UP)

    @classmethod
    def profit_margin(cls, numerator: Any, revenue: Any, places: int = 2) -> Optional[Decimal]:
        """Calculates margin percentage: (numerator / revenue) * 100."""
        num = cls.to_decimal(numerator)
        rev = cls.to_decimal(revenue)

        if num is None or rev is None:
            return None
        if rev == Decimal("0"):
            return None  # Division by zero revenue is undefined

        margin = (num / rev) * Decimal("100")
        return margin.quantize(Decimal(f"1e-{places}"), rounding=ROUND_HALF_UP)

    @classmethod
    def percentage_point_diff(cls, current_margin: Any, previous_margin: Any, places: int = 2) -> Optional[Decimal]:
        """Calculates difference in margins in percentage points (pp): current - previous."""
        curr = cls.to_decimal(current_margin)
        prev = cls.to_decimal(previous_margin)

        if curr is None or prev is None:
            return None

        diff = curr - prev
        return diff.quantize(Decimal(f"1e-{places}"), rounding=ROUND_HALF_UP)

    @classmethod
    def debt_to_equity(cls, total_liabilities: Any, stockholders_equity: Any, places: int = 2) -> Optional[Decimal]:
        """Calculates Debt-to-Equity ratio: total_liabilities / stockholders_equity."""
        liab = cls.to_decimal(total_liabilities)
        eq = cls.to_decimal(stockholders_equity)

        if liab is None or eq is None or eq <= Decimal("0"):
            return None

        ratio = liab / eq
        return ratio.quantize(Decimal(f"1e-{places}"), rounding=ROUND_HALF_UP)

    @classmethod
    def current_ratio(cls, current_assets: Any, current_liabilities: Any, places: int = 2) -> Optional[Decimal]:
        """Calculates Current Ratio: current_assets / current_liabilities."""
        ca = cls.to_decimal(current_assets)
        cl = cls.to_decimal(current_liabilities)

        if ca is None or cl is None or cl <= Decimal("0"):
            return None

        ratio = ca / cl
        return ratio.quantize(Decimal(f"1e-{places}"), rounding=ROUND_HALF_UP)

    @classmethod
    def compute_all_metrics(
        cls,
        company_id: str,
        facts_by_year: Dict[int, Dict[str, Decimal]],
    ) -> List[CalculatedMetric]:
        """Computes all applicable financial indicators across years for a company."""
        results: List[CalculatedMetric] = []
        sorted_years = sorted(facts_by_year.keys())

        for idx, year in enumerate(sorted_years):
            data = facts_by_year[year]
            rev = data.get("revenue")
            net_inc = data.get("net_income")
            op_inc = data.get("operating_income")
            gross_p = data.get("gross_profit")
            liab = data.get("total_liabilities")
            eq = data.get("stockholders_equity")

            # 1. Net Profit Margin
            if rev is not None and net_inc is not None:
                npm = cls.profit_margin(net_inc, rev)
                if npm is not None:
                    results.append(
                        CalculatedMetric(
                            name="net_profit_margin",
                            company_id=company_id,
                            fiscal_year=year,
                            value=float(npm),
                            unit="%",
                            formula="(Net Income / Revenue) * 100",
                            details={"revenue": float(rev), "net_income": float(net_inc)},
                        )
                    )

            # 2. Operating Margin
            if rev is not None and op_inc is not None:
                op_m = cls.profit_margin(op_inc, rev)
                if op_m is not None:
                    results.append(
                        CalculatedMetric(
                            name="operating_margin",
                            company_id=company_id,
                            fiscal_year=year,
                            value=float(op_m),
                            unit="%",
                            formula="(Operating Income / Revenue) * 100",
                            details={"revenue": float(rev), "operating_income": float(op_inc)},
                        )
                    )

            # 3. Gross Margin
            if rev is not None and gross_p is not None:
                gm = cls.profit_margin(gross_p, rev)
                if gm is not None:
                    results.append(
                        CalculatedMetric(
                            name="gross_margin",
                            company_id=company_id,
                            fiscal_year=year,
                            value=float(gm),
                            unit="%",
                            formula="(Gross Profit / Revenue) * 100",
                            details={"revenue": float(rev), "gross_profit": float(gross_p)},
                        )
                    )

            # 4. Debt to Equity
            if liab is not None and eq is not None:
                de = cls.debt_to_equity(liab, eq)
                if de is not None:
                    results.append(
                        CalculatedMetric(
                            name="debt_to_equity",
                            company_id=company_id,
                            fiscal_year=year,
                            value=float(de),
                            unit="x",
                            formula="Total Liabilities / Stockholders Equity",
                            details={"total_liabilities": float(liab), "stockholders_equity": float(eq)},
                        )
                    )

            # 5. YoY Variations (if previous year exists)
            if idx > 0:
                prev_year = sorted_years[idx - 1]
                prev_data = facts_by_year[prev_year]

                # Revenue YoY Growth
                prev_rev = prev_data.get("revenue")
                if rev is not None and prev_rev is not None:
                    rev_growth = cls.yoy_growth(rev, prev_rev)
                    if rev_growth is not None:
                        results.append(
                            CalculatedMetric(
                                name="revenue_growth",
                                company_id=company_id,
                                fiscal_year=year,
                                value=float(rev_growth),
                                unit="%",
                                formula=f"((Revenue_{year} - Revenue_{prev_year}) / Revenue_{prev_year}) * 100",
                                details={"current_revenue": float(rev), "previous_revenue": float(prev_rev)},
                            )
                        )

                # Net Income YoY Growth
                prev_ni = prev_data.get("net_income")
                if net_inc is not None and prev_ni is not None:
                    ni_growth = cls.yoy_growth(net_inc, prev_ni)
                    if ni_growth is not None:
                        results.append(
                            CalculatedMetric(
                                name="net_income_growth",
                                company_id=company_id,
                                fiscal_year=year,
                                value=float(ni_growth),
                                unit="%",
                                formula=f"((NetIncome_{year} - NetIncome_{prev_year}) / NetIncome_{prev_year}) * 100",
                                details={"current_net_income": float(net_inc), "previous_net_income": float(prev_ni)},
                            )
                        )

                # Net Margin Change (in percentage points)
                curr_margin = cls.profit_margin(net_inc, rev) if rev and net_inc else None
                prev_margin = cls.profit_margin(prev_ni, prev_rev) if prev_rev and prev_ni else None
                if curr_margin is not None and prev_margin is not None:
                    diff_pp = cls.percentage_point_diff(curr_margin, prev_margin)
                    results.append(
                        CalculatedMetric(
                            name="net_margin_change_pp",
                            company_id=company_id,
                            fiscal_year=year,
                            value=float(diff_pp),
                            unit="percentage_points",
                            formula=f"NetMargin_{year} - NetMargin_{prev_year}",
                            details={"current_margin": float(curr_margin), "previous_margin": float(prev_margin)},
                        )
                    )

        return results
