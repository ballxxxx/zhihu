# -*- coding: utf-8 -*-
"""D4 测试:对高数样例课件跑划重点管线(消耗少量直答额度)。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.services.chunker import chunk_text
from app.services.highlight import highlight_document
from app.services.parser import parse_file


def main() -> None:
    text = parse_file(config.DATA_DIR / "samples" / "高等数学第一章课件.txt")
    chunks = chunk_text(text)
    print(f"文本 {len(text)} 字符 -> {len(chunks)} 块")

    result = highlight_document("高等数学", chunks, progress=lambda d, t: print(f"  划重点 {d}/{t}"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    assert len(result["points"]) >= 3, "提取的重点过少"
    print(f"\nPASS: 提取 {len(result['points'])} 个重点")


if __name__ == "__main__":
    main()
