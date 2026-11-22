# -*- coding: utf-8 -*-
"""D7 全链路编排:上传资料 → 划重点 → 经验 → 抽认卡 → 模拟题 → 复习计划。

E1:支持 doc_id=None 的无文件模式——在线检索知乎资料代替课件。
"""
from datetime import date

from app import models
from app.services import experience, material, profiles, verify
from app.services.cards import generate_cards
from app.services.chunker import chunk_text
from app.services.exam import generate_exam
from app.services.highlight import highlight_document
from app.services.plan import generate_plan


def generate_review_package(
    doc_id: int | None,
    course: str,
    exam_date: str | None,
    chapters: list[str] | None = None,
    style: str | None = None,
    progress=None,
) -> dict:
    """核心管线:一次调用产出完整复习方案。

    doc_id=None 时走无文件模式;chapters 为勾选的章节范围(仅无文件模式生效);
    style 为模拟卷风格(E5 风格库)。
    progress: 可选回调 progress(stage, detail) 用于状态上报。
    """

    def report(stage: str, detail: str = "") -> None:
        if progress:
            progress(stage, detail)

    dropped: list = []

    if doc_id:
        doc = models.get_document(doc_id)
        if doc is None:
            raise ValueError(f"文档不存在: doc_id={doc_id}")
        raw_text, source_filename = doc["raw_text"], doc["filename"]
        chunks = chunk_text(raw_text)
        report("highlighting", f"划重点({len(chunks)} 块)")
        highlights = highlight_document(course, chunks)
        points = highlights["points"]
        if not points:
            raise ValueError("未提取到重点,请检查课件内容是否完整")
        # P0a:依据逐字校验,引用不上原文的重点丢弃
        points, dropped = verify.verify_points(points, raw_text)
        if not points:
            raise ValueError("划重点结果全部未通过原文校验,请检查课件内容")
        family = highlights["family"]
    else:
        # 无文件模式:DeepSeek 一步生成重点清单
        report("material", "在线生成知识点大纲")
        points = material.generate_outline_points(course, chapters=chapters)
        if not points:
            raise ValueError("在线大纲生成失败,请稍后重试或改为上传课件")
        source_filename = "在线生成大纲(DeepSeek)"
        family = profiles.detect_family(course)

    report("searching", "检索知乎经验")
    enriched = experience.enrich(course, points)

    report("cards", "生成抽认卡")
    cards = generate_cards(course, points)

    report("exam", "生成模拟题")
    exam = generate_exam(course, points, style=style)

    report("plan", "排复习计划")
    # 考试日期解析 + 剩余天数
    try:
        target = date.fromisoformat(exam_date) if exam_date else None
    except ValueError:
        target = None
    if target:
        remaining = max((target - date.today()).days + 1, 1)
    else:
        target = None
        remaining = 7
    plan = generate_plan(course, points, days=remaining)

    report("done", "")
    return {
        "course": course,
        "family": family,
        "exam_date": target.isoformat() if target else None,
        "days": remaining,
        "points": points,
        "experiences": enriched["experiences_matched"],
        "general_experiences": enriched["general"],
        "channels": enriched["channels"],
        "cards": cards,
        "exam": exam,
        "plan": plan,
        "source_filename": source_filename,
        "quality": {"dropped_points": len(dropped)},
    }
