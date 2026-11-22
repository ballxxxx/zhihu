# -*- coding: utf-8 -*-
"""D5 测试:高数经验检索 + 真题渠道(消耗知乎搜索/DeepSeek 少量额度)。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.experience import enrich, extract_experiences, search_experiences


def main() -> None:
    course = "高等数学"
    print("== 搜索知乎经验 ==")
    entries = search_experiences(course)
    print(f"搜索到 {len(entries)} 条结果")

    exps = extract_experiences(course, entries)
    print(f"\n== 提取经验 {len(exps)} 条 ==")
    for e in exps:
        print(f"- {e.get('经验')} 【{e.get('相关知识点')}】 <{e.get('来源标题')}>")

    print("\n== 与重点清单对齐(用 D4 的 5 个重点做示例) ==")
    points = [
        {"知识点": "求极限的综合方法"},
        {"知识点": "等价无穷小替换"},
        {"知识点": "间断点类型的判断"},
        {"知识点": "零点定理证明"},
        {"知识点": "闭区间上连续函数的性质"},
    ]
    result = enrich(course, points)
    print(json.dumps(result, ensure_ascii=False, indent=2)[:3000])

    assert exps, "未提取到任何经验"
    print("\nPASS")


if __name__ == "__main__":
    main()
