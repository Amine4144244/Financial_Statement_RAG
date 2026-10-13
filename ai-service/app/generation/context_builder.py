from typing import List, Dict, Any, Optional

from app.schemas.query import CalculatedMetric, Citation


class ContextBuilder:
    """Assembles structured financial facts, calculations, and narrative passages into a prompt context."""

    @staticmethod
    def build_evidence_context(
        question: str,
        facts: List[Dict[str, Any]],
        calculations: List[CalculatedMetric],
        passages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # 1. Format facts table
        fact_lines = []
        for f in facts:
            val_formatted = f"{f['value']:,.2f}"
            scale_note = f" ({f.get('scale', 'exact')})" if f.get('scale') != 'exact' else ""
            fact_lines.append(
                f"- {f['company_id']} | FY{f['fiscal_year']} | {f['metric']}: {val_formatted} {f.get('currency', 'USD')}{scale_note} (Page {f.get('source_page', 'N/A')})"
            )
        facts_text = "\n".join(fact_lines) if fact_lines else "No verified financial facts retrieved."

        # 2. Format calculated metrics
        calc_lines = []
        for c in calculations:
            calc_lines.append(
                f"- {c.name.replace('_', ' ').title()} ({c.company_id} FY{c.fiscal_year}): {c.value:.2f}{c.unit} [Formula: {c.formula}]"
            )
        calc_text = "\n".join(calc_lines) if calc_lines else "No ratios calculated."

        # 3. Format narrative passages with citations
        passage_lines = []
        for idx, p in enumerate(passages):
            meta = p.get("metadata", {})
            citation_tag = f"[{meta.get('document_id', 'doc')}_Page_{meta.get('page_start', 1)}]"
            passage_lines.append(
                f"Source {idx+1} {citation_tag} (FY{meta.get('fiscal_year', 'N/A')} - {meta.get('section', 'Section')}):\n\"{p.get('text', '').strip()}\""
            )
        passages_text = "\n\n".join(passage_lines) if passage_lines else "No narrative passages retrieved."

        # Prompt assembly
        system_prompt = (
            "You are a professional Financial Statement Analysis Assistant.\n"
            "Your objective is to provide a clear, factual, and strictly evidence-backed financial analysis.\n\n"
            "STRICT RULES:\n"
            "1. Use ONLY the supplied financial figures, calculated ratios, and retrieved excerpts.\n"
            "2. Never calculate or estimate numbers on your own; rely strictly on the provided calculations.\n"
            "3. Clearly distinguish between percentage growth (e.g. 20% YoY) and percentage-point margin changes (e.g. 0.0 pp).\n"
            "4. Cite sources using [DocID_Page_X] format for every factual claim or management explanation.\n"
            "5. If the retrieved evidence does not explain a financial change, explicitly state that the documents do not establish the full reason.\n"
            "6. Structure your response with: Executive Summary, Verified Metrics & Calculations, Management Explanations, and Conclusion."
        )

        user_prompt = (
            f"QUESTION:\n{question}\n\n"
            f"--- VERIFIED FINANCIAL FACTS ---\n{facts_text}\n\n"
            f"--- DETERMINISTIC RATIOS & CALCULATIONS ---\n{calc_text}\n\n"
            f"--- RETRIEVED DOCUMENT EXCERPTS ---\n{passages_text}\n\n"
            f"Please generate your structured financial analysis based solely on the above evidence."
        )

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "facts_summary": facts_text,
            "calculations_summary": calc_text,
            "passages_count": len(passages),
        }
