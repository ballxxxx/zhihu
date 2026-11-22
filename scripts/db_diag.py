# -*- coding: utf-8 -*-
"""临时诊断脚本:查看表结构、任务行、考试日期配置。用完可删。"""
import sqlite3

DB = "D:/claude code projects/final-mate/data/finalmate.db"
c = sqlite3.connect(DB)

print("== 表 ==")
print([r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")])

print("\n== tasks 全部 ==")
for r in c.execute("SELECT id, course, exam_date, status, created_at FROM tasks ORDER BY id"):
    print(r)

print("\n== notes ==")
for r in c.execute("SELECT id, quadrant, done, content, created_at FROM notes ORDER BY id"):
    print(r)

print("\n== conversations 近5条 ==")
for r in c.execute("SELECT session_id, category, message, created_at FROM conversations ORDER BY id DESC LIMIT 5"):
    print(r)
