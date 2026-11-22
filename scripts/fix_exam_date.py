# -*- coding: utf-8 -*-
"""一次性数据修复:清掉测试任务 id=16 的 exam_date(恰好是今天,导致倒计时显示0天)。"""
import sqlite3

DB = "D:/claude code projects/final-mate/data/finalmate.db"
c = sqlite3.connect(DB)
c.execute("UPDATE tasks SET exam_date=NULL WHERE id=16")
c.commit()
print("已修复 id=16:", c.execute("SELECT id, course, exam_date FROM tasks WHERE id=16").fetchone())
print("最近的未来考试:", c.execute(
    "SELECT id, course, exam_date FROM tasks WHERE exam_date IS NOT NULL "
    "AND exam_date >= date('now','localtime') ORDER BY exam_date LIMIT 3").fetchall())
