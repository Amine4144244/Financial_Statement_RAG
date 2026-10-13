from enum import Enum
from typing import List, Dict, Any

from app.schemas.query import StructuredQuery, QueryIntent


class RouteDecision(str, Enum):
    SQL_ONLY = "sql_only"
    SEMANTIC_ONLY = "semantic_only"
    HYBRID = "hybrid"


class QueryRouter:
    """Routes structured queries to the appropriate retrieval and execution pipelines."""

    @staticmethod
    def route_query(structured_query: StructuredQuery) -> RouteDecision:
        if structured_query.requires_sql and structured_query.requires_semantic_search:
            return RouteDecision.HYBRID
        elif structured_query.requires_sql:
            return RouteDecision.SQL_ONLY
        elif structured_query.requires_semantic_search:
            return RouteDecision.SEMANTIC_ONLY
        else:
            return RouteDecision.HYBRID

    @staticmethod
    def generate_semantic_subqueries(structured_query: StructuredQuery) -> List[str]:
        """Generates targeted subqueries for semantic vector search."""
        subqueries = [structured_query.original_question]
        companies = ", ".join(structured_query.company_ids)
        years = " ".join(str(y) for y in structured_query.fiscal_years)

        # Add targeted narrative queries
        if structured_query.metrics:
            metrics_str = " ".join(structured_query.metrics)
            subqueries.append(f"{companies} {years} {metrics_str} changes drivers and management discussion")

        subqueries.append(f"{companies} {years} operational results and business factors")
        return list(dict.fromkeys(subqueries))  # Deduplicate preserving order
