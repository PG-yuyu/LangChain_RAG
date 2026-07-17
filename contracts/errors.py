"""统一错误接口 —— 避免把底层异常直接显示给用户。"""


class ServiceError(Exception):
    """统一业务异常，所有模块只抛出或包装为此类型。"""

    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = False,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details,
        }


# ── 预定义错误码常量 ──────────────────────────────────────────

# 文档处理
INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
DOCUMENT_PARSE_FAILED = "DOCUMENT_PARSE_FAILED"
DOCUMENT_TOO_LARGE = "DOCUMENT_TOO_LARGE"

# 实体抽取
ENTITY_EXTRACTION_FAILED = "ENTITY_EXTRACTION_FAILED"

# GraphDB
GRAPHDB_UNAVAILABLE = "GRAPHDB_UNAVAILABLE"
GRAPH_WRITE_FAILED = "GRAPH_WRITE_FAILED"
GRAPH_QUERY_FAILED = "GRAPH_QUERY_FAILED"

# 模型调用
MODEL_CALL_FAILED = "MODEL_CALL_FAILED"

# 检索
EMPTY_RETRIEVAL_RESULT = "EMPTY_RETRIEVAL_RESULT"

# 请求
INVALID_REQUEST = "INVALID_REQUEST"
