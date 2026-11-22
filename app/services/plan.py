# -*- coding: utf-8 -*-
"""D7 复习计划:按遗忘曲线(第1/2/4/7天复习)把重点排成每日任务。"""
from datetime import date, timedelta

REVIEW_OFFSETS = (1, 2, 4, 7)  # 新学后的第几天复习


def generate_plan(course: str, points: list[dict], days: int) -> dict:
    """把重点清单排成 days 天的复习计划。

    排序:高频在前;新内容按天分配;复习按遗忘曲线自动排。
    返回 {"days": [{"day": 1, "learn": [...], "review": [...], "tips": "..."}]}
    """
    if days <= 0:
        days = 7
    # 按考点等级排序:高频 > 中频 > 低频
    rank = {"高频": 0, "中频": 1, "低频": 2}
    ordered = sorted(points, key=lambda p: rank.get(str(p.get("考点等级", "中频")), 1))

    # 每天分配 2-3 个新知识点(内容少时每天 1 个)
    per_day = max(1, min(3, -(-len(ordered) // days) if ordered else 1))
    schedule: list[dict] = []
    learned: list[tuple[int, dict]] = []  # (学习日, 知识点)

    for day in range(1, days + 1):
        learn = []
        while ordered and len(learn) < per_day:
            p = ordered.pop(0)
            learn.append(p)
            learned.append((day, p))
        # 按遗忘曲线找今天要复习的
        review = [p for (d, p) in learned if (day - d) in REVIEW_OFFSETS]
        schedule.append({"day": day, "learn": learn, "review": review})

    # 每日 tips(按当天任务生成一句引导)
    for s in schedule:
        n_learn, n_review = len(s["learn"]), len(s["review"])
        if n_learn and n_review:
            tip = f"先花 20 分钟复习旧知识点,再学 {n_learn} 个新知识点;当天睡前把新学的抽认卡过一遍。"
        elif n_learn:
            tip = f"今天学 {n_learn} 个新知识点,配合抽认卡加深记忆;晚上睡前复述一遍今天的内容。"
        elif n_review:
            tip = f"今天以复习为主({n_review} 个知识点),合上笔记复述,卡住的地方重点标记。"
        else:
            tip = "查漏补缺日:重做一遍错题,浏览全部抽认卡。"
        s["tips"] = tip

    return {"days": schedule, "total_points": len(points)}


def format_dates(start: date | None, days: int) -> list[str]:
    """生成每天对应的日期标签(YYYY-MM-DD),供报告展示。"""
    if start is None:
        return [f"D{day}" for day in range(1, days + 1)]
    return [(start + timedelta(days=day - 1)).isoformat() for day in range(1, days + 1)]
