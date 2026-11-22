# -*- coding: utf-8 -*-
"""sqlite 数据层:documents(上传资料)/ tasks(生成任务)。"""
import re
import sqlite3
from datetime import datetime

from app import config

DB_PATH = config.DATA_DIR / "finalmate.db"

# FTS5 默认分词不支持中文(无空格),采用字符级索引:
# 连续中文拆成单字序列,英文/数字保持原样,查询时同样处理。
_CJK = re.compile(r"[一-鿿]")


def _index_text(text: str) -> str:
    """把文本转成 FTS 友好的字符级 token 序列。"""
    text = re.sub(r"\s+", " ", text)
    return _CJK.sub(lambda m: f" {m.group(0)} ", text)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS documents(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                course TEXT NOT NULL,
                exam_date TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                result_json TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS feedbacks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                point_index INTEGER NOT NULL,
                vote TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS conversations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS notes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                quadrant INTEGER NOT NULL DEFAULT 1,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )"""
        )
        # FTS5 全文检索(知识库:跨上传资料搜索)
        conn.execute(
            """CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                doc_id UNINDEXED, filename, content
            )"""
        )
        # 回填:升级前已存在的文档补进索引(字符级分词)
        rows = conn.execute(
            """SELECT d.id, d.filename, d.raw_text FROM documents d
               WHERE d.id NOT IN (SELECT doc_id FROM documents_fts)"""
        ).fetchall()
        for r in rows:
            conn.execute(
                "INSERT INTO documents_fts(doc_id, filename, content) VALUES(?,?,?)",
                (r["id"], r["filename"], _index_text(r["raw_text"])),
            )


def insert_document(filename: str, raw_text: str, chunk_count: int) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO documents(filename, raw_text, chunk_count, created_at) VALUES(?,?,?,?)",
            (filename, raw_text, chunk_count, datetime.now().isoformat(timespec="seconds")),
        )
        doc_id = cur.lastrowid
        conn.execute(
            "INSERT INTO documents_fts(doc_id, filename, content) VALUES(?,?,?)",
            (doc_id, filename, _index_text(raw_text)),
        )
        return doc_id


def get_document(doc_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()


def list_documents(limit: int = 20) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT id, filename, chunk_count, created_at FROM documents ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def list_tasks(limit: int = 20) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT id, doc_id, course, exam_date, status, created_at FROM tasks ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def get_task(task_id: int) -> sqlite3.Row | None:
    with get_db() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()


def insert_conversation(session_id: str, message: str, category: str | None) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO conversations(session_id, message, category, created_at) VALUES(?,?,?,?)",
            (session_id, message, category, datetime.now().isoformat(timespec="seconds")),
        )


def get_recent_conversations(session_id: str, limit: int = 6) -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT message, category FROM conversations WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()


def insert_note(content: str, quadrant: int) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO notes(content, quadrant, created_at) VALUES(?,?,?)",
            (content, quadrant, datetime.now().isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def list_notes() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()


def toggle_note(note_id: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE notes SET done = 1 - done WHERE id=?", (note_id,))


def delete_note(note_id: int) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))


def get_daily_stats() -> dict:
    """今日回顾:今日对话数、今日新增待办、未完成待办、最近考试剩余天数。"""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_db() as conn:
        conv_today = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE created_at LIKE ?", (today + "%",)
        ).fetchone()[0]
        notes_today = conn.execute(
            "SELECT COUNT(*) FROM notes WHERE created_at LIKE ?", (today + "%",)
        ).fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM notes WHERE done=0").fetchone()[0]
        row = conn.execute(
            "SELECT course, exam_date FROM tasks WHERE exam_date IS NOT NULL "
            "AND exam_date >= ? ORDER BY exam_date ASC LIMIT 1",
            (today,),
        ).fetchone()
    days_left: int | None = None
    course: str = ""
    if row:
        course = row["course"]
        try:
            days_left = (
                datetime.strptime(row["exam_date"], "%Y-%m-%d").date()
                - datetime.now().date()
            ).days
        except ValueError:
            pass
    return {
        "conversations_today": conv_today,
        "notes_today": notes_today,
        "pending_notes": pending,
        "course": course,
        "days_left": days_left,
    }


def insert_feedback(task_id: int, point_index: int, vote: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO feedbacks(task_id, point_index, vote, created_at) VALUES(?,?,?,?)",
            (task_id, point_index, vote, datetime.now().isoformat(timespec="seconds")),
        )


def search_documents(query: str, limit: int = 5) -> list[dict]:
    """FTS5 全文检索:跨所有上传资料搜索,返回带高亮片段的命中。"""
    indexed_query = _index_text(query).strip()
    with get_db() as conn:
        rows = conn.execute(
            """SELECT doc_id, filename,
                      snippet(documents_fts, 2, '[', ']', '…', 20) AS snip
               FROM documents_fts WHERE content MATCH ? LIMIT ?""",
            (indexed_query, limit),
        ).fetchall()
    # 去掉字符级索引引入的单字间空格,恢复可读片段
    results = []
    for r in rows:
        snip = str(r["snip"]).replace(" ", "")
        results.append({"doc_id": r["doc_id"], "filename": r["filename"], "snippet": snip})
    return results
