# -*- coding: utf-8 -*-
"""D4 划重点管线:课件切块 → LLM 逐块提取重点 → 合并成重点清单。

输出结构:
{"course": str, "family": str, "points": [{知识点, 考点等级, 出题方向, 依据}]}

通道决策(实测经验):划重点固定用 DeepSeek——指令遵循稳定、输出必来自输入材料、
不受官方直答额度(100/天)限制。直答仅用于无文件模式的课程大纲生成。
"""
from app.services import profiles
from app.services.llm import DeepSeekChannel, LLMError


def _build_prompt(course: str, chunk: str) -> str:
    family = profiles.detect_family(course)
    template = profiles.get_profile(course)["highlight_prompt"]
    return template.format(course=course, chunk=chunk)


def highlight_chunk(course: str, chunk: str) -> list[dict]:
    """对单个文本块提取重点,返回 points 列表。"""
    prompt = _build_prompt(course, chunk)
    data = DeepSeekChannel().chat_json(prompt)
    points = data.get("points")
    if not isinstance(points, list):
        raise LLMError(f"划重点未按格式返回 points: {str(data)[:200]}")
    return [p for p in points if isinstance(p, dict) and p.get("知识点")]


def highlight_document(course: str, chunks: list[str], progress=None) -> dict:
    """对全部文本块划重点并合并。

    progress: 可选回调 progress(done, total),用于进度展示。
    """
    all_points: list[dict] = []
    errors: list[str] = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks):
        try:
            all_points.extend(highlight_chunk(course, chunk))
        except LLMError as exc:
            errors.append(f"块{idx + 1}: {exc}")
        if progress:
            progress(idx + 1, total)

    # 按知识点名去重(保留首次出现的完整信息)
    seen: set[str] = set()
    deduped: list[dict] = []
    for p in all_points:
        key = str(p.get("知识点", "")).strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(p)

    return {
        "course": course,
        "family": profiles.detect_family(course),
        "points": deduped,
        "errors": errors,
    }
