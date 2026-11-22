# -*- coding: utf-8 -*-
"""文本切块:把课件全文切成适合 LLM 处理的小块。

策略:优先按空行分段合并(保段落完整),超长段落按句号/分号切开。
"""

DEFAULT_MAX = 2000
DEFAULT_MIN = 300


def _split_long(paragraph: str, max_chars: int) -> list[str]:
    """超长段落按句子边界切开。"""
    pieces: list[str] = []
    current = ""
    # 以句号/分号/换行作为安全切分点
    for ch in paragraph:
        current += ch
        if ch in "。;；!！?？" and len(current) >= max_chars * 0.5:
            pieces.append(current)
            current = ""
    if current.strip():
        pieces.append(current)
    return pieces


def chunk_text(text: str, max_chars: int = DEFAULT_MAX, min_chars: int = DEFAULT_MIN) -> list[str]:
    """返回切好的文本块列表(每块不超过 max_chars,尽量不小于 min_chars)。"""
    raw_paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paras:
        return []

    chunks: list[str] = []
    buf = ""
    for para in raw_paras:
        # 长段落先自己切成合法小块
        parts = _split_long(para, max_chars) if len(para) > max_chars else [para]
        for part in parts:
            candidate = f"{buf}\n\n{part}".strip()
            if len(candidate) <= max_chars:
                buf = candidate
            else:
                if buf:
                    chunks.append(buf)
                buf = part
        if len(buf) >= max_chars:
            chunks.append(buf)
            buf = ""
    if buf:
        chunks.append(buf)

    # 收尾:过小的尾块并入前一块
    if len(chunks) >= 2 and len(chunks[-1]) < min_chars:
        chunks[-2] = f"{chunks[-2]}\n\n{chunks[-1]}".strip()[: max_chars * 2]
        chunks.pop()
    return chunks
