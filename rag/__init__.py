"""rag 模块 —— 成员 3：文档处理、RAG 与 Agent。

提供：
- create_backend_service(): 工厂函数，创建完整装配的 BackendService
- 各子模块可单独导入用于测试
"""

import logging

from contracts.graph_repository import GraphRepository
from rag.config import Settings, get_settings
from rag.document_loader import DocumentLoader
from rag.document_processor import DocumentProcessor
from rag.entity_extractor import EntityExtractor
from rag.intent_router import IntentRouter
from rag.llm_client import LLMClient
from rag.query_rewriter import QueryRewriter
from rag.rag_pipeline import RAGPipeline
from rag.reranker import Reranker
from rag.retriever import Retriever
from rag.backend_service_impl import DefaultBackendService
from rag.session_store import SessionStore

__version__ = "0.1.0"


def create_backend_service(
    graph_repository: GraphRepository | None = None,
    settings: Settings | None = None,
) -> DefaultBackendService:
    """创建完整装配的 BackendService 实例。

    如果没有提供 graph_repository，使用 MockGraphRepository。
    如果没有提供 settings，从环境变量读取。

    Usage:
        from rag import create_backend_service
        backend = create_backend_service()
    """
    settings = settings or get_settings()

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # LLM
    llm_client = LLMClient(settings)

    # 文档处理
    document_processor = DocumentProcessor(settings)

    # 存储
    session_store = SessionStore()

    # 智能模块
    entity_extractor = EntityExtractor(llm_client)
    query_rewriter = QueryRewriter(llm_client, session_store, enabled=True)
    intent_router = IntentRouter(llm_client)
    reranker = Reranker(settings)

    # 如果没有提供 GraphRepository，使用 Mock
    if graph_repository is None:
        from tests.mocks.mock_graph_repository import MockGraphRepository
        graph_repository = MockGraphRepository()
        logging.getLogger("rag").warning("No GraphRepository provided, using MockGraphRepository")

    retriever = Retriever(graph_repository)

    # 主流程
    pipeline = RAGPipeline(
        document_processor=document_processor,
        entity_extractor=entity_extractor,
        intent_router=intent_router,
        query_rewriter=query_rewriter,
        retriever=retriever,
        reranker=reranker,
        llm_client=llm_client,
        session_store=session_store,
        graph_repository=graph_repository,
    )

    # 统一服务
    backend = DefaultBackendService(
        rag_pipeline=pipeline,
        session_store=session_store,
        graph_repository=graph_repository,
    )

    logging.getLogger("rag").info("BackendService created (version=%s)", __version__)
    return backend
