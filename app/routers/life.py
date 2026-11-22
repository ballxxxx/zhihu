# -*- coding: utf-8 -*-
"""「生活参谋」接口:对话式生活决策建议(带轻量记忆)。"""
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel

from app import config, models
from app.services import linkx, parser
from app.services.life import RULE_PROMPT, build_advice
from app.services.llm import DeepSeekChannel, LLMError

router = APIRouter()

TODO_QUADRANT_PROMPT = """你是时间管理助手。把这条"采纳的 AI 建议"变成一条待办,并判断象限,按 JSON 输出,只输出 JSON:
{{"事项": "一句话待办(保留地点/店名/时间等关键信息,如:周日中午去盐田海鲜街华城渔港,3人)","象限": 1|2|3|4, "说明": "一句话理由"}}
象限定义:1=重要且紧急(立即做) 2=重要不紧急(计划做) 3=紧急不重要(快速处理) 4=不重要不紧急(暂缓或放弃)
建议内容:「{text}」"""


class LifeRequest(BaseModel):
    message: str
    session_id: str | None = None  # 浏览器本地生成的会话标识,用于轻量记忆
    location: str | None = None  # 浏览器定位/手动设置的位置(城市名或坐标)


class TodoRequest(BaseModel):
    content: str


@router.post("/api/life/rule")
async def rule_explain(file: UploadFile = File(...)) -> dict:
    """校园规则解读:上传保研细则/奖学金评定/培养方案 → 人话解读+隐藏陷阱。"""
    suffix = Path(file.filename or "").suffix or ".pdf"
    tmp = config.DATA_DIR / "uploads" / f"rule_{uuid4().hex}{suffix}"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(await file.read())
    try:
        text = parser.parse_file(tmp)
    except parser.ParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        tmp.unlink(missing_ok=True)
    if len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="文件里没解析出文字,试试转成 PDF 或图片")
    try:
        data = DeepSeekChannel().chat_json(RULE_PROMPT.format(text=text[:6000]))
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {
        "ok": True,
        "要点": [x for x in (data.get("要点") or []) if isinstance(x, dict) and x.get("人话")][:8],
        "陷阱": [x for x in (data.get("陷阱") or []) if isinstance(x, dict) and x.get("坑")][:4],
        "总结": str(data.get("总结") or ""),
    }


@router.post("/api/life/link-extract")
async def link_extract(file: UploadFile = File(...)) -> dict:
    """识图取链:粘贴/上传截图 → OCR + 二维码提取可跳转链接。"""
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片过大(最大8MB)")
    try:
        img = Image.open(BytesIO(data))
        img.load()
    except Exception:
        raise HTTPException(status_code=400, detail="图片格式无法识别(支持 png/jpg/bmp/webp)")
    if img.format not in ("PNG", "JPEG", "BMP", "WEBP"):
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {img.format}")
    links = linkx.extract_links(img)
    return {
        "ok": True,
        "count": len(links),
        "links": links,
        "hint": "" if links else "没识别出链接:截图里可能没有网址文字/二维码,或图片太模糊,试试截大一点再传",
    }


@router.post("/api/life/todo")
def advice_to_todo(req: TodoRequest) -> dict:
    """把采纳的建议转成执行待办,进四象限记事本。"""
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="内容为空")
    content = req.content.strip()[:120]
    try:
        data = DeepSeekChannel().chat_json(TODO_QUADRANT_PROMPT.format(text=content))
    except LLMError:
        data = {}
    quadrant = data.get("象限") if data.get("象限") in (1, 2, 3, 4) else 2
    note_id = models.insert_note(str(data.get("事项") or content), quadrant)
    return {"ok": True, "id": note_id, "quadrant": quadrant}


@router.get("/api/life/daily")
def daily_summary() -> dict:
    """今日回顾卡片:今天问过什么、新增待办、距考试几天。"""
    return models.get_daily_stats()


@router.post("/api/life/chat")
def life_chat(req: LifeRequest) -> dict:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="内容为空")
    if len(req.message) > 200:
        raise HTTPException(status_code=400, detail="问题过长(200字内)")
    try:
        result = build_advice(req.message.strip(), session_id=req.session_id, location=req.location)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    # 存记忆(考试类也存,下次能记住用户在备考)
    if req.session_id:
        try:
            models.insert_conversation(
                req.session_id, req.message.strip(), result.get("intent", {}).get("类别")
            )
        except Exception:
            pass
    return result
