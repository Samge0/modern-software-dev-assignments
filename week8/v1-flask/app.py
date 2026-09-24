"""Notes CRUD API — Flask + raw sqlite3 (Version 1).

Deliberately minimal: one file, stdlib + Flask only, to contrast with the
FastAPI (v2) and Django (v3) versions of the same app.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import Flask, g, jsonify, request

DB_PATH = Path(__file__).resolve().parent / "notes.db"

app = Flask(__name__)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def _validate(payload: dict) -> tuple[str, str] | None:
    title = str(payload.get("title", "")).strip()
    content = str(payload.get("content", "")).strip()
    if not title or len(title) > 200:
        return None
    if not content:
        return None
    return title, content


@app.get("/notes")
def list_notes():
    rows = get_db().execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/notes")
def create_note():
    data = request.get_json(silent=True) or {}
    valid = _validate(data)
    if valid is None:
        return jsonify({"error": "title (1-200 chars) and content (>=1 char) required"}), 400
    title, content = valid
    con = get_db()
    cur = con.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)", (title, content)
    )
    con.commit()
    row = con.execute("SELECT * FROM notes WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.get("/notes/<int:note_id>")
def get_note(note_id: int):
    row = get_db().execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        return jsonify({"error": "note not found"}), 404
    return jsonify(dict(row))


@app.put("/notes/<int:note_id>")
def update_note(note_id: int):
    data = request.get_json(silent=True) or {}
    valid = _validate(data)
    if valid is None:
        return jsonify({"error": "title and content required"}), 400
    con = get_db()
    exists = con.execute("SELECT 1 FROM notes WHERE id = ?", (note_id,)).fetchone()
    if exists is None:
        return jsonify({"error": "note not found"}), 404
    con.execute(
        "UPDATE notes SET title = ?, content = ? WHERE id = ?",
        (valid[0], valid[1], note_id),
    )
    con.commit()
    row = con.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return jsonify(dict(row))


@app.delete("/notes/<int:note_id>")
def delete_note(note_id: int):
    con = get_db()
    cur = con.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    con.commit()
    if cur.rowcount == 0:
        return jsonify({"error": "note not found"}), 404
    return "", 204


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(port=5001)
