# -*- coding: utf-8 -*-
"""D6 测试:高数样例课件 → 划重点 → 抽认卡 + 模拟题(DeepSeek 批量)。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.services.cards import generate_cards
from app.services.chunker import chunk_text
from app.services.exam import generate_exam
from app.services.highlight import highlight_document
from app.services.parser import parse_file


def main() -> None:
    text = parse_file(config.DATA_DIR / "samples" / "高等数学第一章课件.txt")
    chunks = chunk_text(text)
    result = highlight_document("高等数学", chunks)
    points = result["points"]
    print(f"重点 {len(points)} 个")

    cards = generate_cards("高等数学", points)
    print(f"\n== 抽认卡 {len(cards)} 张 ==")
    for c in cards[:5]:
        print(f"Q: {c['q']}\nA: {c['a']}\n")

    exam = generate_exam("高等数学", points)
    print(f"== 模拟题 {len(exam)} 题 ==")
    for q in exam[:3]:
        print(f"题: {q['题干'][:80]}...")

    assert cards and exam
    print("\nPASS")


if __name__ == "__main__":
    main()
