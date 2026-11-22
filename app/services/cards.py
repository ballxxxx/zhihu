# -*- coding: utf-8 -*-
"""D6 抽认卡生成:把重点清单转成问答对卡片(DeepSeek 批量生成)。

数学族:概念问答 + 方法辨析;英语族:词汇/表达卡。
"""
import json

from app.services import profiles
from app.services.llm import DeepSeekChannel, LLMError

CARD_PROMPT = """你是《{course}》的复习教练。请把以下重点知识点做成抽认卡(问答对):

{points}

按 JSON 输出:
{{"cards": [{{"q": "问题(像考试题一样提问)", "a": "答案(精炼、可背诵,不超过60字)"}}]}}

要求:
- 每个知识点至少 1 张卡,特别高频的可 2 张;
- {style_rule}
- 最多 20 张;问题要能独立成立(不依赖上下文);
- **数学公式必须用 $...$ 包裹并写规范 LaTeX**:幂次用花括号 $x^{{2}}$、积分 $\\int_{{a}}^{{b}}$、分数 $\\frac{{}}{{}}$;
- 禁止使用 Unicode 数学符号(∫、²、α、→ 等),一律用 LaTeX 命令($\\int$、$x^{{2}}$、$\\alpha$)。"""

STYLE_RULES = {
    profiles.FAMILY_MATH: "问题侧重概念辨析与方法选择(如\"什么时候能用等价无穷小替换?\"),答案给出条件+结论;",
    profiles.FAMILY_ENGLISH: "问题侧重词汇含义/用法辨析/考点规则,答案给出简洁释义或规则;",
}


def generate_cards(course: str, points: list[dict]) -> list[dict]:
    """按科目族风格生成抽认卡。"""
    family = profiles.detect_family(course)
    points_text = "\n".join(f"- {p.get('知识点', '')}({p.get('考点等级', '')})" for p in points)
    prompt = CARD_PROMPT.format(course=course, points=points_text, style_rule=STYLE_RULES[family])
    data = DeepSeekChannel().chat_json(prompt)
    cards = data.get("cards")
    if not isinstance(cards, list):
        raise LLMError(f"抽认卡格式错误: {str(data)[:200]}")
    return [c for c in cards if isinstance(c, dict) and c.get("q") and c.get("a")]
