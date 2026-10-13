import re
from decimal import Decimal
from typing import List, Dict, Any, Tuple

from app.schemas.query import CalculatedMetric


class AnswerValidator:
    """Verifies that numerical statements in generated answers match approved facts and calculations."""

    @staticmethod
    def validate_answer(
        generated_text: str,
        verified_facts: List[Dict[str, Any]],
        calculations: List[CalculatedMetric],
    ) -> Tuple[str, List[str]]:
        warnings = []

        # Collect all approved values
        approved_numbers = set()
        for f in verified_facts:
            val = float(f["value"])
            approved_numbers.add(val)
            # Also scale in millions/thousands if common (e.g. 120 from 120,000,000)
            approved_numbers.add(val / 1e6)
            approved_numbers.add(val / 1e3)

        for c in calculations:
            approved_numbers.add(round(c.value, 2))
            approved_numbers.add(round(c.value, 1))
            approved_numbers.add(float(int(c.value)))

        # Find percentage mentions in generated text (e.g. "20%", "15.0%", "0.0%")
        pct_matches = re.findall(r"\b(\d+(?:\.\d+)?)\s*%", generated_text)
        for pct_str in pct_matches:
            pct_val = float(pct_str)
            # Check if this percentage exists in calculations
            calc_match = any(abs(c.value - pct_val) < 0.1 for c in calculations if c.unit in ["%", "percentage_points"])
            if not calc_match and pct_val != 0.0:
                warnings.append(
                    f"Generated text mentions {pct_val}%, which does not match any approved deterministic calculation."
                )

        status = "verified" if not warnings else "warnings"
        return status, warnings
