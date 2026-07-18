from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.models import DocumentSummary, HealthResponse, QueryRequest, QueryResponse
from backend.services import MockRAGService

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="GraphRAG API", version="0.1.0")
service = MockRAGService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="mock-ready",
        message="FastAPI Mock Backend 已启动，可用于前端联调。",
    )


@app.get("/api/documents", response_model=list[DocumentSummary])
def list_documents(knowledge_base_id: str = "kb_demo") -> list[DocumentSummary]:
    return service.list_documents(knowledge_base_id)


@app.post("/api/documents/upload", response_model=DocumentSummary)
async def upload_document(
    file: UploadFile = File(...),
    knowledge_base_id: str = Form("kb_demo"),
) -> DocumentSummary:
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    safe_name = Path(file.filename).name
    target = UPLOAD_DIR / safe_name
    with target.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return service.ingest_document(str(target), knowledge_base_id)


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str, knowledge_base_id: str = "kb_demo") -> dict:
    deleted = service.delete_document(knowledge_base_id, document_id)
    return {"deleted": deleted}


@app.post("/api/answer", response_model=QueryResponse)
def answer(request: QueryRequest) -> QueryResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    return service.answer(request)

