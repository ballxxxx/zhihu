# -*- coding: utf-8 -*-
"""上传接口:文件 → 解析 → 切块 → 落库。"""
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app import config, models
from app.services.chunker import chunk_text
from app.services.parser import ParseError, parse_file

router = APIRouter()

ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}
MAX_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {suffix}")
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="文件超过 20MB 限制")

    upload_dir = config.DATA_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)
    saved_path = upload_dir / f"{uuid.uuid4().hex}{suffix}"
    saved_path.write_bytes(content)

    try:
        text = parse_file(saved_path)
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not text.strip():
        raise HTTPException(status_code=400, detail="未解析到任何文本内容")

    chunks = chunk_text(text)
    doc_id = models.insert_document(filename=file.filename or saved_path.name, raw_text=text, chunk_count=len(chunks))
    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "chars": len(text),
        "chunks": len(chunks),
        "preview": text[:100],
    }


@router.get("/api/documents")
def documents(limit: int = 20) -> dict:
    rows = models.list_documents(limit)
    return {"items": [dict(r) for r in rows]}
