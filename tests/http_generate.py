# -*- coding: utf-8 -*-
"""HTTP 测试:无文件模式生成(用 httpx,避开 PowerShell 编码坑)。

用法: py tests/http_generate.py <课程名> [考试日期]
"""
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"


def main() -> None:
    course = sys.argv[1] if len(sys.argv) > 1 else "大学英语四级"
    exam_date = sys.argv[2] if len(sys.argv) > 2 else None

    resp = httpx.post(
        f"{BASE}/api/generate",
        json={"doc_id": None, "course": course, "exam_date": exam_date},
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["task_id"]
    print(f"task_id: {task_id}")

    for _ in range(60):
        time.sleep(5)
        st = httpx.get(f"{BASE}/api/task/{task_id}", timeout=30).json()
        status = st["status"]
        print(f"  [{status}]")
        if status.startswith("done") or status.startswith("failed"):
            break

    full = httpx.get(f"{BASE}/api/task/{task_id}", timeout=30).json()
    result = full.get("result") or {}
    points = result.get("points", [])
    print(f"\n结果: 重点 {len(points)} / 抽认卡 {len(result.get('cards', []))} / "
          f"模拟题 {len(result.get('exam', []))} / 经验 {len(result.get('general_experiences', []))} 条")
    print("重点列表:")
    for p in points:
        print(f"  - {p.get('知识点')} [{p.get('考点等级')}] → {p.get('出题方向')}")
    # 供后续步骤使用:保存完整结果
    out = "data/last_result.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n完整结果: {out}")


if __name__ == "__main__":
    main()
