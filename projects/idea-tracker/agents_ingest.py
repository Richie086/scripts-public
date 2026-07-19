"""Ingest AGENTS.md (and similar) files into Idea Forge as versioned entries."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_SEARCH_NAMES = ("AGENTS.md", "agents.md", "AGENT.md")


class AgentsIngestError(Exception):
    """User-facing ingest failure."""


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def discover_agents_files(roots: list[Path], *, max_files: int = 50) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        try:
            root = root.expanduser().resolve()
        except OSError:
            continue
        if not root.exists():
            continue
        # Prefer top-level AGENTS.md in each root
        for name in DEFAULT_SEARCH_NAMES:
            candidate = root / name
            if candidate.is_file():
                key = str(candidate.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(candidate.resolve())
        # Shallow scan one level of subdirs (e.g. projects/*)
        try:
            children = list(root.iterdir())
        except OSError:
            children = []
        for child in children:
            if not child.is_dir() or child.name.startswith("."):
                continue
            for name in DEFAULT_SEARCH_NAMES:
                candidate = child / name
                if candidate.is_file():
                    key = str(candidate.resolve())
                    if key not in seen:
                        seen.add(key)
                        found.append(candidate.resolve())
            if len(found) >= max_files:
                return found
    return found[:max_files]


def read_agents_file(path: Path) -> str:
    try:
        resolved = path.expanduser().resolve()
    except OSError as exc:
        raise AgentsIngestError(f"Cannot resolve path: {exc}") from exc
    if not resolved.is_file():
        raise AgentsIngestError(f"Not a file: {resolved}")
    lower = resolved.name.lower()
    ok_name = lower in {"agents.md", "agent.md"} or lower.endswith((".md", ".markdown", ".txt"))
    if not ok_name:
        raise AgentsIngestError("Only Markdown agent rule files are supported.")
    try:
        text = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentsIngestError(f"Cannot read file: {exc}") from exc
    if not text.strip():
        raise AgentsIngestError("File is empty.")
    if len(text) > 1_500_000:
        raise AgentsIngestError("File exceeds 1.5MB limit.")
    return text


def build_entry_payload(path: Path, text: str, *, stamped: str | None = None) -> dict:
    stamp = stamped or utcnow()
    name = path.name
    title = f"{name} · {stamp}"
    footer = (
        "\n\n---\n\n"
        f"## Ingest metadata\n\n"
        f"- source: `{path}`\n"
        f"- ingested_at: {stamp}\n"
        f"- content_sha256: `{content_hash(text)[:16]}…`\n"
    )
    body = text.rstrip() + footer
    tags = f"agents-md, ingest, {stamp[:10]}"
    return {
        "title": title,
        "category": "agent_instruction",
        "status": "active",
        "url": str(path),
        "tags": tags,
        "body": body,
        "stamp": stamp,
        "content_hash": content_hash(text),
        "source_path": str(path),
        "source_name": name,
    }


def ensure_ingest_tables(db: sqlite3.Connection) -> None:
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS ingest_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            source_path TEXT NOT NULL,
            source_name TEXT,
            content_hash TEXT NOT NULL,
            entry_id INTEGER,
            detail TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_ingest_events_created ON ingest_events(created_at DESC)"
    )
    db.commit()


def ensure_agents_collection(db: sqlite3.Connection, now: str) -> int:
    row = db.execute(
        "SELECT id FROM collections WHERE slug = ?",
        ("agents-md-history",),
    ).fetchone()
    if row:
        return int(row[0] if not isinstance(row, sqlite3.Row) else row["id"])
    cur = db.execute(
        """
        INSERT INTO collections (name, slug, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "AGENTS.md history",
            "agents-md-history",
            "Timestamped imports of AGENTS.md and related agent rule files",
            now,
            now,
        ),
    )
    db.commit()
    return int(cur.lastrowid)


def insert_entry(db: sqlite3.Connection, payload: dict) -> int:
    now = payload["stamp"]
    cur = db.execute(
        """
        INSERT INTO entries
            (title, category, status, url, tags, body, pinned,
             jira_id, bitbucket_id, github_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, NULL, NULL, NULL, ?, ?)
        """,
        (
            payload["title"],
            payload["category"],
            payload["status"],
            payload["url"],
            payload["tags"],
            payload["body"],
            now,
            now,
        ),
    )
    entry_id = int(cur.lastrowid)
    coll_id = ensure_agents_collection(db, now)
    db.execute(
        """
        INSERT OR IGNORE INTO collection_entries (collection_id, entry_id, created_at)
        VALUES (?, ?, ?)
        """,
        (coll_id, entry_id, now),
    )
    db.execute(
        """
        INSERT INTO ingest_events
            (kind, source_path, source_name, content_hash, entry_id, detail, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "agents_md",
            payload["source_path"],
            payload["source_name"],
            payload["content_hash"],
            entry_id,
            f"Created entry {entry_id} from {payload['source_name']}",
            now,
        ),
    )
    db.commit()
    return entry_id


def recent_ingests(db: sqlite3.Connection, *, limit: int = 20) -> list[dict]:
    ensure_ingest_tables(db)
    rows = db.execute(
        """
        SELECT * FROM ingest_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
