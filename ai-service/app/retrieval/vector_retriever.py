from typing import List, Dict, Any, Optional

from app.services.chroma_service import ChromaService
from app.retrieval.reranker import SimpleReranker
from app.schemas.query import Citation


class VectorRetriever:
    """Retrieves narrative passages from ChromaDB with metadata filtering and reranking."""

    def __init__(self, chroma_service: Optional[ChromaService] = None):
        self.chroma_service = chroma_service or ChromaService()
        self.reranker = SimpleReranker()

    def retrieve_passages(
        self,
        query: str,
        subqueries: Optional[List[str]] = None,
        company_ids: Optional[List[str]] = None,
        fiscal_years: Optional[List[int]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        queries_to_run = subqueries if subqueries else [query]
        candidates = []

        # If multiple companies, query each; otherwise query with first company filter
        target_company = company_ids[0] if company_ids else None

        for sq in queries_to_run:
            if fiscal_years:
                for yr in fiscal_years:
                    results = self.chroma_service.query(
                        query_text=sq,
                        n_results=top_k * 2,
                        company_id=target_company,
                        fiscal_year=yr,
                    )
                    candidates.extend(results)
            else:
                results = self.chroma_service.query(
                    query_text=sq,
                    n_results=top_k * 2,
                    company_id=target_company,
                )
                candidates.extend(results)

        # Rerank and select top-k passages
        reranked = self.reranker.rerank(
            query=query,
            candidates=candidates,
            top_k=top_k,
            target_years=fiscal_years,
        )

        return reranked

    @staticmethod
    def to_citations(passages: List[Dict[str, Any]]) -> List[Citation]:
        citations = []
        for p in passages:
            meta = p.get("metadata", {})
            citations.append(
                Citation(
                    document_id=meta.get("document_id", "unknown_doc"),
                    company_id=meta.get("company_id", "unknown_company"),
                    fiscal_year=int(meta.get("fiscal_year", 0)),
                    page_number=int(meta.get("page_start", 1)),
                    section=meta.get("section", "narrative"),
                    chunk_id=p.get("chunk_id"),
                    excerpt=p.get("text", "")[:300] + ("..." if len(p.get("text", "")) > 300 else ""),
                )
            )
        return citations
