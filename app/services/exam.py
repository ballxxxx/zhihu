# -*- coding: utf-8 -*-
"""D6 模拟题生成:按科目族题型风格出卷(DeepSeek 批量生成)。"""
from app.services import profiles
from app.services.llm import DeepSeekChannel, LLMError


def generate_exam(course: str, points: list[dict], style: str | None = None) -> list[dict]:
    """按科目族的题型风格生成一套模拟题。style 为风格库选项(E5)。"""
    family = profiles.detect_family(course)
    template = profiles.get_profile(course)["exam_prompt"]
    points_text = "\n".join(f"- {p.get('知识点', '')}({p.get('考点等级', '')})" for p in points)
    style_line = ""
    if style:
        guide = profiles.get_style_guide(style)
        style_line = f"\n试卷风格:{style}。出卷要求:{guide or '贴近该风格常规出题模式'}。"
    data = DeepSeekChannel().chat_json(
        template.format(course=course, points=points_text) + style_line
    )
    questions = data.get("questions")
    if not isinstance(questions, list):
        raise LLMError(f"模拟题格式错误: {str(data)[:200]}")
    return [q for q in questions if isinstance(q, dict) and q.get("题干")]
