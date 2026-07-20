"""Retrieval loop that combines Chroma recall and Neo4j source metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from neo4j_chroma.database_repository import ChildChunkNode, DatabaseRepository, ParentChunkNode
from neo4j_chroma.vector_store import VectorDocument, VectorSearchResult, VectorStore


@dataclass(slots=True)
class SourceInfo:
    document_id: str
    filename: str
    parent_id: str
    child_id: str
    chunk_index: int | None
    page_number: int | None
    content: str
    child_content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetrievalOutput:
    query: str
    context: str
    retrieved_docs: list[SourceInfo] = field(default_factory=list)
    sources: list[SourceInfo] = field(default_factory=list)
    graph_results: list[dict[str, Any]] = field(default_factory=list)


class HybridRetriever:
    """Implements child recall, parent backtracking, and source assembly."""

    def __init__(
        self,
        vector_store: VectorStore,
        database_repository: DatabaseRepository | None = None,
    ):
        self.vector_store = vector_store
        self.database_repository = database_repository

    @classmethod
    def from_env(cls) -> "HybridRetriever":
        return cls(
            vector_store=VectorStore.from_env(),
            database_repository=DatabaseRepository.from_env(),
        )

    def health_check(self) -> bool:
        vector_ok = self.vector_store.health_check()
        neo4j_ok = True
        if self.database_repository is not None:
            neo4j_ok = self.database_repository.health_check()
        return vector_ok and neo4j_ok

    def close(self) -> None:
        self.vector_store.close()
        if self.database_repository is not None:
            self.database_repository.close()

    def retrieve(
        self,
        query: str,
        document_ids: Sequence[str] | None = None,
        top_k: int = 5,
        entity_names: Sequence[str] | None = None,
        max_hops: int = 2,
    ) -> RetrievalOutput:
        child_results = self.vector_store.query_child_chunks(
            query,
            top_k=top_k,
            document_ids=document_ids,
        )
        parent_ids = _unique(
            result.metadata.get("parent_id")
            for result in child_results
            if result.metadata.get("parent_id")
        )
        child_ids = _unique(
            result.metadata.get("child_id")
            for result in child_results
            if result.metadata.get("child_id")
        )

        parent_documents = self.vector_store.get_parent_documents_by_ids(parent_ids)
        parent_vectors = {
            str(doc.metadata.get("parent_id")): doc
            for doc in parent_documents
            if doc.metadata.get("parent_id")
        }
        neo4j_parents, neo4j_children = self._load_neo4j_sources(parent_ids, child_ids)

        sources = [
            self._build_source(
                child_result,
                parent_vectors,
                neo4j_parents,
                neo4j_children,
            )
            for child_result in child_results
        ]
        context = self._build_context(sources)
        graph_results = self._retrieve_graph_results(entity_names or [], document_ids, max_hops)
        return RetrievalOutput(
            query=query,
            context=context,
            retrieved_docs=sources,
            sources=sources,
            graph_results=graph_results,
        )

    def _load_neo4j_sources(
        self,
        parent_ids: Sequence[str],
        child_ids: Sequence[str],
    ) -> tuple[dict[str, ParentChunkNode], dict[str, ChildChunkNode]]:
        if self.database_repository is None:
            return {}, {}
        parents = self.database_repository.get_parent_chunks_by_ids(parent_ids)
        children = self.database_repository.get_child_chunks_by_ids(child_ids)
        return (
            {parent.parent_id: parent for parent in parents},
            {child.child_id: child for child in children},
        )

    def _retrieve_graph_results(
        self,
        entity_names: Sequence[str],
        document_ids: Sequence[str] | None,
        max_hops: int,
    ) -> list[dict[str, Any]]:
        if not entity_names or self.database_repository is None:
            return []
        method = getattr(self.database_repository, "retrieve_entity_context", None)
        if method is None:
            return []
        return method(entity_names=list(entity_names), document_ids=list(document_ids or []), max_hops=max_hops)

    @staticmethod
    def _build_source(
        child_result: VectorSearchResult,
        parent_vectors: dict[str, VectorDocument],
        neo4j_parents: dict[str, ParentChunkNode],
        neo4j_children: dict[str, ChildChunkNode],
    ) -> SourceInfo:
        child_meta = dict(child_result.metadata)
        child_id = str(child_meta.get("child_id", ""))
        parent_id = str(child_meta.get("parent_id", ""))
        neo4j_child = neo4j_children.get(child_id)
        neo4j_parent = neo4j_parents.get(parent_id)
        parent_vector = parent_vectors.get(parent_id)

        merged_metadata = {}
        if parent_vector:
            merged_metadata.update(parent_vector.metadata)
        if neo4j_parent:
            merged_metadata.update(neo4j_parent.metadata)
        if neo4j_child:
            merged_metadata.update(neo4j_child.metadata)
        merged_metadata.update(child_meta)

        content = (
            parent_vector.content
            if parent_vector and parent_vector.content
            else neo4j_parent.content
            if neo4j_parent
            else child_result.content
        )
        child_content = neo4j_child.content if neo4j_child else child_result.content
        return SourceInfo(
            document_id=str(merged_metadata.get("document_id", "")),
            filename=str(merged_metadata.get("filename", "")),
            parent_id=parent_id,
            child_id=child_id,
            chunk_index=_optional_int(merged_metadata.get("chunk_index")),
            page_number=_optional_int(merged_metadata.get("page_number")),
            content=content,
            child_content=child_content,
            score=child_result.score,
            metadata=merged_metadata,
        )

    @staticmethod
    def _build_context(sources: Sequence[SourceInfo]) -> str:
        seen = set()
        context_parts = []
        for source in sources:
            key = source.parent_id or source.child_id or source.content
            if key in seen:
                continue
            seen.add(key)
            context_parts.append(source.content)
        return "\n\n".join(context_parts)


def _unique(values: Sequence[Any]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
