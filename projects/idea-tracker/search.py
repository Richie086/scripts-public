"""SQLite FTS5 helpers for Idea Forge entry search."""

from __future__ import annotations

import re
import sqlite3


def ensure_fts(db: sqlite3.Connection) -> bool:
    """Create FTS table if possible. Returns True when FTS is available."""
    try:
        db.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                title,
                body,
                tags,
                url,
                attachment_names,
                tokenize = 'porter unicode61'
            )
            """
        )
        db.commit()
        return True
    except sqlite3.OperationalError:
        return False


def fts_available(db: sqlite3.Connection) -> bool:
    row = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entries_fts'"
    ).fetchone()
    return bool(row)


def build_match_query(raw: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9_./-]+", raw)
    parts = []
    for token in tokens[:20]:
        safe = token.replace('"', "")
        if not safe:
            continue
        parts.append(f'"{safe}"*')
    return " OR ".join(parts)


def attachment_names_for(db: sqlite3.Connection, entry_id: int) -> str:
    rows = db.execute(
        """
        SELECT original_name FROM attachments
        WHERE entry_id = ? AND deleted_at IS NULL
        """,
        (entry_id,),
    ).fetchall()
    return " ".join(r[0] if not isinstance(r, sqlite3.Row) else r["original_name"] for r in rows)


def fts_upsert(db: sqlite3.Connection, entry: dict) -> None:
    if not fts_available(db):
        return
    entry_id = entry["id"]
    names = attachment_names_for(db, entry_id)
    ext_ids = " ".join(
        x
        for x in (
            entry.get("jira_id"),
            entry.get("bitbucket_id"),
            entry.get("github_id"),
        )
        if x
    )
    tags = " ".join(p for p in (entry.get("tags") or "", ext_ids) if p)
    db.execute("DELETE FROM entries_fts WHERE rowid = ?", (entry_id,))
    db.execute(
        """
        INSERT INTO entries_fts(rowid, title, body, tags, url, attachment_names)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry_id,
            entry.get("title") or "",
            entry.get("body") or "",
            tags,
            entry.get("url") or "",
            names,
        ),
    )


def fts_delete(db: sqlite3.Connection, entry_id: int) -> None:
    if not fts_available(db):
        return
    db.execute("DELETE FROM entries_fts WHERE rowid = ?", (entry_id,))


def fts_rebuild(db: sqlite3.Connection) -> None:
    if not ensure_fts(db):
        return
    db.execute("DELETE FROM entries_fts")
    rows = db.execute("SELECT * FROM entries").fetchall()
    for row in rows:
        entry = dict(row)
        fts_upsert(db, entry)
    db.commit()


def search_entry_ids(
    db: sqlite3.Connection,
    q: str,
    *,
    category: str | None = None,
    status: str | None = None,
) -> list[int] | None:
    """
    Return matching entry ids via FTS, or None to signal caller should use LIKE fallback.
    """
    if not q or not fts_available(db):
        return None
    match = build_match_query(q)
    if not match:
        return None
    clauses = ["entries_fts MATCH ?"]
    params: list = [match]
    joins = "JOIN entries e ON e.id = entries_fts.rowid"
    if category:
        clauses.append("e.category = ?")
        params.append(category)
    if status and status != "all":
        clauses.append("e.status = ?")
        params.append(status)
    sql = f"""
        SELECT e.id
        FROM entries_fts
        {joins}
        WHERE {' AND '.join(clauses)}
        ORDER BY e.pinned DESC, rank, e.updated_at DESC, e.id DESC
    """
    try:
        rows = db.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return None
    return [r[0] if not isinstance(r, sqlite3.Row) else r["id"] for r in rows]
