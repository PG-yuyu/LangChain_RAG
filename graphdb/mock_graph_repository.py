from __future__ import annotations

from contracts.models import (
    DocumentGraphPayload,
    DocumentSummary,
    RetrievalResult,
)


class MockGraphRepository:
    def __init__(self) -> None:
        self.documents: dict[str, list[DocumentSummary]] = {"kb_demo": []}

    def health_check(self) -> bool:
        return True

    def upsert_document_graph(self, payload: DocumentGraphPayload) -> DocumentSummary:
        current = self.documents.setdefault(payload.knowledge_base_id, [])
        self.documents[payload.knowledge_base_id] = [
            item for item in current if item.document_id != payload.document.document_id
        ] + [payload.document]
        return payload.document

    def retrieve_context(
        self,
        query: str,
        entity_names: list[str],
        knowledge_base_id: str,
        document_ids: list[str],
        top_k: int = 5,
        max_hops: int = 2,
    ) -> RetrievalResult:
        return RetrievalResult(
            rewritten_query=query,
            matched_entities=[],
            chunks=[],
            nodes=[],
            edges=[],
            paths=[],
        )

    def list_documents(self, knowledge_base_id: str) -> list[DocumentSummary]:
        return list(self.documents.get(knowledge_base_id, []))

    def delete_document(self, knowledge_base_id: str, document_id: str) -> bool:
        current = self.documents.get(knowledge_base_id, [])
        remaining = [item for item in current if item.document_id != document_id]
        self.documents[knowledge_base_id] = remaining
        return len(remaining) != len(current)

    def get_subgraph(
        self,
        knowledge_base_id: str,
        entity_ids: list[str],
        max_hops: int = 2,
    ) -> RetrievalResult:
        return RetrievalResult(
            rewritten_query="",
            matched_entities=[],
            chunks=[],
            nodes=[],
            edges=[],
            paths=[],
        )

