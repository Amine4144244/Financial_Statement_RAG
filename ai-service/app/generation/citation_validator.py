import re
from typing import List, Dict, Any, Tuple, Optional

from app.schemas.query import Citation


class CitationValidator:
    """Validates that citations referenced in generated responses correspond to retrieved passages or facts."""

    @staticmethod
    def validate_citations(
        generated_text: str,
        retrieved_citations: List[Citation],
        retrieved_facts: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[List[Citation], List[str]]:
        warnings = []
        valid_citations = []

        # Find citation tags like [doc_Page_42] or [Page 42]
        referenced_pages = set()
        for match in re.finditer(r"(?:\[.*?page[_\s]+(\d+).*?\]|page\s+(\d+))", generated_text, re.IGNORECASE):
            pg = match.group(1) or match.group(2)
            if pg:
                referenced_pages.add(int(pg))

        available_pages: Dict[int, Citation] = {c.page_number: c for c in retrieved_citations}

        # Also register pages from verified relational financial facts
        fact_citations: Dict[int, Citation] = {}
        if retrieved_facts:
            for f in retrieved_facts:
                pg = f.get("source_page")
                if pg and pg not in available_pages and pg not in fact_citations:
                    fact_citations[pg] = Citation(
                        document_id=f.get("document_id") or "financial_statement",
                        company_id=f.get("company_id", ""),
                        fiscal_year=f.get("fiscal_year", 2025),
                        page_number=pg,
                        section=f.get("statement_type", "financial_statement"),
                        chunk_id=f"fact_{f.get('metric')}_{pg}",
                        excerpt=f"Verified statement fact: {f.get('metric')} = {f.get('value'):,.2f} {f.get('currency', 'USD')} ({f.get('statement_type', 'financial_statement')})"
                    )

        combined_pages = {**available_pages, **fact_citations}

        for pg in referenced_pages:
            if pg in combined_pages:
                valid_citations.append(combined_pages[pg])
            else:
                warnings.append(f"Citation refers to Page {pg}, which was not in the retrieved evidence set.")

        # If generated text did not explicitly tag brackets, include all retrieved citations as supporting evidence
        if not valid_citations:
            valid_citations = list(combined_pages.values())

        return valid_citations, warnings
