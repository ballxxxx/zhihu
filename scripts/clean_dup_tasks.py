# -*- coding: utf-8 -*-
"""清理「我的复习方案」中的重复/僵尸任务(保留每组最新一条)。"""
import sqlite3

DB = "D:/claude code projects/final-mate/data/finalmate.db"
c = sqlite3.connect(DB)

print("== 清理前 ==")
for r in c.execute("SELECT id, course, exam_date, status FROM tasks ORDER BY id"):
    print(r)

# 每组 (course, exam_date) 只保留 id 最大的,其余删除
dups = c.execute(
    "SELECT course, IFNULL(exam_date, ''), MIN(id) AS keep_id, COUNT(*) AS n "
    "FROM tasks GROUP BY course, IFNULL(exam_date, '') HAVING n > 1"
).fetchall()
del_ids = []
for course, edate, keep_id, n in dups:
    del_ids += [r[0] for r in c.execute(
        "SELECT id FROM tasks WHERE course=? AND IFNULL(exam_date,'')=? AND id<>?",
        (course, edate, keep_id))]
# 僵尸任务:永远停在 searching 的
del_ids += [r[0] for r in c.execute("SELECT id FROM tasks WHERE status LIKE 'searching:%'")]

for tid in sorted(set(del_ids)):
    c.execute("DELETE FROM tasks WHERE id=?", (tid,))
    print(f"删除任务 {tid}")
c.commit()

print("== 清理后 ==")
for r in c.execute("SELECT id, course, exam_date, status FROM tasks ORDER BY id"):
    print(r)
