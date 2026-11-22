# -*- coding: utf-8 -*-
"""生成接口:创建任务 → 后台执行管线 → 轮询进度取结果。"""
import json
import sqlite3
import threading
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import models
from app.services import profiles
from app.services.pipeline import generate_review_package

router = APIRouter()


class GenerateRequest(BaseModel):
    doc_id: int | None = None  # None=无文件模式,在线检索资料
    course: str
    exam_date: str | None = None  # YYYY-MM-DD
    chapters: list[str] | None = None  # E2:勾选的章节范围(无文件模式生效)
    style: str | None = None  # E5:模拟卷风格


def _run_task(task_id: int, req: GenerateRequest) -> None:
    def update(status: str, detail: str = "", result: dict | None = None) -> None:
        with models.get_db() as conn:
            conn.execute(
                "UPDATE tasks SET status=?, result_json=? WHERE id=?",
                (status, json.dumps(result, ensure_ascii=False) if result else None, task_id),
            )
            if detail:
                conn.execute(
                    "UPDATE tasks SET status=? WHERE id=?",
                    (f"{status}:{detail[:200]}", task_id),
                )

    try:
        result = generate_review_package(
            req.doc_id, req.course, req.exam_date, chapters=req.chapters, style=req.style, progress=update
        )
        update("done", result=result)
    except Exception as exc:  # noqa: BLE001 任何失败都要落状态
        update("failed", str(exc))


def _insert_task(req: GenerateRequest) -> int:
    with models.get_db() as conn:
        cur = conn.execute(
            "INSERT INTO tasks(doc_id, course, exam_date, status, created_at) VALUES(?,?,?,?,?)",
            (req.doc_id or 0, req.course, req.exam_date, "pending", datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def _get_task(task_id: int) -> sqlite3.Row | None:
    with models.get_db() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()


@router.post("/api/generate")
def generate(req: GenerateRequest) -> dict:
    if req.doc_id is not None and models.get_document(req.doc_id) is None:
        raise HTTPException(status_code=404, detail=f"文档不存在: doc_id={req.doc_id}")
    task_id = _insert_task(req)
    threading.Thread(target=_run_task, args=(task_id, req), daemon=True).start()
    return {"task_id": task_id, "status": "pending"}


@router.get("/api/syllabus")
def syllabus(course: str) -> dict:
    """按课程名返回可勾选的章节模板。匹配不到返回空 chapters。"""
    t = profiles.match_syllabus(course)
    if t is None:
        return {"course": course, "chapters": []}
    return {"course": t["course"], "chapters": t["chapters"]}


@router.get("/api/styles")
def styles(course: str) -> dict:
    """按课程名返回模拟卷风格库选项。"""
    return {"course": course, "styles": profiles.get_styles(course)}


@router.get("/api/task/{task_id}")
def task_status(task_id: int) -> dict:
    row = _get_task(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {
        "task_id": row["id"],
        "status": row["status"],
        "course": row["course"],
        "result": json.loads(row["result_json"]) if row["result_json"] else None,
    }
