#!/usr/bin/env python3
"""Idea Forge — personal idea tracker with local git hosting."""

from __future__ import annotations

import logging
import os
import re
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from markdown import markdown
from werkzeug.security import check_password_hash, generate_password_hash
import requests

import garden
import git_http
import media
import search as searchmod
import ai_providers
import fs_browser
import agents_ingest
from git_util import (
    GARDEN_SLUG,
    GitError,
    cat_file,
    commits_between,
    delete_bare_repo,
    diff_patch,
    diff_stat,
    ensure_dirs,
    ensure_garden,
    generate_token,
    git_available,
    hash_token,
    init_bare_repo,
    list_branches,
    list_tags,
    log_commits,
    ls_tree,
    merge_branches,
    merge_tree_check,
    seed_initial_commit,
    show_commit,
    slugify,
    ssh_fingerprint,
    validate_slug,
)

try:
    from git_ssh import make_key_lookup, start_ssh_server_thread

    ASYNCSSH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    ASYNCSSH_AVAILABLE = False

    def make_key_lookup(*_a, **_k):  # type: ignore[misc]
        raise RuntimeError("asyncssh is not installed")

    def start_ssh_server_thread(*_a, **_k):  # type: ignore[misc]
        raise RuntimeError("asyncssh is not installed")

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("SEEDBANK_DATA", APP_DIR / "data"))
DATABASE = DATA_DIR / "seedbank.db"
PATHS = ensure_dirs(DATA_DIR)
REPOS_DIR = PATHS["repos"]
GARDEN_DIR = PATHS["garden"]
SSH_DIR = PATHS["ssh"]
FILES_DIR = DATA_DIR / "files"
FILES_DIR.mkdir(parents=True, exist_ok=True)

PUBLIC_HOST = os.environ.get("SEEDBANK_PUBLIC_HOST") or os.environ.get(
    "SEEDBANK_HOST", "127.0.0.1"
)
if PUBLIC_HOST in {"0.0.0.0", "::", "[::]"}:
    PUBLIC_HOST = "127.0.0.1"
HTTP_PORT = int(os.environ.get("SEEDBANK_PORT", "5050"))
SSH_PORT = int(os.environ.get("SEEDBANK_SSH_PORT", "2222"))
SSH_ENABLED = os.environ.get("SEEDBANK_SSH", "1") == "1" and ASYNCSSH_AVAILABLE
ADMIN_PASSWORD = os.environ.get("SEEDBANK_ADMIN_PASSWORD", "seedbank")

CATEGORIES = [
    ("project", "Projects"),
    ("site", "Sites"),
    ("bookmark", "Bookmarks"),
    ("idea", "Ideas"),
    ("agent_instruction", "Agent Instructions"),
    ("agent", "Agents"),
    ("ai_rulebook", "AI Rulebook"),
    ("vscode_workspace", "VS Code Workspaces"),
]
CATEGORY_LABELS = dict(CATEGORIES)
CATEGORY_KEYS = {key for key, _ in CATEGORIES}

CATEGORY_TEMPLATES = {
    "project": (
        "## Problem\n\n\n"
        "## MVP\n\n- [ ] \n\n"
        "## Stack\n\n\n"
        "## Notes\n\n"
    ),
    "site": (
        "## Goal\n\n\n"
        "## Audience\n\n\n"
        "## Pages\n\n- \n\n"
        "## Design notes\n\n"
    ),
    "bookmark": (
        "## Why save this\n\n\n"
        "## Key takeaways\n\n- \n"
    ),
    "idea": (
        "## Spark\n\n\n"
        "## Next step\n\n- [ ] \n"
    ),
    "agent_instruction": (
        "## Role\n\n\n"
        "## Tools\n\n- \n\n"
        "## Constraints\n\n- \n\n"
        "## Output format\n\n"
    ),
    "agent": (
        "## Purpose\n\n\n"
        "## Instructions\n\n\n"
        "## Model notes\n\n\n"
        "## Related workspaces\n\n"
    ),
    "ai_rulebook": (
        "## Rule\n\n\n"
        "## Why\n\n\n"
        "## Examples\n\n```\n\n```\n\n"
        "## Exceptions\n\n"
    ),
    "vscode_workspace": (
        "## Path\n\n\n"
        "## Roots / folders\n\n- \n\n"
        "## Purpose\n\n"
    ),
}

STATUSES = [
    ("active", "Active"),
    ("someday", "Someday"),
    ("done", "Done"),
    ("archived", "Archived"),
]
STATUS_LABELS = dict(STATUSES)
STATUS_KEYS = {key for key, _ in STATUSES}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seedbank")

app = Flask(__name__)
app.secret_key = os.environ.get("SEEDBANK_SECRET", "ideaforge-dev-secret-change-me")


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


ORDERED_ITEM_RE = re.compile(r"^(\s*)(\d+)([.)])\s+(.*)$")
# Match malformed headings with missing whitespace after hashes, e.g. "##Title".
# Excludes headings that already start with "## " (or deeper), to avoid
# backtracking into multi-hash markers and rewriting valid headings.
HEADING_RE = re.compile(r"^(\s*)(#{1,6})([^\s#].*)$")
WELL_FORMED_HEADING_RE = re.compile(r"^\s*#{1,6}\s+\S")
ASSIST_HEADING_RE = re.compile(r"(?m)^# Assist Section \(AI-generated\)\s*$")
ASSIST_PREVIEW_MAX_CHARS = 20_000


def _normalize_ai_markdown(text: str) -> str:
    """Normalize AI-applied Markdown for readability.

    The goal is not to rewrite content semantics, but to keep common structures
    clean: heading spacing, ordered list numbering, and fenced code balance.
    """
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    # Pass 1: normalize heading marker spacing and keep code fences balanced.
    spaced: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fence_line = line.rstrip()
            if not in_fence and spaced and spaced[-1].strip():
                spaced.append("")
            spaced.append(fence_line)
            in_fence = not in_fence
            if not in_fence:
                spaced.append("")
            continue
        if in_fence:
            spaced.append(line.rstrip())
            continue
        heading = HEADING_RE.match(line)
        if heading:
            line = f"{heading.group(1)}{heading.group(2)} {heading.group(3).lstrip()}"
        spaced.append(line.rstrip())
    if in_fence:
        spaced.append("```")

    # Pass 2: renumber ordered lists sequentially (1,2,3...) outside code fences.
    renumbered: list[str] = []
    in_fence = False
    current_indent: int | None = None
    next_num = 1
    for line in spaced:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            renumbered.append(line)
            current_indent = None
            next_num = 1
            continue
        if in_fence:
            renumbered.append(line)
            continue
        item = ORDERED_ITEM_RE.match(line)
        if item:
            indent = len(item.group(1))
            marker = item.group(3)
            content = item.group(4)
            if current_indent != indent:
                current_indent = indent
                next_num = 1
            renumbered.append(f"{item.group(1)}{next_num}{marker} {content}")
            next_num += 1
            continue
        renumbered.append(line)
        current_indent = None
        next_num = 1

    # Pass 3: ensure headings have breathing room outside code fences.
    final_lines: list[str] = []
    in_fence = False
    for idx, line in enumerate(renumbered):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            final_lines.append(line)
            continue
        if in_fence:
            final_lines.append(line)
            continue
        if WELL_FORMED_HEADING_RE.match(line):
            if final_lines and final_lines[-1].strip():
                final_lines.append("")
            final_lines.append(line)
            nxt = renumbered[idx + 1] if idx + 1 < len(renumbered) else ""
            if nxt.strip():
                final_lines.append("")
            continue
        final_lines.append(line)

    # Collapse runaway blank lines while keeping intentional spacing.
    compact: list[str] = []
    blank_run = 0
    for line in final_lines:
        if not line.strip():
            blank_run += 1
            if blank_run <= 2:
                compact.append("")
            continue
        blank_run = 0
        compact.append(line)
    return "\n".join(compact).strip()


def _assist_disclaimer_block(payload: dict) -> str:
    action_label = payload.get("action_label") or "Assist"
    provider_label = payload.get("provider_label") or "AI provider"
    return (
        "# Assist Section (AI-generated)\n\n"
        "> This section was created using the Assist function and generated by AI, "
        "which can make mistakes. Verify details before using them.\n\n"
        f"## Assist Action: {action_label}\n"
        f"### Provider: {provider_label}"
    )


def _assist_markers(action: str) -> tuple[str, str]:
    key = (action or "assist").strip() or "assist"
    return (
        f"<!-- ASSIST_SECTION_START action={key} -->",
        f"<!-- ASSIST_SECTION_END action={key} -->",
    )


def _assist_section_block(payload: dict, draft: str) -> str:
    start, end = _assist_markers(payload.get("action") or "")
    return f"{start}\n{_assist_disclaimer_block(payload)}\n\n{draft.strip()}\n{end}".strip()


def _clamp_assist_preview(text: str, *, max_chars: int = ASSIST_PREVIEW_MAX_CHARS) -> str:
    trimmed = (text or "").strip()
    if len(trimmed) <= max_chars:
        return trimmed
    return trimmed[:max_chars].rstrip()


