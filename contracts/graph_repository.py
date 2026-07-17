"""成员 2 与成员 3 之间的图数据库接口（Protocol）。

成员 3 只依赖此接口调用 GraphDB，不编写 SPARQL 语句。
SPARQL 完全封装在成员 2 的模块内部。
"""

from typing import Protocol

from contracts.models import (
    DocumentGraphPayload,
    DocumentSummary,
    RetrievalResult,
)


class GraphRepository(Protocol):
    """成员 2 提供的图数据库抽象接口。"""

    def health_check(self) -> bool:
        """检查 GraphDB 是否可访问。"""
        ...

    def upsert_document_graph(
        self,
        payload: DocumentGraphPayload,
    ) -> DocumentSummary:
        """保存文档、分块、实体和关系到 GraphDB（幂等）。"""
        ...

    def retrieve_context(
        self,
        query: str,
        entity_names: list[str],
        knowledge_base_id: str,
        document_ids: list[str],
        top_k: int = 5,
        max_hops: int = 2,
    ) -> RetrievalResult:
        """根据实体名称和查询文本检索相关文档块、实体关系和路径。"""
        ...

    def list_documents(
        self,
        knowledge_base_id: str,
    ) -> list[DocumentSummary]:
        """查询知识库中的文档。"""
        ...

    def delete_document(
        self,
        knowledge_base_id: str,
        document_id: str,
    ) -> bool:
        """删除文档及其相关三元组。"""
        ...

    def get_subgraph(
        self,
        knowledge_base_id: str,
        entity_ids: list[str],
        max_hops: int = 2,
    ) -> RetrievalResult:
        """获取指定实体的子图（实体、关系、路径和文档块）。"""
        ...
