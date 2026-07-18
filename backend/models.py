from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    NORMAL_CHAT = "normal_chat"
    DOCUMENT_SEARCH = "document_search"
    GRAPH_QUERY = "graph_query"
    UNKNOWN = "unknown"


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    knowledge_base_id: str
    chunk_count: int
    entity_count: int
    created_at: str


class QueryRequest(BaseModel):
    query: str
    session_id: str
    knowledge_base_id: str = "kb_demo"
    selected_document_ids: list[str] = Field(default_factory=list)
    top_k: int = 5
    max_hops: int = 2
    enable_query_rewrite: bool = True
    trace_id: str | None = None


class SourceReference(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    page_number: int | None = None
    content: str
    score: float


class GraphNode(BaseModel):
    node_id: str
    label: str
    node_type: str


class GraphEdge(BaseModel):
    edge_id: str
    source: str
    target: str
    relation: str
    source_chunk_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    intent: IntentType
    original_query: str
    rewritten_query: str
    sources: list[SourceReference] = Field(default_factory=list)
    graph_nodes: list[GraphNode] = Field(default_factory=list)
    graph_edges: list[GraphEdge] = Field(default_factory=list)
    graph_paths: list[list[str]] = Field(default_factory=list)
    session_id: str
    trace_id: str


class HealthResponse(BaseModel):
    status: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")

