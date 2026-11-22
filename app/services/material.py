# -*- coding: utf-8 -*-
"""E1 在线资料构建:无文件模式下直接生成重点清单(一步到位)。

数据源决策(实测结论):
- DeepSeek 对自由文本 prompt 响应不稳定(偶尔"脱稿"输出泛化内容);
- 强制 JSON 结构化输出 + 自动重试后输出稳定,一步产出 points,少一层 LLM。
- 知乎直答行为不稳定(超时/元讨论),已退出管线;
- 知乎搜索只用于"经验板块"(已验证可靠)。
- 加课程一致性质检:DeepSeek 有时把"考试大纲"默认成高数,输出不含本族
  标志词(如英语族的听力/阅读)时自动带警告重试。
"""
from app.services import profiles
from app.services.llm import DeepSeekChannel, LLMError

# 科目族标志词:用于校验输出是否与课程一致
FAMILY_MARKERS = {
    profiles.FAMILY_MATH: ["极限", "导数", "积分", "函数", "几何", "代数", "方程", "级数", "概率", "矩阵"],
    profiles.FAMILY_ENGLISH: ["听力", "阅读", "写作", "翻译", "词汇", "语法", "口语", "单词"],
}

FAMILY_NAMES = {
    profiles.FAMILY_MATH: "数学类科目",
    profiles.FAMILY_ENGLISH: "英语类考试",
}


def _matches_family(points: list[dict], markers: list[str]) -> bool:
    text = " ".join(
        str(p.get("依据", "")) + str(p.get("出题方向", "")) + str(p.get("知识点", ""))
        for p in points
    )
    return any(m in text for m in markers)


def generate_outline_points(course: str, chapters: list[str] | None = None, max_attempts: int = 3) -> list[dict]:
    """DeepSeek 按科目族生成重点清单,带课程一致性质检。

    chapters: 用户勾选的章节范围(E2),无则覆盖教材全部范围。
    返回 [{"知识点", "考点等级", "出题方向", "依据"}]
    """
    family = profiles.detect_family(course)
    markers = FAMILY_MARKERS[family]
    chapters_text = "、".join(chapters) if chapters else "教材全部范围"
    points_target = max(10, min(30, len(chapters) * 2 + 4)) if chapters else 12
    base_prompt = profiles.get_profile(course)["outline_json_prompt"].format(
        course=course, chapters=chapters_text, points_target=points_target
    )
    prompt = base_prompt

    for _ in range(max_attempts):
        data = DeepSeekChannel().chat_json(prompt)
        points = [p for p in data.get("points", []) if isinstance(p, dict) and p.get("知识点")]
        if points and _matches_family(points, markers):
            return points
        prompt = (
            base_prompt
            + f"\n\n(警告:你上一条输出内容与《{course}》完全不符!这是{FAMILY_NAMES[family]}的大纲,"
              f"严禁输出其他科目的内容。请重新输出《{course}》自己的考点。)"
        )
    raise LLMError(f"大纲生成 {max_attempts} 次仍未通过课程一致性检查,请稍后重试")
