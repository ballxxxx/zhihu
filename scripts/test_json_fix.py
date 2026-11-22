# -*- coding: utf-8 -*-
"""验证 _extract_json 的 LaTeX 反斜杠清洗修复。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.llm import _extract_json

cases = [
    ('{"q": "\\\\frac{1}{x} 正确转义"}', '\\frac{1}{x} 正确转义'),   # 正常 JSON 不受影响
    ('{"q": "\\frac{1}{x} 未转义"}', '\\frac{1}{x} 未转义'),        # 非法转义被清洗
    ('{"a": "\\n换行"}', '\n换行'),                                  # 合法转义保持
    ('前缀 {"k": "\\lim x"} 后缀', '\\lim x'),                       # 花括号提取+清洗
    ('```json\n{"x": "\\int_0^1"}', '\\int_0^1'),                   # 代码块包裹+清洗
]

for raw, expect in cases:
    got = _extract_json(raw)
    key = "q" if "q" in got else ("a" if "a" in got else "k" if "k" in got else "x")
    ok = got.get(key) == expect
    print(("PASS" if ok else "FAIL"), repr(got.get(key)), "<->", repr(expect))
