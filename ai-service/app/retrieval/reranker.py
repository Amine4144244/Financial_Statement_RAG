import re
from typing import List, Dict, Any, Optional


class SimpleReranker:
    """Reranks candidate retrieved passages based on relevance to query keywords and metadata diversity."""

    def __init__(self):
        pass

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5,
        target_years: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        q_terms = set(re.findall(r"\b\w{3,}\b", query.lower()))

        scored_candidates = []
        for cand in candidates:
            text = cand.get("text", "").lower()
            meta = cand.get("metadata", {})
            base_score = float(cand.get("relevance_score", 0.5))

            # Keyword match bonus
            term_matches = sum(1 for term in q_terms if term in text)
            keyword_score = term_matches / (len(q_terms) + 1e-5)

            # Year match bonus if targeted
            year_bonus = 0.0
            chunk_year = meta.get("fiscal_year")
            if target_years and chunk_year in target_years:
                year_bonus = 0.15

            # Combined score
            final_score = (0.5 * base_score) + (0.35 * keyword_score) + year_bonus
            scored_candidates.append({**cand, "rerank_score": final_score})

        # Sort descending by rerank_score
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Deduplicate identical or near-identical text
        seen_texts = set()
        deduped = []
        for c in scored_candidates:
            snippet = c["text"][:100].strip()
            if snippet not in seen_texts:
                seen_texts.add(snippet)
                deduped.append(c)

        return deduped[:top_k]
