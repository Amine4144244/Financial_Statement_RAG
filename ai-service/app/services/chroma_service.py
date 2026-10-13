import os
from typing import List, Dict, Any, Optional

from app.ingestion.chunker import DocumentChunk


class ChromaService:
    """Manages vector storage, embedding indexing, and filtered semantic search."""

    def __init__(
        self,
        persist_directory: str = "./chroma_data",
        collection_name: str = "financial_reports",
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._init_db()

    def _init_db(self):
        try:
            import chromadb
            from chromadb.config import Settings

            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Financial reports narrative chunks"}
            )
        except Exception as e:
            # Keep client as None for graceful fallback during testing
            self.client = None
            self.collection = None

    def upsert_chunks(self, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            return 0

        if not self.collection:
            self._init_db()
            if not self.collection:
                raise RuntimeError("ChromaDB collection is not available.")

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "company_id": str(chunk.company_id),
                "fiscal_year": int(chunk.fiscal_year),
                "document_id": str(chunk.document_id),
                "section": str(chunk.section),
                "page_start": int(chunk.page_start),
                "page_end": int(chunk.page_end),
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def query(
        self,
        query_text: str,
        n_results: int = 10,
        company_id: Optional[str] = None,
        fiscal_year: Optional[int] = None,
        section: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not self.collection:
            self._init_db()
            if not self.collection:
                return []

        # Construct ChromaDB metadata filter
        filter_conditions = []
        if company_id:
            filter_conditions.append({"company_id": str(company_id)})
        if fiscal_year:
            filter_conditions.append({"fiscal_year": int(fiscal_year)})
        if section:
            filter_conditions.append({"section": str(section)})

        where_clause = None
        if len(filter_conditions) == 1:
            where_clause = filter_conditions[0]
        elif len(filter_conditions) > 1:
            where_clause = {"$and": filter_conditions}

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"],
        )

        output: List[Dict[str, Any]] = []
        if not results or not results["documents"] or not results["documents"][0]:
            return output

        doc_list = results["documents"][0]
        meta_list = results["metadatas"][0] if results.get("metadatas") else [{}] * len(doc_list)
        dist_list = results["distances"][0] if results.get("distances") else [0.0] * len(doc_list)
        id_list = results["ids"][0] if results.get("ids") else [f"chunk_{i}" for i in range(len(doc_list))]

        for cid, doc, meta, dist in zip(id_list, doc_list, meta_list, dist_list):
            output.append({
                "chunk_id": cid,
                "text": doc,
                "metadata": meta,
                "distance": dist,
                "relevance_score": max(0.0, 1.0 - (dist if dist is not None else 0.5)),
            })

        return output

    def count(self) -> int:
        if not self.collection:
            self._init_db()
            if not self.collection:
                return 0
        return self.collection.count()
