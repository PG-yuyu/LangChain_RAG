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
  backend_service_impl.py  当前 Mock RAG 服务，后续替换真实 LangChain RAG

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

现在后端使用 Mock 数据，后续接真实 LangChain、GraphDB 和大模型时保持这些接口不变即可。
