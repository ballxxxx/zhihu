# -*- coding: utf-8 -*-
"""数学文本清洗:$...$ 内的 Unicode 数学符号转 LaTeX 命令,裸幂次补花括号。

解决 LLM 输出里的不规范写法:∫[a,b]f(x)dx、e^-∫P、f²(x)、α/β 等,
统一成 MathJax 可正确渲染的规范 LaTeX。
"""
import re

UNICODE_TO_LATEX = {
    "∫": r"\int", "∬": r"\iint", "∑": r"\sum", "∏": r"\prod",
    "√": r"\sqrt", "α": r"\alpha", "β": r"\beta", "γ": r"\gamma",
    "θ": r"\theta", "λ": r"\lambda", "μ": r"\mu", "π": r"\pi",
    "φ": r"\varphi", "ψ": r"\psi", "ω": r"\omega",
    "Δ": r"\Delta", "Ω": r"\Omega", "∞": r"\infty",
    "→": r"\to", "←": r"\leftarrow", "≤": r"\leq", "≥": r"\geq",
    "≠": r"\neq", "±": r"\pm", "·": r"\cdot", "×": r"\times",
    "÷": r"\div", "≈": r"\approx", "∈": r"\in", "∉": r"\notin",
    "∂": r"\partial", "∅": r"\emptyset", "∩": r"\cap", "∪": r"\cup",
    "₀": "_0", "₁": "_1", "₂": "_2", "₃": "_3", "₄": "_4",
    "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
    "′": "'", "″": "''", "‖": r"\|", "∞型": r"\infty型",
}

_LATEX_SEG = re.compile(r"(\$[^$]+\$)")


def _fix_segment(body: str) -> str:
    for uni, latex in UNICODE_TO_LATEX.items():
        body = body.replace(uni, latex)
    # 裸幂次/下标补花括号:x^2 → x^{2}(仅当后跟单字符且非 {)
    body = re.sub(r"\^([A-Za-z0-9])(?![{])", r"^{\1}", body)
    body = re.sub(r"_([A-Za-z0-9])(?![{])", r"_{\1}", body)
    # 定积分方括号写法 ∫[a,b] → \int_{a}^{b}
    body = re.sub(r"\\int\s*\[([^\]]+),([^\]]+)\]", r"\\int_{\1}^{\2}", body)
    return body


def normalize(text: str) -> str:
    """清洗数学文本:统一公式包裹、修复未闭合/嵌套、$ 内转规范 LaTeX。"""
    if not text:
        return text
    # 1. 统一公式包裹:\(...\) 和 \[...\] 都转成 $...$
    text = text.replace(r"\(", "$").replace(r"\)", "$")
    text = text.replace(r"\[", "$").replace(r"\]", "$")
    # 2. 分 $ 段处理
    parts: list[str] = []
    for seg in _LATEX_SEG.split(text):
        if seg.startswith("$") and seg.endswith("$") and len(seg) > 1:
            body = _fix_segment(seg[1:-1])
            parts.append("$" + body + "$")
        else:
            parts.append(seg)
    result = "".join(parts)
    # 3. 奇数个 $:末尾补一个,兜底未闭合
    if result.count("$") % 2 == 1:
        result += "$"
    return result
