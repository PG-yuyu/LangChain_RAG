"""共享数据模型 —— 使用标准库 dataclass，三个成员共享。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    """用户查询意图类型。"""
    NORMAL_CHAT = "normal_chat"
    DOCUMENT_SEARCH = "document_search"
    GRAPH_QUERY = "graph_query"
    UNKNOWN = "unknown"


# ── 文档与知识图谱数据 ──────────────────────────────────────────


@dataclass
class DocumentSummary:
    """文档摘要信息。"""
    document_id: str
    filename: str
    knowledge_base_id: str
    chunk_count: int
    entity_count: int
    created_at: str


@dataclass
class ChunkRecord:
    """文档分块记录。"""
    chunk_id: str
    document_id: str
    content: str
    page_number: int | None = None
    title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityRecord:
    """实体记录。"""
    entity_id: str
    name: str
    entity_type: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class RelationRecord:
    """关系记录。"""
    relation_id: str
    source_entity_id: str
    relation_type: str
    target_entity_id: str
    source_chunk_id: str
    confidence: float = 1.0


@dataclass
class DocumentGraphPayload:
    """成员 3 向成员 2 传递数据的核心格式。"""
    schema_version: str
    knowledge_base_id: str
    document: DocumentSummary
    chunks: list[ChunkRecord]
    entities: list[EntityRecord]
    relations: list[RelationRecord]


# ── 查询请求与响应 ──────────────────────────────────────────────


@dataclass
class QueryRequest:
    """用户查询请求。"""
    query: str
    session_id: str
    knowledge_base_id: str
    selected_document_ids: list[str] = field(default_factory=list)
    top_k: int = 5
    max_hops: int = 2
    enable_query_rewrite: bool = True
    trace_id: str | None = None


# ── GraphDB 检索结果 ──────────────────────────────────────────


@dataclass
class RetrievedChunk:
    """从 GraphDB 检索到的文档块。"""
    chunk_id: str
    document_id: str
    filename: str
    content: str
    page_number: int | None
    score: float


@dataclass
class GraphNode:
    """知识图谱节点（用于前端展示）。"""
    node_id: str
    label: str
    node_type: str


@dataclass
class GraphEdge:
    """知识图谱边（用于前端展示）。"""
    edge_id: str
    source: str
    target: str
    relation: str
    source_chunk_id: str | None = None


@dataclass
class RetrievalResult:
    """成员 2 GraphDB 检索返回的结构化结果。"""
    rewritten_query: str
    matched_entities: list[EntityRecord] = field(default_factory=list)
    chunks: list[RetrievedChunk] = field(default_factory=list)
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    paths: list[list[str]] = field(default_factory=list)


# ── 最终问答结果 ──────────────────────────────────────────────


@dataclass
class SourceReference:
    """回答的引用来源。"""
    document_id: str
    filename: str
    chunk_id: str
    page_number: int | None
    content: str
    score: float


@dataclass
class QueryResponse:
    """成员 3 向成员 1 返回的最终问答结果。"""
    answer: str
    intent: IntentType
    original_query: str
    rewritten_query: str
    sources: list[SourceReference] = field(default_factory=list)
    graph_nodes: list[GraphNode] = field(default_factory=list)
    graph_edges: list[GraphEdge] = field(default_factory=list)
    graph_paths: list[list[str]] = field(default_factory=list)
    session_id: str = ""
    trace_id: str = ""
