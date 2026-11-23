# -*- coding: utf-8 -*-
"""数据洞察(增量池):大脑地图(时间线+话题聚类)、每周反思卡片、人物卡片。"""
from datetime import datetime, timedelta

from app import models
from app.services.llm import DeepSeekChannel


def get_map() -> dict:
    """大脑地图(轻量版):近期动向时间线 + 话题分布 + 反馈统计(纯 DB 聚合,无 LLM)。"""
    with models.get_db() as conn:
        timeline = conn.execute(
            "SELECT category, message, created_at FROM conversations "
            "ORDER BY id DESC LIMIT 30"
        ).fetchall()
        cats = conn.execute(
            "SELECT category, COUNT(*) AS n FROM conversations "
            "WHERE category IS NOT NULL AND category != '' "
            "GROUP BY category ORDER BY n DESC LIMIT 8"
        ).fetchall()
        feedbacks = conn.execute(
            "SELECT vote, COUNT(*) AS n FROM feedbacks GROUP BY vote"
        ).fetchall()
    return {
        "timeline": [
            {
                "category": r["category"] or "?",
                "message": (r["message"] or "")[:60],
                "time": (r["created_at"] or "")[:16].replace("T", " "),
            }
            for r in timeline
        ],
        "categories": [{"name": r["category"], "n": r["n"]} for r in cats],
        "feedbacks": {r["vote"]: r["n"] for r in feedbacks},
    }


WEEKLY_PROMPT = """以下是用户最近一周在本产品中的动向:

【对话】
{convs}

【待办】
{notes}

请给用户写一张「每周反思卡片」,按 JSON 输出,只输出 JSON:
{{"回顾": "2-3句话总结本周动向(学习/生活/消费,基于给定数据)", "建议": "一条具体的下周建议(要具体、可执行,如'考前把导数章节错题重做一遍')", "亮点": "本周做得好的1件事(没有则写'继续保持记录习惯')"}}

要求:只依据给定数据,不得编造;语气像一个贴心的搭子;只输出 JSON。"""


def weekly_reflection() -> dict:
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
    with models.get_db() as conn:
        convs = conn.execute(
            "SELECT message, category FROM conversations WHERE created_at >= ? "
            "ORDER BY id DESC LIMIT 40",
            (since,),
        ).fetchall()
        notes = conn.execute(
            "SELECT content, done FROM notes WHERE created_at >= ? ORDER BY id DESC LIMIT 20",
            (since,),
        ).fetchall()
    conv_text = "\n".join(f"- [{r['category'] or '?'}] {(r['message'] or '')[:60]}" for r in convs) or "(无)"
    note_text = "\n".join(
        f"- [{'✓' if r['done'] else '○'}] {(r['content'] or '')[:50]}" for r in notes
    ) or "(无)"
    return DeepSeekChannel().chat_json(
        WEEKLY_PROMPT.format(convs=conv_text, notes=note_text)
    )


PERSONS_PROMPT = """以下是用户在本产品中的近期对话记录:

{data}

请找出用户提到过的人(朋友/老师/家人等),为每人建一张小卡片,按 JSON 输出,只输出 JSON:
{{"人物": [{{"称呼": "如:室友小李/张老师", "话题": "一起聊过什么(1句话)", "建议": "下次可以聊/提醒什么(1句话,没有则空)"}}]}}

要求:只依据给定数据;没有提到任何人则输出 {{"人物": []}};最多 6 人;只输出 JSON。"""


def persons() -> dict:
    with models.get_db() as conn:
        convs = conn.execute(
            "SELECT message FROM conversations ORDER BY id DESC LIMIT 60"
        ).fetchall()
    data = "\n".join(f"- {(r['message'] or '')[:80]}" for r in convs) or "(无)"
    result = DeepSeekChannel().chat_json(PERSONS_PROMPT.format(data=data))
    people = result.get("人物") or []
    return {"persons": [p for p in people if isinstance(p, dict) and p.get("称呼")][:6]}
