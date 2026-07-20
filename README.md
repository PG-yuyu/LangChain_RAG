# GraphRAG 文档问答项目

这是重新搭建的 Vue + FastAPI 版本。

## 结构

```text
contracts/
  models.py             共享接口数据结构
  backend_service.py    前端调用的统一业务接口
  graph_repository.py   RAG 调用的 GraphDB 抽象接口
  errors.py             统一错误结构和错误码

backend/
  main.py               FastAPI 接口入口

rag/
  backend_service_impl.py  RAG 业务服务入口，当前接真实 RAG 流程

graphdb/
  mock_graph_repository.py Mock GraphDB 仓库，后续替换真实 GraphDB

frontend/
  src/App.vue           Vue 页面
  src/api.js            前端接口调用
  src/styles.css        页面样式
```

## 后端运行

```powershell
$env:UV_CACHE_DIR="$PWD\.uv-cache"
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

## 前端运行

```powershell
cd frontend
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:5173
```

## 当前接口

- `GET /api/health`
- `GET /api/documents?knowledge_base_id=kb_demo`
- `POST /api/documents/upload`
- `DELETE /api/documents/{document_id}`
- `POST /api/answer`

现在后端已经接入文档解析、切块、意图识别、问题改写、实体抽取、检索重排和 DeepSeek 问答生成。
当前还没有接真实 GraphDB，图数据库层暂时使用 `graphdb/mock_graph_repository.py` 的内存 Mock 仓库，后续替换真实 GraphDB 时保持接口不变即可。
