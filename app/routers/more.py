# -*- coding: utf-8 -*-
"""今日外刊 + 数据洞察接口(P2 + 增量池)。"""
from fastapi import APIRouter, HTTPException

from app.services import insight, news
from app.services.llm import LLMError

router = APIRouter()


@router.get("/api/news/today")
def news_today() -> dict:
    try:
        return news.fetch_news()
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/api/insight/map")
def insight_map() -> dict:
    return insight.get_map()


@router.post("/api/insight/weekly")
def insight_weekly() -> dict:
    try:
        return insight.weekly_reflection()
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/api/insight/persons")
def insight_persons() -> dict:
    try:
        return insight.persons()
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
