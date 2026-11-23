# -*- coding: utf-8 -*-
"""11-24 里程碑·端到端联调:四场景(参谋/复习/记事/记录)全链路回归。

用法: py scripts/e2e_smoke.py [BASE_URL]   # 默认 http://127.0.0.1:8000
云端无历史任务时,复习段会自动先触发一次在线生成。
"""
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
SID = "e2e-" + time.strftime("%Y%m%d%H%M")
SID_FU = SID + "-fu"
passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}  {detail[:200]}")


def chat(msg, sid, timeout=180, location=None):
    payload = {"message": msg, "session_id": sid}
    if location:
        payload["location"] = location
    r = httpx.post(f"{BASE}/api/life/chat", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


# ---------- 参谋链路 ----------
print("== 参谋链路 ==")
# 1. 深圳湾回归(经典案例):建议带来源、双源印证、不追问
d = chat("周末去深圳湾吃海鲜,3个人,人均300,求推荐", SID)
adv = d.get("advice") or []
check("深圳湾案例 → 有建议", len(adv) >= 1, str(d)[:200])
check("深圳湾案例 → 不追问", not d.get("is_followup"))
check("深圳湾案例 → 建议带来源链接",
      all(a.get("来源链接", "").startswith("http") for a in adv if a.get("来源链接")))
print(f"   summary: {str(d.get('summary'))[:100]}")

# 2. 记忆查询(同会话,应记得刚才问了海鲜)
d = chat("我之前说过想吃什么来着", SID)
check("记忆查询 → is_memory", bool(d.get("is_memory")))
mem = str(d.get("memory_answer") or "")
check("记忆查询 → 回答提到海鲜", "海鲜" in mem, mem[:100])

# 3. 追问流:信息不足先追问
d = chat("周末想吃火锅", SID_FU)
check("追问流 → 第一步追问", bool(d.get("is_followup")))
# 第二步模拟前端行为:5分钟内短回答自动拼回原问题再发
d = chat("周末想吃火锅。2个人 预算200 江门", SID_FU)
check("追问流 → 第二步给出建议", (not d.get("is_followup")) and len(d.get("advice") or []) >= 1)

# 4. 考试学习引导
d = chat("明天要考高等数学了,有点慌", SID)
check("考试学习 → is_study 引导复习", bool(d.get("is_study")))

# 5. 记事意图
d = chat("帮我记一下周六上午9点去图书馆还书", SID)
check("记事 → is_note", bool(d.get("is_note")))
note_id = (d.get("note") or {}).get("id")

# 6. 避坑清单
d = chat("第一次租房要注意什么坑", SID)
check("避坑清单 → is_avoid", bool(d.get("is_avoid")))
check("避坑清单 → 有坑", len(((d.get("avoid") or {}).get("清单") or [])) >= 1)

# 7. 对比选择
d = chat("肯德基还是麦当劳", SID)
check("对比选择 → is_compare", bool(d.get("is_compare")))

# 8. 识图取链
with open("D:/claude code projects/screen-link/scripts/test_screen.png", "rb") as f:
    r = httpx.post(f"{BASE}/api/life/link-extract",
                   files={"file": ("test.png", f, "image/png")}, timeout=180)
d = r.json()
check("识图取链 → 3 链接", r.status_code == 200 and d.get("count") == 3, str(d)[:200])

# 8b. 位置场景:有定位说"附近" → 直接推荐;无定位 → 追问位置
d = chat("在我附近找吃的", SID_FU + "-loc", location="江门市")
check("位置场景 → 有定位直接推荐", (not d.get("is_followup")) and len(d.get("advice") or []) >= 1)
d = chat("在我附近找吃的", SID_FU + "-noloc")
check("位置场景 → 无定位追问位置", bool(d.get("is_followup")))

# 9. 今日回顾
d = httpx.get(f"{BASE}/api/life/daily", timeout=30).json()
check("今日回顾 → 接口正常", isinstance(d.get("conversations_today"), int) and "course" in d, str(d))

# ---------- 记事链路 ----------
print("== 记事链路 ==")
notes = httpx.get(f"{BASE}/api/notes", timeout=30).json().get("items", [])
check("记事本 → 含刚写入的还书待办",
      any("还书" in (n.get("content") or "") for n in notes), str(notes)[:150])
if note_id:
    r = httpx.post(f"{BASE}/api/notes/{note_id}/toggle", timeout=30)
    check("记事本 → 勾选打卡", r.status_code == 200 and r.json().get("ok"))
    httpx.post(f"{BASE}/api/notes/{note_id}/toggle", timeout=30)  # 还原

# ---------- 复习链路 ----------
print("== 复习链路 ==")
tasks = httpx.get(f"{BASE}/api/tasks", timeout=30).json().get("items", [])
done_id = next((t.get("id") for t in tasks if str(t.get("status", "")).startswith("done")), None)
if done_id is None:
    # 云端全新数据库:先触发一次在线生成(等待完成)
    print("   (无已完成任务,触发在线生成:高等数学...)")
    r = httpx.post(f"{BASE}/api/generate",
                   json={"doc_id": None, "course": "高等数学", "exam_date": "2026-12-25"},
                   timeout=30)
    r.raise_for_status()
    tid = r.json()["task_id"]
    for _ in range(90):
        time.sleep(5)
        st = httpx.get(f"{BASE}/api/task/{tid}", timeout=60).json()
        print(f"   [{st['status']}]", end="", flush=True)
        if str(st["status"]).startswith(("done", "failed")):
            print()
            break
    tasks = httpx.get(f"{BASE}/api/tasks", timeout=30).json().get("items", [])
    done_id = next((t.get("id") for t in tasks if str(t.get("status", "")).startswith("done")), None)
check("复习 → 历史任务列表", isinstance(tasks, list) and len(tasks) > 0)
check("复习 → 存在已完成任务", done_id is not None)
if done_id:
    t = httpx.get(f"{BASE}/api/task/{done_id}", timeout=30).json()
    pts = (t.get("result") or {}).get("points") or []
    check("复习 → 任务结果完整(重点/抽认卡/模拟题)",
          len(pts) > 0 and (t.get("result") or {}).get("cards") and (t.get("result") or {}).get("exam"))
    r = httpx.get(f"{BASE}/api/report/{done_id}", timeout=60)
    check("复习 → 报告页可访问", r.status_code == 200)
    # 伴随式 AI 问AI
    r = httpx.post(f"{BASE}/api/ask", json={"task_id": done_id, "point_index": 0,
                                            "question": "这个知识点怎么考"}, timeout=180)
    check("复习 → 伴随式问AI", r.status_code == 200 and bool(r.json().get("answer")))
    r = httpx.post(f"{BASE}/api/feedback", json={"task_id": done_id, "point_index": 0, "vote": "useful"},
                   timeout=30)
    check("复习 → 反馈闭环", r.status_code == 200 and r.json().get("ok"))
styles = httpx.get(f"{BASE}/api/styles", params={"course": "高等数学"}, timeout=30).json()
check("复习 → 数学族风格库", len(styles.get("styles") or {}) >= 4, str(styles)[:150])
styles_eng = httpx.get(f"{BASE}/api/styles", params={"course": "大学英语四级"}, timeout=30).json()
check("复习 → 英语族风格库", len(styles_eng.get("styles") or {}) >= 4, str(styles_eng)[:150])
r = httpx.get(f"{BASE}/api/syllabus", params={"course": "高等数学"}, timeout=60)
check("复习 → 章节大纲", r.status_code == 200 and len(r.json().get("chapters") or []) > 0,
      r.text[:150])

# ---------- 记录链路 ----------
print("== 记录链路 ==")
r = httpx.get(f"{BASE}/api/search", params={"q": "极限", "mode": "local"}, timeout=60)
check("记录 → 我的资料检索", r.status_code == 200)
r = httpx.get(f"{BASE}/api/search", params={"q": "极限", "mode": "global"}, timeout=120)
check("记录 → 全网知识检索", r.status_code == 200)

# ---------- 上传链路 ----------
print("== 上传链路 ==")
import pathlib

sample = pathlib.Path("data/samples/高等数学第一章课件.txt")
if sample.exists():
    with open(sample, "rb") as f:
        r = httpx.post(f"{BASE}/api/upload", files={"file": (sample.name, f, "text/plain")},
                       timeout=120)
    check("上传 → 课件入库", r.status_code == 200 and r.json().get("doc_id"), r.text[:200])
    docs = httpx.get(f"{BASE}/api/documents", timeout=30).json().get("items", [])
    check("上传 → 文档列表包含新文件", any("高等数学" in str(d.get("filename")) for d in docs))
else:
    print("SKIP 上传链路(样例课件不存在)")

# ---------- 待办分析 ----------
print("== 待办分析 ==")
r = httpx.post(f"{BASE}/api/todo/analyze", json={"text": "12月19日考大学英语四级"}, timeout=120)
check("待办分析 → 识别考试类", r.status_code == 200 and r.json().get("type") == "考试",
      r.text[:150])

# ---------- 今日外刊与数据洞察 ----------
print("== 今日外刊与数据洞察 ==")
r = httpx.get(f"{BASE}/api/news/today", timeout=240)
d = r.json()
check("今日外刊 → 双语新闻", r.status_code == 200 and len(d.get("news") or []) >= 3, r.text[:150])
d = httpx.get(f"{BASE}/api/insight/map", timeout=30).json()
check("数据洞察 → 大脑地图", isinstance(d.get("timeline"), list) and isinstance(d.get("categories"), list))
r = httpx.post(f"{BASE}/api/insight/weekly", timeout=240)
check("数据洞察 → 每周反思", r.status_code == 200 and bool(r.json().get("建议")), r.text[:150])
r = httpx.post(f"{BASE}/api/insight/persons", timeout=240)
check("数据洞察 → 人物卡片", r.status_code == 200 and isinstance(r.json().get("persons"), list))

print(f"\n===== {passed} PASS / {failed} FAIL =====")
