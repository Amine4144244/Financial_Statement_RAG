import re
from typing import List, Optional


class TextCleaner:
    """Cleans and normalizes extracted narrative text from financial PDF reports."""

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        # Normalize special unicode spaces and dashes
        cleaned = text.replace("\u00a0", " ").replace("\u2013", "-").replace("\u2014", "-")

        # Fix hyphenated words broken across line breaks (e.g. "profita-\nbility" -> "profitability")
        cleaned = re.sub(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)", r"\1\2", cleaned)

        # Remove form feed characters
        cleaned = cleaned.replace("\x0c", " ")

        # Normalize line breaks while keeping paragraph separation
        lines = [line.strip() for line in cleaned.split("\n")]
        
        # Filter out standalone page number lines or empty headers
        filtered_lines = []
        for line in lines:
            # Skip lines that are just numbers like "42" or "Page 42"
            if re.match(r"^(?:page\s+)?\d+\s*$", line, re.IGNORECASE):
                continue
            # Skip common repeated confidentiality / disclaimer lines
            if re.match(r"^(?:table of contents|all rights reserved|confidential)\s*$", line, re.IGNORECASE):
                continue
            filtered_lines.append(line)

        # Re-join lines and normalize consecutive spaces
        reconstructed = "\n".join(filtered_lines)
        reconstructed = re.sub(r"[ \t]+", " ", reconstructed)
        reconstructed = re.sub(r"\n{3,}", "\n\n", reconstructed)

        return reconstructed.strip()

    @staticmethod
    def identify_section_header(line: str) -> Optional[str]:
        """Detects whether a line is likely a major financial section header."""
        normalized = line.strip().lower()
        if not normalized or len(normalized) > 90:
            return None

        section_patterns = [
            (r"item\s+1a[\.:\s\-]+risk\s+factors", "risk_factors"),
            (r"item\s+7[\.:\s\-]+management'?s\s+discussion", "mda"),
            (r"management'?s\s+discussion\s+and\s+analysis", "mda"),
            (r"consolidated\s+statements?\s+of\s+(?:income|operations|earnings)", "income_statement"),
            (r"consolidated\s+balance\s+sheets?", "balance_sheet"),
            (r"consolidated\s+statements?\s+of\s+cash\s+flows?", "cash_flow"),
            (r"notes\s+to\s+(?:consolidated\s+)?financial\s+statements?", "notes"),
            (r"business\s+overview|overview\s+of\s+the\s+business", "business_overview"),
        ]

        for pattern, section_key in section_patterns:
            if re.search(pattern, normalized):
                return section_key

        return None
