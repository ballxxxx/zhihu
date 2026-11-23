# -*- coding: utf-8 -*-
"""期末搭子(FinalMate) FastAPI 入口。

D1 骨架:健康检查 + LLM 双通道调试接口。
后续将加入 /api/upload、/api/generate 等核心路由。
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import models
from app.routers import ai, generate, history, life, more, notes, upload
from app.services.llm import LLMError, get_channel

models.init_db()
app = FastAPI(title="期末搭子 FinalMate", version="0.1.0")
app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(history.router)
app.include_router(ai.router)
app.include_router(life.router)
app.include_router(more.router)
app.include_router(notes.router)

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATE_DIR = Path(__file__).parent / "templates"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/life", response_class=HTMLResponse)
def life_page() -> str:
    return (TEMPLATE_DIR / "life.html").read_text(encoding="utf-8")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "app": "final-mate"}


@app.get("/api/v1/llm/test")
def llm_test(channel: str = "deepseek", q: str = "用一句话解释什么是导数") -> dict:
    """调试接口:测试指定 LLM 通道。channel=deepseek|zhida"""
    try:
        answer = get_channel(channel).chat(q)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"channel": channel, "question": q, "answer": answer}
