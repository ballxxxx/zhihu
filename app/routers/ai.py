# -*- coding: utf-8 -*-
"""P0 伴随式 AI:问AI(带知识点上下文)+ 待办识别 + 反馈。"""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import models
from app.services.llm import DeepSeekChannel, LLMError

router = APIRouter()

ASK_PROMPT = """你是《{course}》的辅导老师。学生正在复习下面这个知识点:

知识点:{point}
出题方向:{direction}
AI 依据:{basis}
知乎经验:{experiences}

学生的问题是:「{question}」

请基于以上上下文回答,用通俗的语言,300字以内。如果学生的问题与这个知识点无关,可以简答并引导回知识点。"""


class AskRequest(BaseModel):
    task_id: int
    point_index: int
    question: str


class FeedbackRequest(BaseModel):
    task_id: int
    point_index: int
    vote: str  # useful / wrong


class TodoRequest(BaseModel):
    text: str


@router.post("/api/ask")
def ask(req: AskRequest) -> dict:
    row = models.get_task(req.task_id)
    if row is None or not row["result_json"]:
        raise HTTPException(status_code=404, detail="任务不存在或未完成")
    result = json.loads(row["result_json"])
    points = result.get("points", [])
    if req.point_index >= len(points):
        raise HTTPException(status_code=404, detail="知识点序号无效")
    p = points[req.point_index]
    exps = result.get("experiences", {}).get(str(req.point_index), [])
    exp_text = ";".join(e.get("经验", "") for e in exps) or "无"

    prompt = ASK_PROMPT.format(
        course=result.get("course", ""),
        point=p.get("知识点", ""),
        direction=p.get("出题方向", ""),
        basis=p.get("依据", ""),
        experiences=exp_text,
        question=req.question,
    )
    try:
        answer = DeepSeekChannel().chat(prompt, temperature=0.5)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"answer": answer}


@router.post("/api/feedback")
def feedback(req: FeedbackRequest) -> dict:
    if req.vote not in ("useful", "wrong"):
        raise HTTPException(status_code=400, detail="vote 必须为 useful 或 wrong")
    if models.get_task(req.task_id) is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    models.insert_feedback(req.task_id, req.point_index, req.vote)
    return {"ok": True}


TODO_PROMPT = """分析用户输入的事项,判断它是什么类型。按 JSON 输出,只输出 JSON:

{{"type": "考试/学习/生活/其他", "考试科目": "若为考试类,写出科目名(如:大学英语四级、高等数学),否则空字符串", "考试日期": "若提到日期,写 YYYY-MM-DD(未提年份时默认 2026 年),否则空字符串", "建议": "一句话建议(考试类:建议生成对应复习方案;学习类:给学习建议;生活类:提醒设置)"}}

用户输入:「{text}」"""


@router.post("/api/todo/analyze")
def todo_analyze(req: TodoRequest) -> dict:
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="内容为空")
    try:
        data = DeepSeekChannel().chat_json(TODO_PROMPT.format(text=req.text.strip()))
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return data
