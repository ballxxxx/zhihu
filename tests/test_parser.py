# -*- coding: utf-8 -*-
"""D2 测试:三种格式解析 + 切块。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.services.chunker import chunk_text
from app.services.parser import parse_file

SAMPLE_DIR = config.DATA_DIR / "samples"


def test_parse_all_formats():
    for name in ("高等数学第一章课件.txt", "高等数学第一章课件.docx", "高等数学第一章课件.pdf"):
        path = SAMPLE_DIR / name
        text = parse_file(path)
        print(f"[{name}] {len(text)} 字符")
        assert "极限" in text and "间断点" in text, f"{name} 内容不完整"


def test_chunk():
    text = parse_file(SAMPLE_DIR / "高等数学第一章课件.txt")
    chunks = chunk_text(text, max_chars=800)
    print(f"[chunk] max=800 -> {len(chunks)} 块,块长: {[len(c) for c in chunks]}")
    assert len(chunks) >= 2, "切块数量过少"
    assert all(len(c) <= 800 for c in chunks), "存在超过上限的块"
    joined = "\n".join(chunks)
    assert "等价无穷小" in joined and "零点定理" in joined, "切块丢失内容"

    # 全文小于上限时应合并为一块
    single = chunk_text(text, max_chars=2000)
    assert len(single) == 1, "小文本应合并为单块"


if __name__ == "__main__":
    test_parse_all_formats()
    test_chunk()
    print("\nALL PASS")
