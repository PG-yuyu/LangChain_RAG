from __future__ import annotations

import uuid
from pathlib import Path

from contracts.models import (
    DocumentSummary,
    GraphEdge,
    GraphNode,
    IntentType,
    QueryRequest,
    QueryResponse,
    SourceReference,
    now_text,
)


class MockBackendService:
    def __init__(self) -> None:
        self.documents: dict[str, list[DocumentSummary]] = {"kb_demo": []}

    def health_check(self) -> dict:
        return {
            "status": "mock-ready",
            "message": "FastAPI Mock Backend 已启动，可用于前端联调。",
        }

    def ingest_document(self, file_path: str, knowledge_base_id: str) -> DocumentSummary:
        filename = Path(file_path).name
        document_id = "doc_" + Path(filename).stem.lower().replace(" ", "_")
        document = DocumentSummary(
            document_id=document_id,
            filename=filename,
            knowledge_base_id=knowledge_base_id,
            chunk_count=6,
            entity_count=4,
            created_at=now_text(),
        )
        current = self.documents.setdefault(knowledge_base_id, [])
        self.documents[knowledge_base_id] = [
            item for item in current if item.document_id != document_id
        ] + [document]
        return document

    def list_documents(self, knowledge_base_id: str) -> list[DocumentSummary]:
        return list(self.documents.get(knowledge_base_id, []))

    def delete_document(self, knowledge_base_id: str, document_id: str) -> bool:
        current = self.documents.get(knowledge_base_id, [])
        remaining = [item for item in current if item.document_id != document_id]
        self.documents[knowledge_base_id] = remaining
        return len(remaining) != len(current)

    def clear_session(self, session_id: str) -> bool:
        return bool(session_id)

    def answer(self, request: QueryRequest) -> QueryResponse:
        selected = request.selected_document_ids or ["整个知识库"]
        answer = (
            "这是 Mock RAG 返回的示例回答。真实联调时，这里会接入 LangChain、GraphDB "
            "和大模型生成的答案。\n\n"
            f"问题：{request.query}\n"
            f"检索范围：{', '.join(selected)}"
        )
        return QueryResponse(
            answer=answer,
            intent=IntentType.GRAPH_QUERY,
            original_query=request.query,
            rewritten_query=request.query
            if not request.enable_query_rewrite
            else f"{request.query}（改写示例）",
            sources=[
                SourceReference(
                    document_id="doc_ai_intro",
                    filename="ai_intro.pdf",
                    chunk_id="chunk_001",
                    page_number=1,
                    content="机器学习是人工智能的一个重要分支，常用于从数据中学习规律。",
                    score=0.92,
                )
            ],
            graph_nodes=[
                GraphNode(node_id="entity_ai", label="人工智能", node_type="Concept"),
                GraphNode(node_id="entity_ml", label="机器学习", node_type="Concept"),
            ],
            graph_edges=[
                GraphEdge(
                    edge_id="edge_001",
                    source="entity_ml",
                    target="entity_ai",
                    relation="SUBFIELD_OF",
                    source_chunk_id="chunk_001",
                )
            ],
            graph_paths=[["机器学习", "SUBFIELD_OF", "人工智能"]],
            session_id=request.session_id,
            trace_id=request.trace_id or f"trace_{uuid.uuid4().hex[:12]}",
        )

