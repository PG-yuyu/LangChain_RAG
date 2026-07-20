"""Chroma client wrapper with parent and child collections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from neo4j_chroma.config import GraphDBConfig
from neo4j_chroma.embedding import HashEmbeddingFunction, create_embedding_function


ClientFactory = Callable[[str], Any]


@dataclass(slots=True)
class ChromaClient:
    """Lazy Chroma client that owns the parent and child collections."""

    persist_directory: str
    parent_collection_name: str = "parent_documents"
    child_collection_name: str = "child_documents"
    embedding_function: HashEmbeddingFunction | None = None
    client: Any | None = None
    client_factory: ClientFactory | None = None

    @classmethod
    def from_config(cls, config: GraphDBConfig) -> "ChromaClient":
        return cls(
            persist_directory=config.chroma_persist_directory,
            parent_collection_name=config.chroma_parent_collection,
            child_collection_name=config.chroma_child_collection,
            embedding_function=create_embedding_function(
                config.embedding_provider,
                config.embedding_dimension,
            ),
        )

    @classmethod
    def from_env(cls) -> "ChromaClient":
        return cls.from_config(GraphDBConfig.from_env())

    def connect(self) -> Any:
        if self.client is None:
            if self.client_factory is None:
                try:
                    import chromadb
                except ImportError as exc:
                    raise RuntimeError(
                        "chromadb package is required for a real Chroma connection",
                    ) from exc
                self.client_factory = chromadb.PersistentClient
            self.client = self.client_factory(path=self.persist_directory)
        return self.client

    def get_collection(self, name: str) -> Any:
        return self.connect().get_or_create_collection(name=name)

    @property
    def parent_collection(self) -> Any:
        return self.get_collection(self.parent_collection_name)

    @property
    def child_collection(self) -> Any:
        return self.get_collection(self.child_collection_name)

    def health_check(self) -> bool:
        try:
            self.parent_collection.count()
            self.child_collection.count()
            return True
        except Exception:
            return False

    def close(self) -> None:
        self.client = None
