# -*- coding: utf-8 -*-
"""D9 历史记录 + 知识库检索接口。E3:双通道检索 + 原文视图。"""
import html as html_mod
import json

from fastapi import APIRouter, HTTPException, Response

from app import models
from app.services import zhihu
from app.services.experience import _parse_search
from app.services.report import render_report

router = APIRouter()


@router.get("/api/tasks")
def tasks(limit: int = 20) -> dict:
    return {"items": [dict(r) for r in models.list_tasks(limit)]}


@router.get("/api/report/{task_id}")
def report(task_id: int) -> Response:
    """按任务渲染 HTML 报告(单文件,可直接分享)。"""
    row = models.get_task(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not row["result_json"]:
        raise HTTPException(status_code=409, detail=f"任务尚未完成(status={row['status']})")
    result = json.loads(row["result_json"])
    html = render_report(result, task_id=task_id)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/api/search")
def search(q: str, mode: str = "local", limit: int = 5) -> dict:
    """知识库检索双通道。

    mode=local:全文检索本地上传过的资料;
    mode=global:知乎站内实时搜索(带链接可直达原帖)。
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="缺少查询参数 q")
    if mode == "global":
        try:
            entries = _parse_search(zhihu.search_zhihu(q, count=limit))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"知乎搜索失败: {exc}")
        return {
            "query": q,
            "mode": "global",
            "hits": [{"title": e["title"], "url": e["url"], "snippet": e["text"][:200]} for e in entries],
        }
    return {"query": q, "mode": "local", "hits": models.search_documents(q, limit)}


@router.get("/api/document/{doc_id}/raw")
def document_raw(doc_id: int) -> Response:
    """查看上传资料的原文(纯文本页)。"""
    doc = models.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    body = html_mod.escape(doc["raw_text"]).replace("\n", "<br>")
    page = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{html_mod.escape(doc["filename"])} - 原文</title>
<style>body{{font-family:'Microsoft YaHei',sans-serif;max-width:800px;margin:24px auto;padding:0 16px;line-height:1.9;}}
h1{{font-size:20px;border-bottom:2px solid #0084ff;padding-bottom:8px;color:#333;}}
.meta{{color:#8a919f;font-size:12px;margin-bottom:16px;}}</style></head>
<body><h1>{html_mod.escape(doc["filename"])}</h1>
<div class="meta">{doc["created_at"]} 上传 · {len(doc["raw_text"])} 字符</div>
<div>{body}</div></body></html>"""
    return Response(content=page, media_type="text/html; charset=utf-8")
