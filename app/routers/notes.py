# -*- coding: utf-8 -*-
"""四象限记事本:记录待办 + AI 建议象限。"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import models
from app.services.llm import DeepSeekChannel, LLMError

router = APIRouter()

SUGGEST_PROMPT = """你是时间管理助手。根据"重要程度 × 紧急程度"判断用户事项应放入哪个象限,按 JSON 输出,只输出 JSON:

{{"象限": 1|2|3|4, "说明": "一句话理由(为什么放这个象限)"}}

象限定义:
1 = 重要且紧急(立即做)
2 = 重要不紧急(计划做,别拖成紧急)
3 = 紧急不重要(快速处理或委托)
4 = 不重要不紧急(暂缓或放弃)

用户事项:「{text}」"""

QUADRANT_NAMES = {
    1: "Ⅰ 重要且紧急 · 立即做",
    2: "Ⅱ 重要不紧急 · 计划做",
    3: "Ⅲ 紧急不重要 · 快速处理",
    4: "Ⅳ 不重要不紧急 · 暂缓",
}


class NoteCreate(BaseModel):
    content: str
    quadrant: int = 1


class SuggestRequest(BaseModel):
    content: str


@router.get("/api/notes")
def list_notes() -> dict:
    return {"items": [dict(r) for r in models.list_notes()]}


@router.post("/api/notes")
def create_note(req: NoteCreate) -> dict:
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="内容为空")
    if req.quadrant not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="象限必须为 1-4")
    note_id = models.insert_note(req.content.strip(), req.quadrant)
    return {"id": note_id, "ok": True}


@router.post("/api/notes/suggest")
def suggest_quadrant(req: SuggestRequest) -> dict:
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="内容为空")
    try:
        data = DeepSeekChannel().chat_json(SUGGEST_PROMPT.format(text=req.content.strip()))
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    q = data.get("象限")
    if q not in (1, 2, 3, 4):
        raise HTTPException(status_code=502, detail="AI 返回了无效象限")
    return {"象限": q, "说明": data.get("说明", ""), "象限名": QUADRANT_NAMES[q]}


@router.post("/api/notes/{note_id}/toggle")
def toggle_note(note_id: int) -> dict:
    models.toggle_note(note_id)
    return {"ok": True}


@router.delete("/api/notes/{note_id}")
def remove_note(note_id: int) -> dict:
    models.delete_note(note_id)
    return {"ok": True}
