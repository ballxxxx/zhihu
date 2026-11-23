# -*- coding: utf-8 -*-
"""云端演示数据补齐:四象限待办 + 英语四级复习方案(云端已有高数方案)。"""
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://finalmate-352354-12-1538712646.sh.run.tcloudbase.com"

# 四象限待办(演示记事 tab)
notes = [
    ("12月19日考大学英语四级,核心词汇还没背完", 1),
    ("周六上午9点去图书馆还书,别逾期", 2),
    ("今晚23点前交高数作业", 1),
    ("周末和室友去江门万达聚餐", 4),
]
for content, q in notes:
    r = httpx.post(f"{BASE}/api/notes", json={"content": content, "quadrant": q}, timeout=30)
    print("note", r.status_code, content[:22])

# 英语四级方案(补英语族)
r = httpx.post(
    f"{BASE}/api/generate",
    json={"doc_id": None, "course": "大学英语四级", "exam_date": "2026-12-19"},
    timeout=30,
)
print("generate:", r.status_code)
tid = (r.json() or {}).get("task_id")
if tid:
    for _ in range(90):
        time.sleep(5)
        st = httpx.get(f"{BASE}/api/task/{tid}", timeout=60).json()
        print(" ", st["status"])
        if str(st["status"]).startswith(("done", "failed")):
            break
print("演示数据补齐完成")
