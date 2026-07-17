"""成员 1 与成员 3 之间的统一服务接口（Protocol）。

成员 1 只依赖此接口，不导入 rag/ 或 graphdb/ 的内部模块。
"""

from typing import Protocol

from contracts.models import (
    DocumentSummary,
    QueryRequest,
    QueryResponse,
)


class BackendService(Protocol):
    """成员 1 统一调用的后端服务接口。"""

    def ingest_document(
        self,
        file_path: str,
        knowledge_base_id: str,
    ) -> DocumentSummary:
        """解析文档、切块、抽取实体关系并存入 GraphDB。"""
        ...

    def answer(
        self,
        request: QueryRequest,
    ) -> QueryResponse:
        """完成意图识别、检索和答案生成。"""
        ...

    def list_documents(
        self,
        knowledge_base_id: str,
    ) -> list[DocumentSummary]:
        """查询知识库中的文档列表。"""
        ...

    def delete_document(
        self,
        knowledge_base_id: str,
        document_id: str,
    ) -> bool:
        """删除文档及其关联数据。"""
        ...

    def clear_session(
        self,
        session_id: str,
    ) -> bool:
        """清除指定会话的历史记录。"""
        ...

    def health_check(self) -> dict:
        """系统健康检查。"""
        ...