def _replace_existing_assist_section(
    existing: str, payload: dict, assist_section: str
) -> tuple[str, bool]:
    action = payload.get("action") or ""
    start_marker, end_marker = _assist_markers(action)
    marked_pattern = re.compile(
        re.escape(start_marker)
        + r".*?"
        + re.escape(end_marker)
        + r"(?:\n```(?:\n|$))*",
        re.DOTALL,
    )
    if marked_pattern.search(existing):
        return marked_pattern.sub(assist_section, existing, count=1), True

    # Legacy fallback for sections created before markers were added.
    action_label = payload.get("action_label") or "Assist"
    headings = list(ASSIST_HEADING_RE.finditer(existing))
    for idx, match in enumerate(headings):
        chunk_start = match.start()
        chunk_end = headings[idx + 1].start() if idx + 1 < len(headings) else len(existing)
        chunk = existing[chunk_start:chunk_end]
        if f"## Assist Action: {action_label}" in chunk:
            prefix = existing[:chunk_start].strip()
            suffix = existing[chunk_end:].strip()
            parts = [p for p in (prefix, assist_section, suffix) if p]
            return "\n\n".join(parts), True

    return existing, False


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            url TEXT,
            tags TEXT,
            body TEXT,
            pinned INTEGER NOT NULL DEFAULT 0,
            jira_id TEXT,
            bitbucket_id TEXT,
            github_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_entries_category ON entries(category);
        CREATE INDEX IF NOT EXISTS idx_entries_status ON entries(status);

        CREATE TABLE IF NOT EXISTS repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            default_branch TEXT NOT NULL DEFAULT 'main',
            entry_id INTEGER REFERENCES entries(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS access_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            prefix TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used_at TEXT
        );

        CREATE TABLE IF NOT EXISTS ssh_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            public_key TEXT NOT NULL UNIQUE,
            fingerprint TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS pull_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
            number INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            source_branch TEXT NOT NULL,
            target_branch TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            merged_at TEXT,
            UNIQUE(repo_id, number)
        );

        CREATE TABLE IF NOT EXISTS entry_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
            to_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            UNIQUE(from_id, to_id),
            CHECK(from_id != to_id)
        );

        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            media_kind TEXT NOT NULL,
            mime_type TEXT,
            size_bytes INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_attachments_entry ON attachments(entry_id);

        CREATE TABLE IF NOT EXISTS attachment_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attachment_id INTEGER NOT NULL REFERENCES attachments(id) ON DELETE CASCADE,
            entry_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            detail TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_attachment_events_entry ON attachment_events(entry_id);

        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS collection_entries (
            collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
            created_at TEXT NOT NULL,
            PRIMARY KEY (collection_id, entry_id)
        );

        CREATE TABLE IF NOT EXISTS ai_providers (
            provider_key TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            api_key_enc TEXT,
            base_url TEXT,
            model TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    row = db.execute(
        "SELECT value FROM settings WHERE key = 'admin_password_hash'"
    ).fetchone()
    if not row:
        db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("admin_password_hash", generate_password_hash(ADMIN_PASSWORD)),
        )
    db.commit()
    # Migrations for existing DBs
    entry_cols = {row[1] for row in db.execute("PRAGMA table_info(entries)").fetchall()}
    if "pinned" not in entry_cols:
        db.execute(
            "ALTER TABLE entries ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0"
        )
        db.commit()
    for col in ("jira_id", "bitbucket_id", "github_id"):
        if col not in entry_cols:
            db.execute(f"ALTER TABLE entries ADD COLUMN {col} TEXT")
            db.commit()
    entry_cols = {row[1] for row in db.execute("PRAGMA table_info(entries)").fetchall()}
    if "jira_id" in entry_cols:
        db.execute("CREATE INDEX IF NOT EXISTS idx_entries_jira ON entries(jira_id)")
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_entries_bitbucket ON entries(bitbucket_id)"
        )
        db.execute("CREATE INDEX IF NOT EXISTS idx_entries_github ON entries(github_id)")
        db.commit()
    # ai_providers table for DBs created before this feature
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_providers (
            provider_key TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            api_key_enc TEXT,
            base_url TEXT,
            model TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    for key in ai_providers.PROVIDERS:
        db.execute(
            """
            INSERT OR IGNORE INTO ai_providers
                (provider_key, enabled, api_key_enc, base_url, model, updated_at)
            VALUES (?, 0, NULL, NULL, NULL, ?)
            """,
            (key, utcnow()),
        )
    db.commit()
    ai_prov_cols = {row[1] for row in db.execute("PRAGMA table_info(ai_providers)").fetchall()}
    if "custom_headers" not in ai_prov_cols:
        db.execute("ALTER TABLE ai_providers ADD COLUMN custom_headers TEXT")
        db.commit()
    agents_ingest.ensure_ingest_tables(db)
    try:
        if searchmod.ensure_fts(db):
            # Rebuild if empty but entries exist
            fts_count = db.execute("SELECT COUNT(*) AS c FROM entries_fts").fetchone()[0]
            entry_count = db.execute("SELECT COUNT(*) AS c FROM entries").fetchone()[0]
            if entry_count and not fts_count:
                searchmod.fts_rebuild(db)
    except Exception as exc:  # noqa: BLE001
        logger.warning("FTS init failed: %s", exc)
    try:
        ensure_garden(REPOS_DIR, GARDEN_DIR)
    except GitError as exc:
        logger.warning("Garden init skipped: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Garden init failed: %s", exc)
    # Ensure garden appears in repos table for browsing
    if not db.execute("SELECT id FROM repos WHERE slug = ?", (GARDEN_SLUG,)).fetchone():
        db.execute(
            """
            INSERT INTO repos (name, slug, description, default_branch, entry_id, created_at)
            VALUES (?, ?, ?, 'main', NULL, ?)
            """,
            (
                "Idea Forge Garden",
                GARDEN_SLUG,
                "Auto-versioned entries (fetch-only)",
                utcnow(),
            ),
        )
        db.commit()


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def tags_to_str(tags: list[str]) -> str:
    return ", ".join(tags)


def row_to_entry(row: sqlite3.Row) -> dict:
    entry = dict(row)
    entry["tag_list"] = parse_tags(entry.get("tags"))
    entry["pinned"] = bool(entry.get("pinned"))
    entry["category_label"] = CATEGORY_LABELS.get(entry["category"], entry["category"])
    entry["status_label"] = STATUS_LABELS.get(entry["status"], entry["status"])
    entry["body_html"] = markdown(
        entry.get("body") or "",
        extensions=["fenced_code", "tables", "nl2br"],
    )
    entry["external_links"] = _external_links_for(entry)
    return entry


def _external_link(template: str | None, ext_id: str | None) -> str | None:
    if not ext_id:
        return None
    if not template:
        return None
    if "{id}" in template:
        return template.replace("{id}", ext_id)
    return template.rstrip("/") + "/" + ext_id


def _github_link(template: str | None, github_id: str | None) -> str | None:
    if not github_id:
        return None
    if "#" in github_id and "/" in github_id.split("#", 1)[0]:
        repo, num = github_id.rsplit("#", 1)
        if num.isdigit():
            return f"https://github.com/{repo}/issues/{num}"
    return _external_link(template, github_id)


def _external_links_for(entry: dict) -> list[dict]:
    links = []
    jira = entry.get("jira_id")
    if jira:
        links.append(
            {
                "kind": "jira",
                "label": f"Jira {jira}",
                "id": jira,
                "href": _external_link(_setting_get("ext_jira_url"), jira),
            }
        )
    bitbucket = entry.get("bitbucket_id")
    if bitbucket:
        links.append(
            {
                "kind": "bitbucket",
                "label": f"Bitbucket {bitbucket}",
                "id": bitbucket,
                "href": _external_link(_setting_get("ext_bitbucket_url"), bitbucket),
            }
        )
    github = entry.get("github_id")
    if github:
        links.append(
            {
                "kind": "github",
                "label": f"GitHub {github}",
                "id": github,
                "href": _github_link(_setting_get("ext_github_url"), github),
            }
        )
    return links


def _fs_roots() -> list:
    return fs_browser.parse_roots(
        _setting_get("fs_browser_roots"),
        os.environ.get("SEEDBANK_FS_ROOTS"),
    )


def fetch_entry(entry_id: int) -> dict | None:
    row = get_db().execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    return row_to_entry(row) if row else None


def form_values(source=None) -> dict:
    src = source or request.form
    return {
        "title": (src.get("title") or "").strip(),
        "category": (src.get("category") or "idea").strip(),
        "status": (src.get("status") or "active").strip(),
        "url": (src.get("url") or "").strip() or None,
        "tags": tags_to_str(parse_tags(src.get("tags"))),
        "body": (src.get("body") or "").strip() or None,
        "jira_id": (src.get("jira_id") or "").strip() or None,
        "bitbucket_id": (src.get("bitbucket_id") or "").strip() or None,
        "github_id": (src.get("github_id") or "").strip() or None,
    }


def validate(values: dict) -> list[str]:
    errors: list[str] = []
    if not values["title"]:
        errors.append("Title is required.")
    if values["category"] not in CATEGORY_KEYS:
        errors.append("Pick a valid category.")
    if values["status"] not in STATUS_KEYS:
        errors.append("Pick a valid status.")
    return errors


def clone_urls(slug: str) -> dict[str, str]:
    return {
        "http": f"http://{PUBLIC_HOST}:{HTTP_PORT}/git/{slug}.git",
        "ssh": f"ssh://git@{PUBLIC_HOST}:{SSH_PORT}/{slug}.git",
    }


def safe_next_url(candidate: str | None, fallback: str) -> str:
    """Only allow same-app relative redirects."""
    if not candidate:
        return fallback
    candidate = candidate.strip()
    if not candidate.startswith("/") or candidate.startswith("//"):
        return fallback
    if "\\" in candidate or "://" in candidate:
        return fallback
    return candidate


def require_repo(slug: str, *, allow_missing_bare: bool = False) -> dict:
    repo = fetch_repo(slug)
    if not repo:
        abort(404)
    if not allow_missing_bare and not repo["exists"]:
        abort(404)
    return repo


def fetch_repo(slug: str) -> dict | None:
    row = get_db().execute("SELECT * FROM repos WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    repo = dict(row)
    repo["clone"] = clone_urls(slug)
    repo["is_garden"] = slug == GARDEN_SLUG
    bare = REPOS_DIR / f"{slug}.git"
    repo["bare_path"] = bare
    repo["exists"] = bare.exists()
    open_prs = get_db().execute(
        "SELECT COUNT(*) AS c FROM pull_requests WHERE repo_id = ? AND status = 'open'",
        (repo["id"],),
    ).fetchone()["c"]
    repo["open_pr_count"] = open_prs
    return repo


def _fts_touch(entry_id: int) -> None:
    entry = fetch_entry(entry_id)
    if entry:
        searchmod.fts_upsert(get_db(), entry)
        get_db().commit()


def _fts_remove(entry_id: int) -> None:
    searchmod.fts_delete(get_db(), entry_id)
    get_db().commit()


def _setting_get(key: str, default: str | None = None) -> str | None:
    row = get_db().execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else default


def _setting_set(key: str, value: str) -> None:
    get_db().execute(
        """
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, value),
    )
    get_db().commit()


def _ai_provider_rows() -> list[dict]:
    rows = {
        r["provider_key"]: dict(r)
        for r in get_db().execute("SELECT * FROM ai_providers").fetchall()
    }
    out = []
    for key, meta in ai_providers.PROVIDERS.items():
        row = rows.get(key) or {
            "provider_key": key,
            "enabled": 0,
            "api_key_enc": None,
            "base_url": None,
            "model": None,
        }
        env_key = os.environ.get(meta["env_key"]) or ""
        has_key = bool(row.get("api_key_enc") or env_key)
        masked = ""
        if row.get("api_key_enc"):
            try:
                plain = ai_providers.decrypt_secret(app.secret_key, row["api_key_enc"])
                masked = ai_providers.mask_key(plain)
            except ai_providers.AIError:
                masked = "(invalid — re-save)"
        elif env_key:
            masked = ai_providers.mask_key(env_key) + " (env)"
        out.append(
            {
                **row,
                "label": meta["label"],
                "notes": meta.get("notes"),
                "default_base_url": meta["default_base_url"],
                "default_model": meta["default_model"],
                "env_key": meta["env_key"],
                "has_key": has_key,
                "masked_key": masked,
                "enabled": bool(row.get("enabled")),
            }
        )
    return out


def _resolve_ai_credentials(provider_key: str) -> tuple[str, str | None, str | None, str | None]:
    meta = ai_providers.PROVIDERS.get(provider_key)
    if not meta:
        raise ai_providers.AIError("Unknown provider.")
    row = get_db().execute(
        "SELECT * FROM ai_providers WHERE provider_key = ?", (provider_key,)
    ).fetchone()
    api_key = ""
    base_url = None
    model = None
    custom_headers = None
    if row:
        if row["api_key_enc"]:
            api_key = ai_providers.decrypt_secret(app.secret_key, row["api_key_enc"])
        base_url = row["base_url"] or None
        model = row["model"] or None
        custom_headers = row["custom_headers"] or None
    if not api_key:
        api_key = os.environ.get(meta["env_key"]) or ""
    return api_key, base_url, model, custom_headers


def _enabled_ai_providers() -> list[dict]:
    return [p for p in _ai_provider_rows() if p["enabled"] and p["has_key"]]


def _default_ai_provider() -> str | None:
    preferred = _setting_get("ai_default_provider")
    enabled = _enabled_ai_providers()
    keys = {p["provider_key"] for p in enabled}
    if preferred in keys:
        return preferred
    return enabled[0]["provider_key"] if enabled else None


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def verify_git_token(token: str | None) -> bool:
    if not token:
        return False
    row = get_db().execute(
        "SELECT id FROM access_tokens WHERE token_hash = ?",
        (hash_token(token),),
    ).fetchone()
    if not row:
        return False
    get_db().execute(
        "UPDATE access_tokens SET last_used_at = ? WHERE id = ?",
        (utcnow(), row["id"]),
    )
    get_db().commit()
    return True


def load_ssh_public_keys() -> list[str]:
    # Open a fresh connection — called from SSH thread outside request context
    conn = sqlite3.connect(DATABASE)
    try:
        rows = conn.execute("SELECT public_key FROM ssh_keys").fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


@app.context_processor
def inject_globals():
    return {
        "categories": CATEGORIES,
        "category_labels": CATEGORY_LABELS,
        "category_templates": CATEGORY_TEMPLATES,
        "statuses": STATUSES,
        "status_labels": STATUS_LABELS,
        "admin_logged_in": bool(session.get("admin")),
        "git_ok": git_available(),
        "ssh_enabled": SSH_ENABLED,
        "ssh_port": SSH_PORT,
        "garden_slug": GARDEN_SLUG,
    }


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    category = request.args.get("category", "").strip()
    status = request.args.get("status", "active").strip()
    q = request.args.get("q", "").strip()
    collection_slug = request.args.get("collection", "").strip()

    if status not in STATUS_KEYS and status != "all":
        status = "active"
    cat = category if category in CATEGORY_KEYS else None

    entries: list[dict] = []
    fts_ids = None
    if q:
        fts_ids = searchmod.search_entry_ids(
            get_db(),
            q,
            category=cat,
            status=status if status != "all" else None,
        )

    if fts_ids is not None:
        if fts_ids:
            placeholders = ",".join("?" for _ in fts_ids)
            rows = get_db().execute(
                f"SELECT * FROM entries WHERE id IN ({placeholders})",
                fts_ids,
            ).fetchall()
            by_id = {r["id"]: row_to_entry(r) for r in rows}
            entries = [by_id[i] for i in fts_ids if i in by_id]
        else:
            entries = []
    else:
        clauses: list[str] = []
        params: list[str] = []
        if cat:
            clauses.append("category = ?")
            params.append(cat)
        if status in STATUS_KEYS:
            clauses.append("status = ?")
            params.append(status)
        if q:
            like = f"%{q}%"
            clauses.append(
                "(title LIKE ? OR body LIKE ? OR tags LIKE ? OR url LIKE ?"
                " OR jira_id LIKE ? OR bitbucket_id LIKE ? OR github_id LIKE ?"
                " OR id IN (SELECT entry_id FROM attachments"
                " WHERE deleted_at IS NULL AND original_name LIKE ?))"
            )
            params.extend([like, like, like, like, like, like, like, like])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = get_db().execute(
            f"SELECT * FROM entries {where} ORDER BY pinned DESC, updated_at DESC, id DESC",
            params,
        ).fetchall()
        entries = [row_to_entry(row) for row in rows]

    current_collection = None
    if collection_slug:
        crow = get_db().execute(
            "SELECT * FROM collections WHERE slug = ?", (collection_slug,)
        ).fetchone()
        if crow:
            current_collection = dict(crow)
            member_ids = {
                r["entry_id"]
                for r in get_db().execute(
                    "SELECT entry_id FROM collection_entries WHERE collection_id = ?",
                    (crow["id"],),
                ).fetchall()
            }
            entries = [e for e in entries if e["id"] in member_ids]

    counts = {
        row["category"]: row["count"]
        for row in get_db().execute(
            """
            SELECT category, COUNT(*) AS count FROM entries
            WHERE status = 'active' GROUP BY category
            """
        ).fetchall()
    }
    collections = [
        dict(r)
        for r in get_db().execute(
            "SELECT * FROM collections ORDER BY name COLLATE NOCASE"
        ).fetchall()
    ]
    return render_template(
        "index.html",
        entries=entries,
        current_category=cat or "",
        current_status=status,
        q=q,
        counts=counts,
        total_active=sum(counts.values()),
        collections=collections,
        current_collection=current_collection,
    )


@app.route("/capture", methods=["POST"])
def quick_capture():
    title = (request.form.get("title") or "").strip()
    category = (request.form.get("category") or "idea").strip()
    if category not in CATEGORY_KEYS:
        category = "idea"
    if not title:
        flash("Capture needs a title.", "error")
        return redirect(url_for("index"))
    now = utcnow()
    cur = get_db().execute(
        """
        INSERT INTO entries
            (title, category, status, url, tags, body, pinned, created_at, updated_at)
        VALUES (?, ?, 'active', NULL, NULL, NULL, 0, ?, ?)
        """,
        (title, category, now, now),
    )
    get_db().commit()
    entry = fetch_entry(cur.lastrowid)
    searchmod.fts_upsert(get_db(), entry)
    get_db().commit()
    try:
        garden.sync_entry(
            repos_dir=REPOS_DIR, garden_dir=GARDEN_DIR, entry=entry, action="create"
        )
    except GitError as exc:
        logger.warning("Garden sync failed: %s", exc)
    flash("Captured.", "ok")
    return redirect(url_for("detail", entry_id=cur.lastrowid))


@app.route("/entry/<int:entry_id>/pin", methods=["POST"])
def toggle_pin(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    new_val = 0 if entry.get("pinned") else 1
    get_db().execute(
        "UPDATE entries SET pinned = ?, updated_at = ? WHERE id = ?",
        (new_val, utcnow(), entry_id),
    )
    get_db().commit()
    flash("Pinned." if new_val else "Unpinned.", "ok")
    nxt = request.form.get("next") or url_for("detail", entry_id=entry_id)
    return redirect(nxt)


@app.route("/new", methods=["GET", "POST"])
def create():
    category = request.args.get("category", "idea")
    if category not in CATEGORY_KEYS:
        category = "idea"
    values = {
        "title": "",
        "category": category,
        "status": "active",
        "url": "",
        "tags": "",
        "body": CATEGORY_TEMPLATES.get(category, ""),
        "jira_id": "",
        "bitbucket_id": "",
        "github_id": "",
    }

    if request.method == "POST":
        values = form_values()
        errors = validate(values)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "form.html",
                values=values,
                mode="create",
                fs_roots=_fs_roots(),
            )

        now = utcnow()
        cur = get_db().execute(
            """
            INSERT INTO entries
                (title, category, status, url, tags, body,
                 jira_id, bitbucket_id, github_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["title"],
                values["category"],
                values["status"],
                values["url"],
                values["tags"] or None,
                values["body"],
                values["jira_id"],
                values["bitbucket_id"],
                values["github_id"],
                now,
                now,
            ),
        )
        get_db().commit()
        entry = fetch_entry(cur.lastrowid)
        searchmod.fts_upsert(get_db(), entry)
        get_db().commit()
        try:
            garden.sync_entry(
                repos_dir=REPOS_DIR, garden_dir=GARDEN_DIR, entry=entry, action="create"
            )
        except GitError as exc:
            logger.warning("Garden sync failed: %s", exc)
        flash("Saved.", "ok")
        return redirect(url_for("detail", entry_id=cur.lastrowid))

    return render_template(
        "form.html",
        values=values,
        mode="create",
        fs_roots=_fs_roots(),
    )


def _related_entries(entry_id: int) -> list[dict]:
    rows = get_db().execute(
        """
        SELECT e.* FROM entry_links l
        JOIN entries e ON e.id = l.to_id
        WHERE l.from_id = ?
        ORDER BY e.title COLLATE NOCASE
        """,
        (entry_id,),
    ).fetchall()
    # Also include reverse links so relationships feel bidirectional
    reverse = get_db().execute(
        """
        SELECT e.* FROM entry_links l
        JOIN entries e ON e.id = l.from_id
        WHERE l.to_id = ?
        ORDER BY e.title COLLATE NOCASE
        """,
        (entry_id,),
    ).fetchall()
    seen = set()
    related = []
    for row in list(rows) + list(reverse):
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        related.append(row_to_entry(row))
    return related


def _log_attachment_event(
    attachment_id: int, entry_id: int, action: str, detail: str | None = None
) -> None:
    get_db().execute(
        """
        INSERT INTO attachment_events
            (attachment_id, entry_id, action, detail, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (attachment_id, entry_id, action, detail, utcnow()),
    )


def _fetch_attachment(entry_id: int, attachment_id: int, *, include_deleted: bool = False):
    if include_deleted:
        row = get_db().execute(
            "SELECT * FROM attachments WHERE id = ? AND entry_id = ?",
            (attachment_id, entry_id),
        ).fetchone()
    else:
        row = get_db().execute(
            """
            SELECT * FROM attachments
            WHERE id = ? AND entry_id = ? AND deleted_at IS NULL
            """,
            (attachment_id, entry_id),
        ).fetchone()
    return dict(row) if row else None


def _attachments_for_entry(entry_id: int) -> list[dict]:
    rows = get_db().execute(
        """
        SELECT * FROM attachments
        WHERE entry_id = ? AND deleted_at IS NULL
        ORDER BY media_kind, original_name COLLATE NOCASE
        """,
        (entry_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def _attachment_events(entry_id: int, limit: int = 50) -> list[dict]:
    rows = get_db().execute(
        """
        SELECT e.*, a.original_name, a.media_kind
        FROM attachment_events e
        JOIN attachments a ON a.id = e.attachment_id
        WHERE e.entry_id = ?
        ORDER BY e.id DESC
        LIMIT ?
        """,
        (entry_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


@app.route("/entry/<int:entry_id>")
def detail(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    history = []
    try:
        history = garden.entry_history(REPOS_DIR, GARDEN_DIR, entry)
    except GitError:
        history = []
    linked = get_db().execute(
        "SELECT * FROM repos WHERE entry_id = ?", (entry_id,)
    ).fetchone()
    candidates = [
        row_to_entry(r)
        for r in get_db().execute(
            """
            SELECT * FROM entries
            WHERE id != ?
            ORDER BY pinned DESC, updated_at DESC
            LIMIT 200
            """,
            (entry_id,),
        ).fetchall()
    ]
    attachments = _attachments_for_entry(entry_id)
    all_collections = [
        dict(r)
        for r in get_db().execute(
            "SELECT * FROM collections ORDER BY name COLLATE NOCASE"
        ).fetchall()
    ]
    ai_draft = None
    draft_key = f"ai_draft_{entry_id}"
    if draft_key in session:
        ai_draft = session.get(draft_key)
    return render_template(
        "detail.html",
        entry=entry,
        history=history,
        linked_repo=dict(linked) if linked else None,
        can_link_repo=entry["category"] in {"project", "idea", "vscode_workspace"},
        related=_related_entries(entry_id),
        link_candidates=candidates,
        attachments=attachments,
        attachments_by_kind=media.group_attachments(attachments),
        media_kinds=media.MEDIA_KINDS,
        media_kind_labels=media.MEDIA_KIND_LABELS,
        attachment_events=_attachment_events(entry_id),
        allowed_extensions=sorted(media.ALLOWED_EXTENSIONS),
        entry_collections=_collections_for_entry(entry_id),
        all_collections=all_collections,
        ai_actions=ai_providers.ACTIONS,
        ai_providers_enabled=_enabled_ai_providers(),
        ai_default_provider=_default_ai_provider(),
        ai_draft=ai_draft,
        ai_available=bool(_enabled_ai_providers()) or os.environ.get("SEEDBANK_AI_MOCK") == "1",
    )


@app.route("/entry/<int:entry_id>/attachments", methods=["POST"])
def upload_attachment(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Choose a file to upload.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    original = media.safe_filename(uploaded.filename)
    if not media.is_allowed(original):
        flash("File type not allowed.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    data = uploaded.read(media.MAX_UPLOAD_BYTES + 1)
    if len(data) > media.MAX_UPLOAD_BYTES:
        flash("File exceeds 25MB limit.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    stored = media.new_stored_name(original)
    path = media.store_path(FILES_DIR, entry_id, stored)
    path.write_bytes(data)
    kind = media.detect_kind(original)
    mime = media.guess_mime(original)
    now = utcnow()
    cur = get_db().execute(
        """
        INSERT INTO attachments
            (entry_id, original_name, stored_name, media_kind, mime_type,
             size_bytes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (entry_id, original, stored, kind, mime, len(data), now, now),
    )
    attachment_id = cur.lastrowid
    _log_attachment_event(attachment_id, entry_id, "added", original)
    get_db().execute(
        "UPDATE entries SET updated_at = ? WHERE id = ?",
        (now, entry_id),
    )
    get_db().commit()
    _fts_touch(entry_id)
    flash(f"Uploaded {original}.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/entry/<int:entry_id>/attachments/<int:attachment_id>/raw")
def attachment_raw(entry_id: int, attachment_id: int):
    att = _fetch_attachment(entry_id, attachment_id)
    if not att:
        abort(404)
    path = media.store_path(FILES_DIR, entry_id, att["stored_name"])
    if not path.exists():
        abort(404)
    return send_file(
        path,
        mimetype=att.get("mime_type") or "application/octet-stream",
        download_name=att["original_name"],
        as_attachment=request.args.get("download") == "1",
    )


@app.route(
    "/entry/<int:entry_id>/attachments/<int:attachment_id>/replace", methods=["POST"]
)
def replace_attachment(entry_id: int, attachment_id: int):
    att = _fetch_attachment(entry_id, attachment_id)
    if not att:
        abort(404)
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Choose a replacement file.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    original = media.safe_filename(uploaded.filename)
    if not media.is_allowed(original):
        flash("File type not allowed.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    data = uploaded.read(media.MAX_UPLOAD_BYTES + 1)
    if len(data) > media.MAX_UPLOAD_BYTES:
        flash("File exceeds 25MB limit.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    old_path = media.store_path(FILES_DIR, entry_id, att["stored_name"])
    stored = media.new_stored_name(original)
    path = media.store_path(FILES_DIR, entry_id, stored)
    path.write_bytes(data)
    if old_path.exists():
        old_path.unlink()
    now = utcnow()
    get_db().execute(
        """
        UPDATE attachments
        SET original_name = ?, stored_name = ?, media_kind = ?, mime_type = ?,
            size_bytes = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            original,
            stored,
            media.detect_kind(original),
            media.guess_mime(original),
            len(data),
            now,
            attachment_id,
        ),
    )
    _log_attachment_event(attachment_id, entry_id, "updated", original)
    get_db().execute(
        "UPDATE entries SET updated_at = ? WHERE id = ?", (now, entry_id)
    )
    get_db().commit()
    _fts_touch(entry_id)
    flash(f"Updated {original}.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route(
    "/entry/<int:entry_id>/attachments/<int:attachment_id>/delete", methods=["POST"]
)
def delete_attachment(entry_id: int, attachment_id: int):
    att = _fetch_attachment(entry_id, attachment_id)
    if not att:
        abort(404)
    now = utcnow()
    get_db().execute(
        "UPDATE attachments SET deleted_at = ?, updated_at = ? WHERE id = ?",
        (now, now, attachment_id),
    )
    _log_attachment_event(attachment_id, entry_id, "deleted", att["original_name"])
    get_db().execute(
        "UPDATE entries SET updated_at = ? WHERE id = ?", (now, entry_id)
    )
    get_db().commit()
    _fts_touch(entry_id)
    flash(f"Deleted {att['original_name']}.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route(
    "/entry/<int:entry_id>/attachments/<int:attachment_id>/insert", methods=["POST"]
)
def insert_attachment_into_notes(entry_id: int, attachment_id: int):
    entry = fetch_entry(entry_id)
    att = _fetch_attachment(entry_id, attachment_id)
    if not entry or not att:
        abort(404)
    raw_url = url_for(
        "attachment_raw", entry_id=entry_id, attachment_id=attachment_id, _external=False
    )
    text_content = None
    if att["media_kind"] in media.TEXT_KINDS:
        path = media.store_path(FILES_DIR, entry_id, att["stored_name"])
        if path.exists() and path.stat().st_size <= media.MAX_INSERT_CHARS * 4:
            try:
                text_content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text_content = None
    snippet = media.notes_snippet(
        kind=att["media_kind"],
        original_name=att["original_name"],
        raw_url=raw_url,
        text_content=text_content,
    )
    new_body = (entry.get("body") or "") + snippet
    now = utcnow()
    get_db().execute(
        "UPDATE entries SET body = ?, updated_at = ? WHERE id = ?",
        (new_body, now, entry_id),
    )
    get_db().commit()
    updated = fetch_entry(entry_id)
    searchmod.fts_upsert(get_db(), updated)
    get_db().commit()
    try:
        garden.sync_entry(
            repos_dir=REPOS_DIR, garden_dir=GARDEN_DIR, entry=updated, action="update"
        )
    except GitError as exc:
        logger.warning("Garden sync failed: %s", exc)
    flash(f"Added {att['original_name']} to notes.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/entry/<int:entry_id>/link", methods=["POST"])
def link_entry(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    try:
        to_id = int(request.form.get("to_id") or "0")
    except ValueError:
        to_id = 0
    other = fetch_entry(to_id)
    if not other or to_id == entry_id:
        flash("Pick a valid related entry.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    # Store undirected as ordered pair (min, max) to avoid duplicates both ways
    a, b = sorted((entry_id, to_id))
    try:
        get_db().execute(
            """
            INSERT OR IGNORE INTO entry_links (from_id, to_id, created_at)
            VALUES (?, ?, ?)
            """,
            (a, b, utcnow()),
        )
        get_db().commit()
        flash("Linked.", "ok")
    except sqlite3.IntegrityError:
        flash("Those entries are already linked.", "error")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/entry/<int:entry_id>/unlink/<int:other_id>", methods=["POST"])
def unlink_entry(entry_id: int, other_id: int):
    a, b = sorted((entry_id, other_id))
    get_db().execute(
        "DELETE FROM entry_links WHERE from_id = ? AND to_id = ?",
        (a, b),
    )
    get_db().commit()
    flash("Unlinked.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/export/entries.json")
def export_entries_json():
    rows = get_db().execute(
        "SELECT * FROM entries ORDER BY id ASC"
    ).fetchall()
    links = get_db().execute(
        "SELECT from_id, to_id, created_at FROM entry_links ORDER BY id ASC"
    ).fetchall()
    collections = [
        dict(r)
        for r in get_db().execute(
            "SELECT id, name, slug, description, created_at, updated_at FROM collections ORDER BY id"
        ).fetchall()
    ]
    membership = [
        dict(r)
        for r in get_db().execute(
            "SELECT collection_id, entry_id, created_at FROM collection_entries ORDER BY collection_id, entry_id"
        ).fetchall()
    ]
    payload = {
        "exported_at": utcnow(),
        "entries": [dict(r) for r in rows],
        "links": [dict(r) for r in links],
        "collections": collections,
        "collection_entries": membership,
    }
    return jsonify(payload)


def _collection_by_slug(slug: str) -> dict | None:
    row = get_db().execute(
        "SELECT * FROM collections WHERE slug = ?", (slug,)
    ).fetchone()
    return dict(row) if row else None


def _collections_for_entry(entry_id: int) -> list[dict]:
    rows = get_db().execute(
        """
        SELECT c.* FROM collections c
        JOIN collection_entries ce ON ce.collection_id = c.id
        WHERE ce.entry_id = ?
        ORDER BY c.name COLLATE NOCASE
        """,
        (entry_id,),
    ).fetchall()
    return [dict(r) for r in rows]


@app.route("/collections")
def collections_index():
    rows = get_db().execute(
        """
        SELECT c.*, COUNT(ce.entry_id) AS entry_count
        FROM collections c
        LEFT JOIN collection_entries ce ON ce.collection_id = c.id
        GROUP BY c.id
        ORDER BY c.name COLLATE NOCASE
        """
    ).fetchall()
    return render_template(
        "collections/index.html",
        collections=[dict(r) for r in rows],
    )


@app.route("/collections/new", methods=["GET", "POST"])
@require_admin
def collections_new():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        slug = (request.form.get("slug") or slugify(name)).strip() or slugify(name)
        if not name or not slugify(slug):
            flash("Name is required.", "error")
            return render_template(
                "collections/form.html",
                values={"name": name, "slug": slug, "description": description},
                mode="create",
            )
        slug = slugify(slug)
        now = utcnow()
        try:
            get_db().execute(
                """
                INSERT INTO collections (name, slug, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, slug, description or None, now, now),
            )
            get_db().commit()
        except sqlite3.IntegrityError:
            flash("That collection slug already exists.", "error")
            return render_template(
                "collections/form.html",
                values={"name": name, "slug": slug, "description": description},
                mode="create",
            )
        flash("Collection created.", "ok")
        return redirect(url_for("index", collection=slug))
    return render_template(
        "collections/form.html",
        values={"name": "", "slug": "", "description": ""},
        mode="create",
    )


@app.route("/entry/<int:entry_id>/collections", methods=["POST"])
def entry_add_collection(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    try:
        collection_id = int(request.form.get("collection_id") or "0")
    except ValueError:
        collection_id = 0
    row = get_db().execute(
        "SELECT id FROM collections WHERE id = ?", (collection_id,)
    ).fetchone()
    if not row:
        flash("Pick a valid collection.", "error")
        return redirect(url_for("detail", entry_id=entry_id))
    get_db().execute(
        """
        INSERT OR IGNORE INTO collection_entries (collection_id, entry_id, created_at)
        VALUES (?, ?, ?)
        """,
        (collection_id, entry_id, utcnow()),
    )
    get_db().commit()
    flash("Added to collection.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/entry/<int:entry_id>/collections/<int:collection_id>/remove", methods=["POST"])
def entry_remove_collection(entry_id: int, collection_id: int):
    get_db().execute(
        "DELETE FROM collection_entries WHERE collection_id = ? AND entry_id = ?",
        (collection_id, entry_id),
    )
    get_db().commit()
    flash("Removed from collection.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/import", methods=["GET", "POST"])
@require_admin
def import_entries():
    if request.method == "GET":
        return render_template("import.html", preview=None)

    mode = (request.form.get("mode") or "dry-run").strip()
    raw = ""
    uploaded = request.files.get("file")
    if uploaded and uploaded.filename:
        raw = uploaded.read().decode("utf-8", errors="replace")
    else:
        raw = request.form.get("json_text") or ""
    try:
        import json

        payload = json.loads(raw)
    except Exception:  # noqa: BLE001
        flash("Invalid JSON.", "error")
        return render_template("import.html", preview=None)

    entries_in = payload.get("entries") or []
    links_in = payload.get("links") or []
    collections_in = payload.get("collections") or []
    membership_in = payload.get("collection_entries") or []
    if not isinstance(entries_in, list):
        flash("entries must be a list.", "error")
        return render_template("import.html", preview=None)

    preview = {
        "entries": len(entries_in),
        "links": len(links_in),
        "collections": len(collections_in),
        "membership": len(membership_in),
        "mode": mode,
        "sample_titles": [e.get("title", "") for e in entries_in[:5] if isinstance(e, dict)],
    }
    if mode != "apply":
        return render_template("import.html", preview=preview, raw_json=raw)

    # Apply: insert entries without forcing ids (avoid collisions)
    id_map: dict[int, int] = {}
    now = utcnow()
    for item in entries_in:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        category = item.get("category") if item.get("category") in CATEGORY_KEYS else "idea"
        status = item.get("status") if item.get("status") in STATUS_KEYS else "active"
        cur = get_db().execute(
            """
            INSERT INTO entries
                (title, category, status, url, tags, body, pinned,
                 jira_id, bitbucket_id, github_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(item["title"]),
                category,
                status,
                item.get("url"),
                item.get("tags"),
                item.get("body"),
                1 if item.get("pinned") else 0,
                item.get("jira_id"),
                item.get("bitbucket_id"),
                item.get("github_id"),
                item.get("created_at") or now,
                item.get("updated_at") or now,
            ),
        )
        new_id = cur.lastrowid
        if item.get("id") is not None:
            try:
                id_map[int(item["id"])] = new_id
            except (TypeError, ValueError):
                pass
        searchmod.fts_upsert(get_db(), fetch_entry(new_id))

    for link in links_in:
        if not isinstance(link, dict):
            continue
        try:
            a = id_map.get(int(link["from_id"]))
            b = id_map.get(int(link["to_id"]))
        except (KeyError, TypeError, ValueError):
            continue
        if not a or not b or a == b:
            continue
        x, y = sorted((a, b))
        get_db().execute(
            """
            INSERT OR IGNORE INTO entry_links (from_id, to_id, created_at)
            VALUES (?, ?, ?)
            """,
            (x, y, link.get("created_at") or now),
        )

    coll_map: dict[int, int] = {}
    for coll in collections_in:
        if not isinstance(coll, dict) or not coll.get("name"):
            continue
        cslug = slugify(coll.get("slug") or coll["name"])
        existing = get_db().execute(
            "SELECT id FROM collections WHERE slug = ?", (cslug,)
        ).fetchone()
        if existing:
            new_cid = existing["id"]
        else:
            cur = get_db().execute(
                """
                INSERT INTO collections (name, slug, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    coll["name"],
                    cslug,
                    coll.get("description"),
                    coll.get("created_at") or now,
                    coll.get("updated_at") or now,
                ),
            )
            new_cid = cur.lastrowid
        if coll.get("id") is not None:
            try:
                coll_map[int(coll["id"])] = new_cid
            except (TypeError, ValueError):
                pass

    for mem in membership_in:
        if not isinstance(mem, dict):
            continue
        try:
            cid = coll_map.get(int(mem["collection_id"]))
            eid = id_map.get(int(mem["entry_id"]))
        except (KeyError, TypeError, ValueError):
            continue
        if not cid or not eid:
            continue
        get_db().execute(
            """
            INSERT OR IGNORE INTO collection_entries (collection_id, entry_id, created_at)
            VALUES (?, ?, ?)
            """,
            (cid, eid, mem.get("created_at") or now),
        )

    get_db().commit()
    flash(
        f"Imported {len(id_map)} entries, {len(coll_map)} collections.",
        "ok",
    )
    return redirect(url_for("index"))


@app.route("/entry/<int:entry_id>/edit", methods=["GET", "POST"])
def edit(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)

    if request.method == "POST":
        values = form_values()
        errors = validate(values)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "form.html",
                values=values,
                mode="edit",
                entry_id=entry_id,
                fs_roots=_fs_roots(),
            )
        get_db().execute(
            """
            UPDATE entries
            SET title = ?, category = ?, status = ?, url = ?, tags = ?,
                body = ?, jira_id = ?, bitbucket_id = ?, github_id = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                values["title"],
                values["category"],
                values["status"],
                values["url"],
                values["tags"] or None,
                values["body"],
                values["jira_id"],
                values["bitbucket_id"],
                values["github_id"],
                utcnow(),
                entry_id,
            ),
        )
        get_db().commit()
        updated = fetch_entry(entry_id)
        searchmod.fts_upsert(get_db(), updated)
        get_db().commit()
        try:
            garden.sync_entry(
                repos_dir=REPOS_DIR, garden_dir=GARDEN_DIR, entry=updated, action="update"
            )
        except GitError as exc:
            logger.warning("Garden sync failed: %s", exc)
        flash("Updated.", "ok")
        return redirect(url_for("detail", entry_id=entry_id))

    values = {
        "title": entry["title"],
        "category": entry["category"],
        "status": entry["status"],
        "url": entry["url"] or "",
        "tags": entry["tags"] or "",
        "body": entry["body"] or "",
        "jira_id": entry.get("jira_id") or "",
        "bitbucket_id": entry.get("bitbucket_id") or "",
        "github_id": entry.get("github_id") or "",
    }
    return render_template(
        "form.html",
        values=values,
        mode="edit",
        entry_id=entry_id,
        fs_roots=_fs_roots(),
    )


@app.route("/entry/<int:entry_id>/delete", methods=["POST"])
def delete(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    try:
        garden.sync_entry(
            repos_dir=REPOS_DIR, garden_dir=GARDEN_DIR, entry=entry, action="delete"
        )
    except GitError as exc:
        logger.warning("Garden sync failed: %s", exc)
    get_db().execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    get_db().commit()
    searchmod.fts_delete(get_db(), entry_id)
    get_db().commit()
    flash(f'Deleted “{entry["title"]}”.', "ok")
    return redirect(url_for("index", category=entry["category"]))


@app.route("/entry/<int:entry_id>/create-repo", methods=["POST"])
@require_admin
def create_repo_from_entry(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    existing = get_db().execute(
        "SELECT slug FROM repos WHERE entry_id = ?", (entry_id,)
    ).fetchone()
    if existing:
        return redirect(url_for("repo_home", slug=existing["slug"]))
    slug = slugify(entry["title"])
    if not validate_slug(slug) or get_db().execute(
        "SELECT id FROM repos WHERE slug = ?", (slug,)
    ).fetchone():
        slug = f"{slug}-{entry_id}"
    return _create_repo_record(
        name=entry["title"],
        slug=slug,
        description=f"Linked from entry #{entry_id}",
        entry_id=entry_id,
    )


# ---------------------------------------------------------------------------
# Git HTTP
# ---------------------------------------------------------------------------


@app.route("/git/<slug>.git", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/git/<slug>.git/<path:path>", methods=["GET", "POST"])
def git_smart_http(slug: str, path: str):
    if not git_available():
        return Response("git not installed\n", status=500, mimetype="text/plain")
    token = git_http.extract_token(request)
    if not verify_git_token(token):
        return Response(
            "Unauthorized\n",
            status=401,
            mimetype="text/plain",
            headers={"WWW-Authenticate": 'Basic realm="Idea Forge Git"'},
        )
    allow_push = slug != GARDEN_SLUG
    # Also deny receive-pack service advertisement for garden
    if not allow_push and "git-receive-pack" in (path + request.query_string.decode()):
        return Response("Push denied\n", status=403, mimetype="text/plain")
    try:
        return git_http.run_http_backend(
            repos_dir=REPOS_DIR,
            slug=slug,
            path_info=path,
            req=request,
            allow_push=allow_push,
        )
    except GitError as exc:
        return Response(str(exc) + "\n", status=500, mimetype="text/plain")


# ---------------------------------------------------------------------------
# Repos + file browser + PRs
# ---------------------------------------------------------------------------


def _create_repo_record(
    *,
    name: str,
    slug: str,
    description: str = "",
    entry_id: int | None = None,
):
    if not validate_slug(slug):
        flash("Invalid slug. Use lowercase letters, numbers, and dashes.", "error")
        return redirect(url_for("repos_index"))
    if get_db().execute("SELECT id FROM repos WHERE slug = ?", (slug,)).fetchone():
        flash("A repository with that slug already exists.", "error")
        return redirect(url_for("repos_index"))
    if not git_available():
        flash("git is not installed on this system.", "error")
        return redirect(url_for("repos_index"))
    bare = REPOS_DIR / f"{slug}.git"
    try:
        init_bare_repo(bare, default_branch="main")
        seed_initial_commit(
            bare,
            default_branch="main",
            readme=f"# {name}\n\n{description}\n",
        )
    except GitError as exc:
        if bare.exists():
            delete_bare_repo(bare)
        flash(f"Failed to create repository: {exc}", "error")
        return redirect(url_for("repos_index"))

    get_db().execute(
        """
        INSERT INTO repos (name, slug, description, default_branch, entry_id, created_at)
        VALUES (?, ?, ?, 'main', ?, ?)
        """,
        (name, slug, description or None, entry_id, utcnow()),
    )
    get_db().commit()
    flash(f"Repository “{name}” created.", "ok")
    return redirect(url_for("repo_home", slug=slug))


@app.route("/repos")
def repos_index():
    rows = get_db().execute(
        "SELECT * FROM repos ORDER BY CASE WHEN slug = ? THEN 0 ELSE 1 END, name COLLATE NOCASE",
        (GARDEN_SLUG,),
    ).fetchall()
    repos = []
    for row in rows:
        repo = fetch_repo(row["slug"])
        if not repo:
            continue
        # Hide orphaned DB rows whose bare repo was deleted (keep garden visible).
        if repo["exists"] or repo["is_garden"]:
            repos.append(repo)
    return render_template("repos/index.html", repos=repos)


@app.route("/repos/new", methods=["GET", "POST"])
@require_admin
def repos_new():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        slug = (request.form.get("slug") or slugify(name)).strip()
        description = (request.form.get("description") or "").strip()
        if not name:
            flash("Name is required.", "error")
            return render_template(
                "repos/new.html",
                values={"name": name, "slug": slug, "description": description},
            )
        return _create_repo_record(name=name, slug=slug, description=description)
    return render_template(
        "repos/new.html", values={"name": "", "slug": "", "description": ""}
    )


@app.route("/repos/<slug>")
def repo_home(slug: str):
    repo = require_repo(slug)
    bare = repo["bare_path"]
    branch = repo["default_branch"]
    try:
        commits = log_commits(bare, branch, limit=10)
        tree = ls_tree(bare, branch)
    except GitError:
        commits, tree = [], []
    return render_template(
        "repos/home.html",
        repo=repo,
        commits=commits,
        tree=tree,
        ref=branch,
        tab="files",
    )


@app.route("/repos/<slug>/tree/<ref>/")
@app.route("/repos/<slug>/tree/<ref>/<path:path>")
def repo_tree(slug: str, ref: str, path: str = ""):
    repo = require_repo(slug)
    bare = repo["bare_path"]
    try:
        tree = ls_tree(bare, ref, path)
        branches = list_branches(bare)
        tags = list_tags(bare)
    except GitError as exc:
        flash(str(exc), "error")
        return redirect(url_for("repo_home", slug=slug))
    crumbs = []
    if path:
        parts = path.split("/")
        acc = []
        for part in parts:
            acc.append(part)
            crumbs.append({"name": part, "path": "/".join(acc)})
    return render_template(
        "repos/tree.html",
        repo=repo,
        tree=tree,
        ref=ref,
        path=path,
        crumbs=crumbs,
        branches=branches,
        tags=tags,
        tab="files",
    )


@app.route("/repos/<slug>/blob/<ref>/<path:path>")
def repo_blob(slug: str, ref: str, path: str):
    repo = require_repo(slug)
    bare = repo["bare_path"]
    try:
        blob = cat_file(bare, ref, path)
        branches = list_branches(bare)
        tags = list_tags(bare)
    except GitError as exc:
        flash(str(exc), "error")
        return redirect(url_for("repo_home", slug=slug))
    html = None
    if blob.get("text") and path.lower().endswith((".md", ".markdown")):
        html = markdown(blob["content"] or "", extensions=["fenced_code", "tables", "nl2br"])
    crumbs = []
    parts = path.split("/")
    acc = []
    for part in parts:
        acc.append(part)
        crumbs.append({"name": part, "path": "/".join(acc)})
    return render_template(
        "repos/blob.html",
        repo=repo,
        blob=blob,
        ref=ref,
        path=path,
        crumbs=crumbs,
        branches=branches,
        tags=tags,
        rendered_html=html,
        tab="files",
    )


@app.route("/repos/<slug>/commits/<ref>")
def repo_commits(slug: str, ref: str):
    repo = require_repo(slug)
    try:
        commits = log_commits(repo["bare_path"], ref, limit=100)
    except GitError as exc:
        flash(str(exc), "error")
        return redirect(url_for("repo_home", slug=slug))
    return render_template(
        "repos/commits.html", repo=repo, commits=commits, ref=ref, tab="files"
    )


@app.route("/repos/<slug>/commit/<sha>")
def repo_commit(slug: str, sha: str):
    repo = require_repo(slug)
    try:
        commit = show_commit(repo["bare_path"], sha)
    except GitError as exc:
        flash(str(exc), "error")
        return redirect(url_for("repo_home", slug=slug))
    return render_template("repos/commit.html", repo=repo, commit=commit, tab="files")


@app.route("/repos/<slug>/pulls")
def repo_pulls(slug: str):
    repo = require_repo(slug)
    if repo["is_garden"]:
        flash("Pull requests are disabled for the garden repository.", "error")
        return redirect(url_for("repo_home", slug=slug))
    status = request.args.get("status", "open")
    if status not in {"open", "merged", "closed", "all"}:
        status = "open"
    if status == "all":
        rows = get_db().execute(
            "SELECT * FROM pull_requests WHERE repo_id = ? ORDER BY number DESC",
            (repo["id"],),
        ).fetchall()
    else:
        rows = get_db().execute(
            """
            SELECT * FROM pull_requests
            WHERE repo_id = ? AND status = ?
            ORDER BY number DESC
            """,
            (repo["id"], status),
        ).fetchall()
    return render_template(
        "repos/pulls.html",
        repo=repo,
        pulls=[dict(r) for r in rows],
        status=status,
        tab="pulls",
    )


@app.route("/repos/<slug>/pulls/new", methods=["GET", "POST"])
@require_admin
def repo_pull_new(slug: str):
    repo = require_repo(slug)
    if repo["is_garden"]:
        abort(404)
    bare = repo["bare_path"]
    branches = list_branches(bare)
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        source = (request.form.get("source_branch") or "").strip()
        target = (request.form.get("target_branch") or "").strip()
        if not title or source not in branches or target not in branches or source == target:
            flash("Provide a title and two different existing branches.", "error")
            return render_template(
                "repos/pull_new.html",
                repo=repo,
                branches=branches,
                values={
                    "title": title,
                    "body": body,
                    "source_branch": source,
                    "target_branch": target,
                },
                tab="pulls",
            )
        last = get_db().execute(
            "SELECT COALESCE(MAX(number), 0) AS n FROM pull_requests WHERE repo_id = ?",
            (repo["id"],),
        ).fetchone()["n"]
        number = last + 1
        now = utcnow()
        get_db().execute(
            """
            INSERT INTO pull_requests
                (repo_id, number, title, body, source_branch, target_branch,
                 status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?)
            """,
            (repo["id"], number, title, body or None, source, target, now, now),
        )
        get_db().commit()
        flash(f"Opened pull request #{number}.", "ok")
        return redirect(url_for("repo_pull_detail", slug=slug, number=number))
    return render_template(
        "repos/pull_new.html",
        repo=repo,
        branches=branches,
        values={
            "title": "",
            "body": "",
            "source_branch": "",
            "target_branch": repo["default_branch"],
        },
        tab="pulls",
    )


@app.route("/repos/<slug>/pulls/<int:number>")
def repo_pull_detail(slug: str, number: int):
    repo = require_repo(slug)
    row = get_db().execute(
        "SELECT * FROM pull_requests WHERE repo_id = ? AND number = ?",
        (repo["id"], number),
    ).fetchone()
    if not row:
        abort(404)
    pull = dict(row)
    bare = repo["bare_path"]
    commits, stat, patch, can_merge, merge_msg = [], "", "", False, ""
    try:
        commits = commits_between(bare, pull["target_branch"], pull["source_branch"])
        stat = diff_stat(bare, pull["target_branch"], pull["source_branch"])
        patch = diff_patch(bare, pull["target_branch"], pull["source_branch"])
        if pull["status"] == "open":
            can_merge, merge_msg = merge_tree_check(
                bare, pull["target_branch"], pull["source_branch"]
            )
    except GitError as exc:
        merge_msg = str(exc)
    return render_template(
        "repos/pull_detail.html",
        repo=repo,
        pull=pull,
        commits=commits,
        diff_stat=stat,
        diff_patch=patch,
        can_merge=can_merge,
        merge_msg=merge_msg,
        tab="pulls",
    )


@app.route("/repos/<slug>/pulls/<int:number>/merge", methods=["POST"])
@require_admin
def repo_pull_merge(slug: str, number: int):
    repo = require_repo(slug)
    if repo["is_garden"]:
        abort(404)
    row = get_db().execute(
        "SELECT * FROM pull_requests WHERE repo_id = ? AND number = ?",
        (repo["id"], number),
    ).fetchone()
    if not row or row["status"] != "open":
        abort(404)
    pull = dict(row)
    can_merge, merge_msg = merge_tree_check(
        repo["bare_path"], pull["target_branch"], pull["source_branch"]
    )
    if not can_merge:
        flash(f"Merge blocked: {merge_msg}", "error")
        return redirect(url_for("repo_pull_detail", slug=slug, number=number))
    try:
        merge_branches(
            repo["bare_path"],
            target=pull["target_branch"],
            source=pull["source_branch"],
            message=f"Merge pull request #{number} from {pull['source_branch']}\n\n{pull['title']}",
        )
    except GitError as exc:
        flash(f"Merge failed: {exc}", "error")
        return redirect(url_for("repo_pull_detail", slug=slug, number=number))
    now = utcnow()
    get_db().execute(
        """
        UPDATE pull_requests
        SET status = 'merged', merged_at = ?, updated_at = ?
        WHERE id = ?
        """,
        (now, now, pull["id"]),
    )
    get_db().commit()
    flash(f"Merged pull request #{number}.", "ok")
    return redirect(url_for("repo_pull_detail", slug=slug, number=number))


@app.route("/repos/<slug>/pulls/<int:number>/close", methods=["POST"])
@require_admin
def repo_pull_close(slug: str, number: int):
    repo = require_repo(slug)
    if not repo:
        abort(404)
    row = get_db().execute(
        "SELECT * FROM pull_requests WHERE repo_id = ? AND number = ?",
        (repo["id"], number),
    ).fetchone()
    if not row or row["status"] != "open":
        abort(404)
    get_db().execute(
        "UPDATE pull_requests SET status = 'closed', updated_at = ? WHERE id = ?",
        (utcnow(), row["id"]),
    )
    get_db().commit()
    flash(f"Closed pull request #{number}.", "ok")
    return redirect(url_for("repo_pull_detail", slug=slug, number=number))


@app.route("/repos/<slug>/delete", methods=["POST"])
@require_admin
def repo_delete(slug: str):
    if slug == GARDEN_SLUG:
        flash("Cannot delete the garden repository.", "error")
        return redirect(url_for("repos_index"))
    repo = fetch_repo(slug)
    if not repo:
        abort(404)
    bare = REPOS_DIR / f"{slug}.git"
    delete_bare_repo(bare)
    get_db().execute("DELETE FROM repos WHERE id = ?", (repo["id"],))
    get_db().commit()
    flash(f'Deleted repository “{repo["name"]}”.', "ok")
    return redirect(url_for("repos_index"))


# ---------------------------------------------------------------------------
# Settings + Admin
# ---------------------------------------------------------------------------


@app.route("/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password") or ""
        row = get_db().execute(
            "SELECT value FROM settings WHERE key = 'admin_password_hash'"
        ).fetchone()
        if row and check_password_hash(row["value"], password):
            session["admin"] = True
            flash("Signed in.", "ok")
            nxt = safe_next_url(
                request.args.get("next"), url_for("admin_panel")
            )
            return redirect(nxt)
        flash("Incorrect password.", "error")
    return render_template("admin/login.html")


@app.route("/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    flash("Signed out.", "ok")
    return redirect(url_for("index"))


@app.route("/admin")
@require_admin
def admin_panel():
    stats = {
        "entries": get_db().execute("SELECT COUNT(*) AS c FROM entries").fetchone()["c"],
        "repos": get_db().execute("SELECT COUNT(*) AS c FROM repos").fetchone()["c"],
        "tokens": get_db().execute("SELECT COUNT(*) AS c FROM access_tokens").fetchone()["c"],
        "ssh_keys": get_db().execute("SELECT COUNT(*) AS c FROM ssh_keys").fetchone()["c"],
        "open_prs": get_db().execute(
            "SELECT COUNT(*) AS c FROM pull_requests WHERE status = 'open'"
        ).fetchone()["c"],
        "git_ok": git_available(),
        "ssh_enabled": SSH_ENABLED,
        "ssh_port": SSH_PORT,
        "data_dir": str(DATA_DIR),
        "repos_dir": str(REPOS_DIR),
    }
    return render_template("admin/panel.html", stats=stats)


@app.route("/admin/password", methods=["POST"])
@require_admin
def admin_change_password():
    current = request.form.get("current_password") or ""
    new = request.form.get("new_password") or ""
    confirm = request.form.get("confirm_password") or ""
    row = get_db().execute(
        "SELECT value FROM settings WHERE key = 'admin_password_hash'"
    ).fetchone()
    if not row or not check_password_hash(row["value"], current):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("admin_panel"))
    if len(new) < 8 or new != confirm:
        flash("New password must be at least 8 characters and match confirmation.", "error")
        return redirect(url_for("admin_panel"))
    get_db().execute(
        "UPDATE settings SET value = ? WHERE key = 'admin_password_hash'",
        (generate_password_hash(new),),
    )
    get_db().commit()
    flash("Admin password updated.", "ok")
    return redirect(url_for("admin_panel"))


@app.route("/settings")
@require_admin
def settings():
    tokens = [
        dict(r)
        for r in get_db().execute(
            "SELECT id, name, prefix, created_at, last_used_at FROM access_tokens ORDER BY id DESC"
        ).fetchall()
    ]
    keys = [
        dict(r)
        for r in get_db().execute(
            "SELECT id, name, fingerprint, created_at FROM ssh_keys ORDER BY id DESC"
        ).fetchall()
    ]
    return render_template(
        "settings.html",
        tokens=tokens,
        keys=keys,
        new_token=session.pop("new_token", None),
        ai_providers=_ai_provider_rows(),
        ai_default_provider=_setting_get("ai_default_provider") or "",
        ai_mock=os.environ.get("SEEDBANK_AI_MOCK") == "1",
        ext_jira_url=_setting_get("ext_jira_url") or "",
        ext_bitbucket_url=_setting_get("ext_bitbucket_url") or "",
        ext_github_url=_setting_get("ext_github_url") or "",
        fs_browser_roots=_setting_get("fs_browser_roots") or "",
        fs_roots_resolved=[str(p) for p in _fs_roots()],
    )


@app.route("/settings/ai/<provider_key>", methods=["POST"])
@require_admin
def settings_save_ai_provider(provider_key: str):
    if provider_key not in ai_providers.PROVIDERS:
        abort(404)
    enabled = 1 if request.form.get("enabled") == "1" else 0
    base_url = (request.form.get("base_url") or "").strip() or None
    model = (request.form.get("model") or "").strip() or None
    api_key_raw = (request.form.get("api_key") or "").strip()
    custom_headers = (request.form.get("custom_headers") or "").strip() or None
    clear_key = request.form.get("clear_key") == "1"

    row = get_db().execute(
        "SELECT api_key_enc FROM ai_providers WHERE provider_key = ?",
        (provider_key,),
    ).fetchone()
    api_key_enc = row["api_key_enc"] if row else None
    if clear_key:
        api_key_enc = None
    elif api_key_raw:
        api_key_enc = ai_providers.encrypt_secret(app.secret_key, api_key_raw)

    get_db().execute(
        """
        INSERT INTO ai_providers
            (provider_key, enabled, api_key_enc, base_url, model, custom_headers, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(provider_key) DO UPDATE SET
            enabled = excluded.enabled,
            api_key_enc = excluded.api_key_enc,
            base_url = excluded.base_url,
            model = excluded.model,
            custom_headers = excluded.custom_headers,
            updated_at = excluded.updated_at
        """,
        (provider_key, enabled, api_key_enc, base_url, model, custom_headers, utcnow()),
    )
    get_db().commit()

    if request.form.get("make_default") == "1":
        _setting_set("ai_default_provider", provider_key)

    flash(f"Saved {ai_providers.PROVIDERS[provider_key]['label']}.", "ok")
    return redirect(url_for("settings") + "#ai-providers")


@app.route("/settings/ai/<provider_key>/test", methods=["POST"])
@require_admin
def settings_test_ai_provider(provider_key: str):
    if provider_key not in ai_providers.PROVIDERS:
        abort(404)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in request.headers.get("Accept", "")
    try:
        api_key, base_url, model, custom_headers = _resolve_ai_credentials(provider_key)
        result = ai_providers.test_connection(
            provider_key, api_key=api_key, base_url=base_url, model=model, custom_headers=custom_headers
        )
        msg = f"Test OK — provider replied: {result[:80]}"
        if is_ajax:
            return jsonify({"success": True, "message": msg})
        flash(msg, "ok")
    except Exception as exc:
        msg = str(exc)
        if is_ajax:
            return jsonify({"success": False, "message": msg})
        flash(msg, "error")
    return redirect(url_for("settings") + "#ai-providers")


@app.route("/settings/ai/default", methods=["POST"])
@require_admin
def settings_ai_default():
    provider = (request.form.get("provider") or "").strip()
    if provider and provider not in ai_providers.PROVIDERS:
        flash("Unknown provider.", "error")
    else:
        if provider:
            _setting_set("ai_default_provider", provider)
        else:
            get_db().execute("DELETE FROM settings WHERE key = 'ai_default_provider'")
            get_db().commit()
        flash("Default AI provider updated.", "ok")
    return redirect(url_for("settings") + "#ai-providers")


@app.route("/entry/<int:entry_id>/ai/<action>", methods=["POST"])
@require_admin
def entry_ai_assist(entry_id: int, action: str):
    if action not in ai_providers.ACTIONS:
        abort(404)
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)

    draft_key = f"ai_draft_{entry_id}"
    provider_key = (request.form.get("provider") or "").strip() or _default_ai_provider()
    if os.environ.get("SEEDBANK_AI_MOCK") == "1" and not provider_key:
        provider_key = "openai"
    if not provider_key:
        session.pop(draft_key, None)
        flash("Configure and enable an AI provider in Settings first.", "error")
        return redirect(url_for("detail", entry_id=entry_id))

    att_names = ", ".join(
        a["original_name"] for a in _attachments_for_entry(entry_id)
    )
    try:
        system, user = ai_providers.build_messages(action, entry, att_names)
        api_key, base_url, model, custom_headers = _resolve_ai_credentials(provider_key)
        if os.environ.get("SEEDBANK_AI_MOCK") == "1" and not api_key:
            api_key = "mock"
        draft = ai_providers.complete(
            provider_key,
            api_key=api_key,
            base_url=base_url,
            model=model,
            system=system,
            user=user,
            custom_headers=custom_headers,
        )
        if action == "features" and os.environ.get("SEEDBANK_AI_MOCK") != "1":
            suggestions = ai_providers.count_feature_suggestions(draft)
            if not (
                ai_providers.FEATURE_MIN_SUGGESTIONS
                <= suggestions
                <= ai_providers.FEATURE_MAX_SUGGESTIONS
            ):
                correction_system = (
                    f"{system}\n\n"
                    "Important: revise the result to include a top-level numbered list "
                    f"with between {ai_providers.FEATURE_MIN_SUGGESTIONS} and "
                    f"{ai_providers.FEATURE_MAX_SUGGESTIONS} feature suggestions."
                )
                correction_user = (
                    "Revise this draft so it satisfies the feature-count requirement.\n\n"
                    f"Current draft:\n{draft}\n"
                )
                draft = ai_providers.complete(
                    provider_key,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    system=correction_system,
                    user=correction_user,
                )
                suggestions = ai_providers.count_feature_suggestions(draft)
                if not (
                    ai_providers.FEATURE_MIN_SUGGESTIONS
                    <= suggestions
                    <= ai_providers.FEATURE_MAX_SUGGESTIONS
                ):
                    raise ai_providers.AIError(
                        "Suggest Features must return between "
                        f"{ai_providers.FEATURE_MIN_SUGGESTIONS} and "
                        f"{ai_providers.FEATURE_MAX_SUGGESTIONS} suggestions. "
                        "Please try again or choose a different model."
                    )
        draft = _clamp_assist_preview(draft)
    except ai_providers.AIError as exc:
        # Avoid showing stale drafts from prior runs when this action fails.
        session.pop(draft_key, None)
        flash(
            f"{ai_providers.ACTIONS[action]['label']} failed: {exc}",
            "error",
        )
        return redirect(url_for("detail", entry_id=entry_id))
    except requests.RequestException as exc:
        session.pop(draft_key, None)
        flash(
            f"{ai_providers.ACTIONS[action]['label']} network error: {exc}",
            "error",
        )
        return redirect(url_for("detail", entry_id=entry_id))

    session[draft_key] = {
        "action": action,
        "action_label": ai_providers.ACTIONS[action]["label"],
        "provider": provider_key,
        "provider_label": ai_providers.PROVIDERS[provider_key]["label"],
        "draft": draft,
        "default_apply": ai_providers.ACTIONS[action]["default_apply"],
    }
    logger.info(
        "AI assist entry=%s action=%s provider=%s",
        entry_id,
        action,
        provider_key,
    )
    flash("Draft ready — review below before applying.", "ok")
    return redirect(url_for("detail", entry_id=entry_id) + "#ai-assist")


@app.route("/entry/<int:entry_id>/ai/apply", methods=["POST"])
@require_admin
def entry_ai_apply(entry_id: int):
    entry = fetch_entry(entry_id)
    if not entry:
        abort(404)
    draft_key = f"ai_draft_{entry_id}"
    payload = session.get(draft_key)
    if not payload or not payload.get("draft"):
        flash("No AI draft to apply.", "error")
        return redirect(url_for("detail", entry_id=entry_id))

    mode = (request.form.get("mode") or payload.get("default_apply") or "append").strip()
    draft = payload["draft"].strip()
    assist_section = _assist_section_block(payload, draft)
    replaced_existing = False
    if mode == "replace":
        new_body = assist_section
    else:
        existing = (entry.get("body") or "").rstrip()
        if existing:
            new_body, replaced_existing = _replace_existing_assist_section(
                existing, payload, assist_section
            )
        else:
            new_body = assist_section
        if not existing or not replaced_existing:
            new_body = f"{existing}\n\n{assist_section}".strip() if existing else assist_section
    new_body = _normalize_ai_markdown(new_body)

    get_db().execute(
        "UPDATE entries SET body = ?, updated_at = ? WHERE id = ?",
        (new_body, utcnow(), entry_id),
    )
    get_db().commit()
    updated = fetch_entry(entry_id)
    searchmod.fts_upsert(get_db(), updated)
    get_db().commit()
    try:
        garden.sync_entry(
            repos_dir=REPOS_DIR, garden_dir=GARDEN_DIR, entry=updated, action="update"
        )
    except GitError as exc:
        logger.warning("Garden sync failed: %s", exc)
    session.pop(draft_key, None)
    if mode != "replace" and replaced_existing:
        flash("Updated existing Assist section for this action.", "ok")
    else:
        flash("AI draft applied to notes.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/entry/<int:entry_id>/ai/discard", methods=["POST"])
@require_admin
def entry_ai_discard(entry_id: int):
    session.pop(f"ai_draft_{entry_id}", None)
    flash("AI draft discarded.", "ok")
    return redirect(url_for("detail", entry_id=entry_id))


@app.route("/settings/trackers", methods=["POST"])
@require_admin
def settings_save_trackers():
    _setting_set("ext_jira_url", (request.form.get("ext_jira_url") or "").strip())
    _setting_set("ext_bitbucket_url", (request.form.get("ext_bitbucket_url") or "").strip())
    _setting_set("ext_github_url", (request.form.get("ext_github_url") or "").strip())
    flash("Tracker link templates saved.", "ok")
    return redirect(url_for("settings") + "#trackers")


@app.route("/settings/fs-roots", methods=["POST"])
@require_admin
def settings_save_fs_roots():
    roots = (request.form.get("fs_browser_roots") or "").strip()
    _setting_set("fs_browser_roots", roots)
    flash("Filesystem browse roots saved.", "ok")
    return redirect(url_for("settings") + "#fs-browser")


@app.route("/api/fs/roots")
@require_admin
def api_fs_roots():
    roots = [str(p) for p in _fs_roots()]
    return jsonify({"roots": roots})


@app.route("/api/fs/list")
@require_admin
def api_fs_list():
    roots = _fs_roots()
    raw_path = (request.args.get("path") or "").strip()
    if not raw_path:
        if not roots:
            return jsonify({"error": "No filesystem roots configured."}), 400
        raw_path = str(roots[0])
    try:
        payload = fs_browser.list_directory(Path(raw_path), roots)
    except fs_browser.FSBrowserError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(payload)


@app.route("/ingest/agents", methods=["GET", "POST"])
@require_admin
def ingest_agents_page():
    default_candidates = [
        Path("/workspace/AGENTS.md"),
        APP_DIR.parent.parent / "AGENTS.md",
        Path.cwd() / "AGENTS.md",
    ]
    discovered = agents_ingest.discover_agents_files(
        [Path("/workspace"), APP_DIR.parent.parent, Path.cwd(), *_fs_roots()]
    )
    for cand in default_candidates:
        if cand.is_file() and cand.resolve() not in discovered:
            discovered.insert(0, cand.resolve())

    if request.method == "POST":
        raw_path = (request.form.get("path") or "").strip()
        uploaded = request.files.get("file")
        try:
            if uploaded and uploaded.filename:
                text = uploaded.read().decode("utf-8", errors="replace")
                name = Path(uploaded.filename).name or "AGENTS.md"
                # Write to a temp path label for metadata only
                source = Path(f"upload://{name}")
                if not text.strip():
                    raise agents_ingest.AgentsIngestError("Uploaded file is empty.")
                payload = agents_ingest.build_entry_payload(
                    Path(name), text
                )
                payload["url"] = f"upload://{name}"
                payload["source_path"] = f"upload://{name}"
            else:
                if not raw_path:
                    raise agents_ingest.AgentsIngestError("Choose a path or upload a file.")
                path = Path(raw_path).expanduser()
                resolved = path.resolve()
                if resolved.name.upper() not in {"AGENTS.MD", "AGENT.MD"} and not (
                    resolved.suffix.lower() in {".md", ".markdown", ".txt"}
                    and "agent" in resolved.name.lower()
                ):
                    raise agents_ingest.AgentsIngestError(
                        "Choose an AGENTS.md (or similarly named Markdown) file."
                    )
                text = agents_ingest.read_agents_file(resolved)
                payload = agents_ingest.build_entry_payload(resolved, text)

            agents_ingest.ensure_ingest_tables(get_db())
            entry_id = agents_ingest.insert_entry(get_db(), payload)
            entry = fetch_entry(entry_id)
            searchmod.fts_upsert(get_db(), entry)
            get_db().commit()
            try:
                garden.sync_entry(
                    repos_dir=REPOS_DIR,
                    garden_dir=GARDEN_DIR,
                    entry=entry,
                    action="create",
                )
                versioned = True
            except GitError as exc:
                logger.warning("Garden sync failed for agents ingest: %s", exc)
                versioned = False
            flash(
                f"Ingested {payload['source_name']} → entry #{entry_id}"
                f"{' (garden versioned)' if versioned else ' (garden skipped)'}.",
                "ok",
            )
            return redirect(url_for("detail", entry_id=entry_id))
        except agents_ingest.AgentsIngestError as exc:
            flash(str(exc), "error")

    events = agents_ingest.recent_ingests(get_db(), limit=25)
    return render_template(
        "ingest_agents.html",
        discovered=[str(p) for p in discovered],
        events=events,
        fs_roots=_fs_roots(),
    )


def _authed_for_ingest_api() -> bool:
    if session.get("admin"):
        return True
    auth = request.headers.get("Authorization") or ""
    token = None
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    elif request.authorization and request.authorization.password:
        token = request.authorization.password
    return verify_git_token(token)


def _ingest_one_agents_md(
    *, raw_path: str, content: str | None, filename: str
) -> dict:
    """Shared single-file ingest logic used by both the single and batch
    ingest API routes. Raises agents_ingest.AgentsIngestError on bad input."""
    if content is not None:
        path = Path(raw_path) if raw_path else Path(filename or "AGENTS.md")
        text = str(content)
        if not text.strip():
            raise agents_ingest.AgentsIngestError("Content is empty.")
        built = agents_ingest.build_entry_payload(path, text)
        if raw_path:
            built["url"] = raw_path
            built["source_path"] = raw_path
    else:
        if not raw_path:
            raise agents_ingest.AgentsIngestError("path or content required")
        path = Path(raw_path).expanduser().resolve()
        text = agents_ingest.read_agents_file(path)
        built = agents_ingest.build_entry_payload(path, text)

    agents_ingest.ensure_ingest_tables(get_db())
    entry_id = agents_ingest.insert_entry(get_db(), built)
    entry = fetch_entry(entry_id)
    searchmod.fts_upsert(get_db(), entry)
    get_db().commit()
    versioned = False
    try:
        garden.sync_entry(
            repos_dir=REPOS_DIR,
            garden_dir=GARDEN_DIR,
            entry=entry,
            action="create",
        )
        versioned = True
    except GitError as exc:
        logger.warning("Garden sync failed for agents ingest API: %s", exc)
    return {
        "entry_id": entry_id,
        "title": entry["title"],
        "source_path": built["source_path"],
        "content_hash": built["content_hash"],
        "garden_versioned": versioned,
        "url": url_for("detail", entry_id=entry_id),
    }


@app.route("/api/ingest/agents-md", methods=["POST"])
def api_ingest_agents_md():
    """Cursor / CLI ingest endpoint. Auth: admin session or Bearer git token."""
    if not _authed_for_ingest_api():
        return jsonify({"error": "Unauthorized"}), 401

    payload_json = request.get_json(silent=True) or {}
    raw_path = (payload_json.get("path") or request.form.get("path") or "").strip()
    content = payload_json.get("content")
    filename = (payload_json.get("filename") or "AGENTS.md").strip() or "AGENTS.md"

    try:
        result = _ingest_one_agents_md(
            raw_path=raw_path, content=content, filename=filename
        )
        return jsonify(result)
    except agents_ingest.AgentsIngestError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/ingest/agents-md/batch", methods=["POST"])
def api_ingest_agents_md_batch():
    """Batch variant for exporting several instruction files in one call
    (e.g. from the Antigravity export plugin: a global rules file plus
    several .agent/rules/*.md files). Auth matches the single-file route."""
    if not _authed_for_ingest_api():
        return jsonify({"error": "Unauthorized"}), 401

    payload_json = request.get_json(silent=True) or {}
    files = payload_json.get("files")
    if not isinstance(files, list):
        return jsonify({"error": "files must be a list"}), 400
    if len(files) > 50:
        return jsonify({"error": "Too many files in one batch (max 50)."}), 400

    results = []
    for item in files:
        if not isinstance(item, dict):
            results.append({"filename": None, "ok": False, "error": "Invalid file entry"})
            continue
        raw_path = str(item.get("path") or "").strip()
        content = item.get("content")
        filename = (str(item.get("filename") or "AGENTS.md")).strip() or "AGENTS.md"
        try:
            result = _ingest_one_agents_md(
                raw_path=raw_path, content=content, filename=filename
            )
            results.append({"filename": filename, "ok": True, **result})
        except agents_ingest.AgentsIngestError as exc:
            results.append({"filename": filename, "ok": False, "error": str(exc)})

    return jsonify({"results": results})


@app.route("/settings/tokens", methods=["POST"])
@require_admin
def settings_create_token():
    name = (request.form.get("name") or "").strip() or "default"
    token, prefix, hashed = generate_token()
    get_db().execute(
        """
        INSERT INTO access_tokens (name, token_hash, prefix, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (name, hashed, prefix, utcnow()),
    )
    get_db().commit()
    session["new_token"] = token
    flash("Token created. Copy it now — it will not be shown again.", "ok")
    return redirect(url_for("settings"))


@app.route("/settings/tokens/<int:token_id>/revoke", methods=["POST"])
@require_admin
def settings_revoke_token(token_id: int):
    get_db().execute("DELETE FROM access_tokens WHERE id = ?", (token_id,))
    get_db().commit()
    flash("Token revoked.", "ok")
    return redirect(url_for("settings"))


@app.route("/settings/ssh-keys", methods=["POST"])
@require_admin
def settings_add_ssh_key():
    name = (request.form.get("name") or "").strip() or "key"
    public_key = (request.form.get("public_key") or "").strip()
    try:
        fingerprint = ssh_fingerprint(public_key)
    except GitError as exc:
        flash(str(exc), "error")
        return redirect(url_for("settings"))
    try:
        get_db().execute(
            """
            INSERT INTO ssh_keys (name, public_key, fingerprint, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, public_key, fingerprint, utcnow()),
        )
        get_db().commit()
    except sqlite3.IntegrityError:
        flash("That SSH key is already registered.", "error")
        return redirect(url_for("settings"))
    flash("SSH key added.", "ok")
    return redirect(url_for("settings"))


@app.route("/settings/ssh-keys/<int:key_id>/revoke", methods=["POST"])
@require_admin
def settings_revoke_ssh_key(key_id: int):
    get_db().execute("DELETE FROM ssh_keys WHERE id = ?", (key_id,))
    get_db().commit()
    flash("SSH key removed.", "ok")
    return redirect(url_for("settings"))


@app.cli.command("init-db")
def init_db_command() -> None:
    with app.app_context():
        init_db()
    print(f"Initialized database at {DATABASE}")


with app.app_context():
    init_db()


def _start_ssh_if_enabled() -> None:
    if not SSH_ENABLED:
        if os.environ.get("SEEDBANK_SSH", "1") == "1" and not ASYNCSSH_AVAILABLE:
            logger.warning("SSH requested but asyncssh is not installed")
        return
    if not git_available():
        logger.warning("SSH enabled but git is not available")
        return
    key_lookup = make_key_lookup(load_ssh_public_keys)
    host = os.environ.get("SEEDBANK_HOST", "127.0.0.1")
    start_ssh_server_thread(
        host=host if host != "0.0.0.0" else "0.0.0.0",
        port=SSH_PORT,
        host_key_path=SSH_DIR / "host_key",
        repos_dir=REPOS_DIR,
        key_lookup=key_lookup,
    )


if __name__ == "__main__":
    host = os.environ.get("SEEDBANK_HOST", "127.0.0.1")
    port = HTTP_PORT
    debug = os.environ.get("SEEDBANK_DEBUG", "1") == "1"
    # Avoid double-binding SSH under the reloader parent/child
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not debug:
        _start_ssh_if_enabled()
    elif debug:
        # First process with reloader: start only in child; for simplicity disable reloader when SSH on
        if SSH_ENABLED:
            debug = False
            _start_ssh_if_enabled()
    app.run(host=host, port=port, debug=debug, use_reloader=False)
