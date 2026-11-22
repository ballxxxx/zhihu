# -*- coding: utf-8 -*-
"""D1 冒烟测试:两个 LLM 通道各跑一次。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.llm import DeepSeekChannel, LLMError, ZhidaChannel

QUESTION = "用一句话解释什么是导数"


def test_deepseek():
    out = DeepSeekChannel().chat(QUESTION)
    print(f"[deepseek] {out[:120]}")
    assert out.strip(), "DeepSeek 返回为空"


def test_zhida():
    out = ZhidaChannel().chat(QUESTION)
    print(f"[zhida] {out[:120]}")
    assert out.strip(), "直答返回为空"


if __name__ == "__main__":
    for name, fn in [("deepseek", test_deepseek), ("zhida", test_zhida)]:
        print(f"=== 测试 {name} ===")
        try:
            fn()
            print(f"{name}: PASS\n")
        except Exception as exc:
            print(f"{name}: FAIL -> {exc}\n")
            sys.exit(1)
    print("ALL PASS")
