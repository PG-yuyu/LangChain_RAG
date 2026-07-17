"""BackendService 协议实现 —— 成员 1 的统一入口。

成员 1 只依赖此接口，不导入 rag/ 或 graphdb/ 的内部模块。
"""

import logging
import os

from contracts.backend_service import BackendService
from contracts.errors import (
    DOCUMENT_PARSE_FAILED,
    INVALID_REQUEST,
    ServiceError,
)
from contracts.graph_repository import GraphRepository
from contracts.models import (
    DocumentSummary,
    QueryRequest,
    QueryResponse,
)
from rag.rag_pipeline import RAGPipeline
from rag.session_store import SessionStore

logger = logging.getLogger("rag.backend_service")


class DefaultBackendService(BackendService):
    """成员 1 统一调用的后端服务实现。"""

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        session_store: SessionStore,
        graph_repository: GraphRepository,
    ):
        self.pipeline = rag_pipeline
        self.session_store = session_store
        self.graph = graph_repository

    # ── 文档管理 ─────────────────────────────────────────────

    def ingest_document(
        self,
        file_path: str,
        knowledge_base_id: str,
    ) -> DocumentSummary:
        """上传文档：解析 → 抽取 → 写入 GraphDB。"""
        if not file_path:
            raise ServiceError(
                code=INVALID_REQUEST,
                message="file_path 不能为空",
            )
        if not os.path.isfile(file_path):
            raise ServiceError(
                code=DOCUMENT_PARSE_FAILED,
                message=f"文件不存在: {file_path}",
            )

        logger.info("Ingesting document: %s (kb=%s)", file_path, knowledge_base_id)

        try:
            result = self.pipeline.process_document(
                file_path=file_path,
                knowledge_base_id=knowledge_base_id,
            )
            logger.info("Document ingested: %s → %s", file_path, result.document_id)
            return result
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(
                code=DOCUMENT_PARSE_FAILED,
                message=f"文档上传失败: {e}",
                details={"file_path": file_path},
            ) from e

    def answer(self, request: QueryRequest) -> QueryResponse:
        """问答：完整的意图识别 → 检索 → 答案生成流程。"""
        if not request.query or not request.query.strip():
            raise ServiceError(
                code=INVALID_REQUEST,
                message="查询内容不能为空",
            )
        if not request.knowledge_base_id:
            raise ServiceError(
                code=INVALID_REQUEST,
                message="knowledge_base_id 不能为空",
            )

        logger.info(
            "Answer request: query='%.60s...', session=%s, kb=%s",
            request.query, request.session_id, request.knowledge_base_id,
        )

        try:
            return self.pipeline.answer_query(request)
        except ServiceError:
            raise
        except Exception as e:
            logger.exception("Unexpected error in answer()")
            raise ServiceError(
                code="INTERNAL_ERROR",
                message=f"系统内部错误: {e}",
                retryable=False,
            ) from e

    def list_documents(
        self,
        knowledge_base_id: str,
    ) -> list[DocumentSummary]:
        """列出知识库中所有文档。"""
        logger.info("Listing documents for kb=%s", knowledge_base_id)
        try:
            return self.graph.list_documents(knowledge_base_id)
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(
                code="GRAPH_QUERY_FAILED",
                message=f"获取文档列表失败: {e}",
                retryable=True,
            ) from e

    def delete_document(
        self,
        knowledge_base_id: str,
        document_id: str,
    ) -> bool:
        """删除文档及其关联数据。"""
        logger.info("Deleting document: %s (kb=%s)", document_id, knowledge_base_id)
        try:
            return self.graph.delete_document(knowledge_base_id, document_id)
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(
                code="GRAPH_WRITE_FAILED",
                message=f"删除文档失败: {e}",
                retryable=True,
            ) from e

    def clear_session(self, session_id: str) -> bool:
        """清除会话历史。"""
        logger.info("Clearing session: %s", session_id)
        return self.session_store.clear_session(session_id)

    def health_check(self) -> dict:
        """系统健康检查：LLM + GraphDB 连接状态。"""
        check_result = {
            "status": "ok",
            "service": "DefaultBackendService",
            "version": "0.1.0",
        }

        # GraphDB 检查
        try:
            graph_ok = self.graph.health_check()
            check_result["graphdb"] = "ok" if graph_ok else "unavailable"
        except Exception as e:
            check_result["graphdb"] = f"error: {e}"
            check_result["status"] = "degraded"

        return check_result
