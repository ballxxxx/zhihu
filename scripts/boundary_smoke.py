# -*- coding: utf-8 -*-
"""11-24 里程碑·边界测试脚本:空输入 / 超长输入 / 搜索无结果兜底。

用法: py scripts/boundary_smoke.py
"""
import httpx

BASE = "http://127.0.0.1:8000"
ok = 0
fail = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global ok, fail
    if cond:
        ok += 1
        print(f"PASS  {name}")
    else:
        fail += 1
        print(f"FAIL  {name}  {detail}")


# 1. 空输入
r = httpx.post(f"{BASE}/api/life/chat", json={"message": ""}, timeout=60)
check("空消息 → 400", r.status_code == 400, f"got {r.status_code}")

r = httpx.post(f"{BASE}/api/life/chat", json={"message": "   "}, timeout=60)
check("纯空格 → 400", r.status_code == 400, f"got {r.status_code}")

# 2. 超长输入(>200 字)
r = httpx.post(f"{BASE}/api/life/chat", json={"message": "吃" * 201}, timeout=60)
check("201字 → 400", r.status_code == 400, f"got {r.status_code}")

# 3. todo 空内容
r = httpx.post(f"{BASE}/api/life/todo", json={"content": ""}, timeout=60)
check("todo空内容 → 400", r.status_code == 400, f"got {r.status_code}")

# 4. rule 空文件(解析不出文字)
r = httpx.post(f"{BASE}/api/life/rule", files={"file": ("empty.txt", b"")}, timeout=60)
check("rule空文件 → 400", r.status_code == 400, f"got {r.status_code}")

# 5. 搜索无结果兜底:意图明确(美食)+信息完整(不追问),但店名虚构搜不到
msg = "想找一家叫「咔滋咔滋神秘小馆」的餐厅，2个人，预算200，在江门"
r = httpx.post(
    f"{BASE}/api/life/chat",
    json={"message": msg, "session_id": "boundary-test"},
    timeout=180,
)
check("无意义查询 → 200 不崩溃", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
if r.status_code == 200:
    d = r.json()
    check("无意义查询 → 不触发追问", not d.get("is_followup"), str(d.get("intent", {})))
    links = [a.get("来源链接") for a in d.get("advice", []) if a.get("来源链接")]
    fake = [l for l in links if l and not l.startswith(("http://", "https://"))]
    check("建议链接均为 http(s)", not fake, str(links[:3]))
    print(f"   searched={d.get('searched')} advice={len(d.get('advice', []))} "
          f"summary={str(d.get('summary'))[:80]}")

print(f"\n{ok} PASS / {fail} FAIL")
