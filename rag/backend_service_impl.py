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
from graphdb.mock_graph_repository import MockGraphRepository
from rag.document_processor import DocumentProcessor
from rag.entity_extractor import EntityExtractor
from rag.intent_router import IntentRouter
from rag.llm_client import LLMClient
from rag.query_rewriter import QueryRewriter
from rag.rag_pipeline import RAGPipeline
from rag.reranker import Reranker
from rag.retriever import Retriever
from rag.session_store import SessionStore


class RAGBackendService:
    def __init__(self, pipeline: RAGPipeline, graph_repository: MockGraphRepository) -> None:
        self.pipeline = pipeline
        self.graph_repository = graph_repository

    def health_check(self) -> dict:
        graph_status = "ready" if self.graph_repository.health_check() else "unavailable"
        return {
            "status": "ready",
            "message": "RAG Backend 已启动，当前使用 Mock GraphDB 存储。",
            "details": {
                "llm": "deepseek-chat",
                "graphdb": graph_status,
                "storage": "mock-memory",
            },
        }

    def ingest_document(self, file_path: str, knowledge_base_id: str) -> DocumentSummary:
        return self.pipeline.process_document(file_path, knowledge_base_id)

    def answer(self, request: QueryRequest) -> QueryResponse:
        return self.pipeline.answer_query(request)

    def answer_stream(self, request: QueryRequest):
        return self.pipeline.answer_query_stream(request)

    def list_documents(self, knowledge_base_id: str) -> list[DocumentSummary]:
        return self.graph_repository.list_documents(knowledge_base_id)

    def delete_document(self, knowledge_base_id: str, document_id: str) -> bool:
        return self.graph_repository.delete_document(knowledge_base_id, document_id)

    def clear_session(self, session_id: str) -> bool:
        return self.pipeline.session_store.clear_session(session_id)


def create_backend_service() -> RAGBackendService:
    llm_client = LLMClient()
    session_store = SessionStore()
    graph_repository = MockGraphRepository()
    retriever = Retriever(graph_repository)

    pipeline = RAGPipeline(
        document_processor=DocumentProcessor(),
        entity_extractor=EntityExtractor(llm_client),
        intent_router=IntentRouter(llm_client),
        query_rewriter=QueryRewriter(llm_client, session_store),
        retriever=retriever,
        reranker=Reranker(),
        llm_client=llm_client,
        session_store=session_store,
        graph_repository=graph_repository,
    )
    return RAGBackendService(pipeline, graph_repository)


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
