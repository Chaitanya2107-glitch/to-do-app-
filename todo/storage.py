"""SQLite storage layer for the todo app."""
import os
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(os.environ.get("TODO_DB", Path.home() / ".todo.db"))
PRIORITIES = ("low", "medium", "high")
_PRIORITY_ORDER = "CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END"


class TodoError(Exception):
    """Raised for user-facing validation problems."""


def connect(path=None):
    conn = sqlite3.connect(path or DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'medium',
            due TEXT,
            tag TEXT,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    return conn


def _validate(title=None, priority=None, due=None):
    if title is not None and not title.strip():
        raise TodoError("Title cannot be empty.")
    if priority is not None and priority not in PRIORITIES:
        raise TodoError(f"Priority must be one of: {', '.join(PRIORITIES)}.")
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            raise TodoError("Due date must be in YYYY-MM-DD format.")


def add_task(conn, title, priority="medium", due=None, tag=None):
    _validate(title, priority, due)
    cur = conn.execute(
        "INSERT INTO tasks (title, priority, due, tag) VALUES (?, ?, ?, ?)",
        (title.strip(), priority, due or None, tag or None),
    )
    conn.commit()
    return cur.lastrowid


def get_task(conn, task_id):
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise TodoError(f"No task with id {task_id}.")
    return row


def list_tasks(conn, status="all", tag=None, search=None, sort="id"):
    query, params = "SELECT * FROM tasks WHERE 1=1", []
    if status == "pending":
        query += " AND done = 0"
    elif status == "done":
        query += " AND done = 1"
    if tag:
        query += " AND tag = ?"
        params.append(tag)
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
    order = {
        "id": "id",
        "due": "due IS NULL, due, id",
        "priority": f"{_PRIORITY_ORDER}, id",
    }
    if sort not in order:
        raise TodoError("Sort must be one of: id, due, priority.")
    return conn.execute(f"{query} ORDER BY {order[sort]}", params).fetchall()


def set_done(conn, task_id, done=True):
    get_task(conn, task_id)
    conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(done), task_id))
    conn.commit()


def delete_task(conn, task_id):
    get_task(conn, task_id)
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()


def edit_task(conn, task_id, title=None, priority=None, due=None, tag=None):
    get_task(conn, task_id)
    _validate(title, priority, due)
    fields = {"title": title, "priority": priority, "due": due, "tag": tag}
    updates = {k: v for k, v in fields.items() if v is not None}
    for k in ("due", "tag"):
        if k in updates and not updates[k]:
            updates[k] = None  # empty string clears the field
    if not updates:
        raise TodoError("Nothing to edit. Pass --title, --priority, --due or --tag.")
    sets = ", ".join(f"{k} = ?" for k in updates)
    conn.execute(f"UPDATE tasks SET {sets} WHERE id = ?", (*updates.values(), task_id))
    conn.commit()
