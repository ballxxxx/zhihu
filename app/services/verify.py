# -*- coding: utf-8 -*-
"""P0a 质量加固:划重点"依据"逐字校验。

校验规则:依据经归一化(去所有标点/空白,保留文字)后,与源文本的归一化形式
求最长公共子串,公共子串 >=6 字符视为有原文支撑,否则丢弃该重点。
"""
import re

MIN_MATCH = 6  # 最长公共子串最小长度


def _norm(text: str) -> str:
    # 保留汉字/字母/数字,去掉标点与空白(含中文标点)
    return re.sub(r"[\W_]+", "", str(text), flags=re.UNICODE)


def _lcs_len(a: str, b: str) -> int:
    """最长公共子串长度(O(n*m),课件文本短,可接受)。"""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    best = 0
    for ch_a in a:
        cur = [0] * (len(b) + 1)
        for j, ch_b in enumerate(b, 1):
            if ch_a == ch_b:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def verify_points(points: list[dict], source_text: str) -> tuple[list[dict], list[dict]]:
    """校验重点清单,返回 (保留列表, 丢弃列表)。

    无依据字段的重点保留(如无文件模式的模块名依据)。"""
    src = _norm(source_text)
    kept: list[dict] = []
    dropped: list[dict] = []
    for p in points:
        basis = str(p.get("依据", "")).strip()
        if not basis:
            kept.append(p)
            continue
        match = _lcs_len(_norm(basis), src)
        if match >= MIN_MATCH:
            kept.append(p)
        else:
            dropped.append({**p, "_drop_reason": f"依据未在原文中找到(匹配{match}字)"})
    return kept, dropped
