import re
from typing import List, Dict, Any, Optional, Tuple

from app.schemas.document import DocumentPage, PageType
from app.schemas.financial_fact import NormalizedFinancialFact, StatementType
from app.ingestion.financial_normalizer import FinancialNormalizer


class TableExtractor:
    """Extracts financial statement rows and aligns figures with fiscal years."""

    def __init__(self):
        self.normalizer = FinancialNormalizer()

    def extract_facts_from_page(
        self,
        page: DocumentPage,
        company_id: str,
        document_id: str,
        default_fiscal_year: int,
    ) -> List[NormalizedFinancialFact]:
        facts: List[NormalizedFinancialFact] = []
        text = page.raw_text or page.text
        if not text:
            return facts

        # Determine statement type from text
        statement_type = self._detect_statement_type(text)

        # Look for year columns in the header region
        year_columns = self._detect_year_columns(text, default_fiscal_year)
        if not year_columns:
            year_columns = [default_fiscal_year]

        # Extract table rows: label followed by numerical values
        lines = text.split("\n")
        context_text = "\n".join(lines[:10])  # Header context for scale detection

        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            extracted = self._parse_line_numbers(line_stripped)
            if not extracted:
                continue

            label, numbers = extracted

            # Map the parsed numbers to the identified year columns
            for i, num_str in enumerate(numbers):
                if i < len(year_columns):
                    target_year = year_columns[i]
                else:
                    target_year = default_fiscal_year - i

                source_id = f"{document_id}_p{page.page_number}_l{line_idx+1}"
                fact = self.normalizer.normalize_fact(
                    company_id=company_id,
                    raw_metric=label,
                    raw_value=num_str,
                    fiscal_year=target_year,
                    context_text=context_text,
                    document_id=document_id,
                    source_id=source_id,
                    source_page=page.page_number,
                    statement_type=statement_type,
                )
                if fact:
                    facts.append(fact)

        return facts

    def _detect_statement_type(self, text: str) -> StatementType:
        text_lower = text.lower()
        if re.search(r"consolidated\s+statements?\s+of\s+(?:income|operations|earnings)", text_lower):
            return StatementType.INCOME_STATEMENT
        if re.search(r"consolidated\s+balance\s+sheets?|statement\s+of\s+financial\s+position", text_lower):
            return StatementType.BALANCE_SHEET
        if re.search(r"consolidated\s+statements?\s+of\s+cash\s+flows?", text_lower):
            return StatementType.CASH_FLOW
        if re.search(r"notes\s+to\s+(?:consolidated\s+)?financial\s+statements?", text_lower):
            return StatementType.NOTES
        return StatementType.UNKNOWN

    def _detect_year_columns(self, text: str, default_year: int) -> List[int]:
        """Finds 4-digit years in header lines, e.g. '2025 2024'."""
        lines = text.split("\n")[:15]
        for line in lines:
            matches = re.findall(r"\b(20[1-3]\d)\b", line)
            if len(matches) >= 2:
                # E.g. found ['2025', '2024']
                return [int(y) for y in matches]
        return [default_year, default_year - 1]

    def _parse_line_numbers(self, line: str) -> Optional[Tuple[str, List[str]]]:
        """Separates line into metric description and trailing numeric values."""
        # Match trailing numbers (including commas, parentheses, decimals, signs)
        pattern = r"^(.*?)(?:\s+([\(\-\$]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?))+$"
        match = re.search(r"^([a-zA-Z\s\(\)\/\,\.\-\&]+?)\s+((?:[\(\-\$]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?\s*)+)$", line)
        if not match:
            return None

        label = match.group(1).strip()
        num_part = match.group(2).strip()

        # Extract individual numbers from num_part
        numbers = re.findall(r"[\(\-\$]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?", num_part)
        if not numbers:
            return None

        return label, numbers
