#!/usr/bin/env python3
"""CLI: ingest AGENTS.md into Idea Forge (timestamped, logged, garden-versioned).

Cursor agents can run:

  cd projects/idea-tracker
  python3 ingest_agents_md.py --path /workspace/AGENTS.md

Or against a running server:

  python3 ingest_agents_md.py --path AGENTS.md --http http://127.0.0.1:5050 --token sb_…
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def ingest_local(path: Path, data_dir: Path) -> dict:
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("SEEDBANK_DATA", str(data_dir))
    os.environ.setdefault("SEEDBANK_SSH", "0")

    import agents_ingest
    import garden
    import search as searchmod
    from git_util import GitError, ensure_dirs

    data_dir.mkdir(parents=True, exist_ok=True)
    paths = ensure_dirs(data_dir)
    db_path = data_dir / "seedbank.db"

    # Ensure schema via app.init_db
    import app as forge

    with forge.app.app_context():
        forge.init_db()
        text = agents_ingest.read_agents_file(path)
        payload = agents_ingest.build_entry_payload(path.resolve(), text)
        agents_ingest.ensure_ingest_tables(forge.get_db())
        entry_id = agents_ingest.insert_entry(forge.get_db(), payload)
        entry = forge.fetch_entry(entry_id)
        searchmod.fts_upsert(forge.get_db(), entry)
        forge.get_db().commit()
        try:
            garden.sync_entry(
                repos_dir=paths["repos"],
                garden_dir=paths["garden"],
                entry=entry,
                action="create",
            )
            versioned = True
        except GitError as exc:
            versioned = False
            print(f"WARN: garden versioning skipped: {exc}", file=sys.stderr)
        return {
            "entry_id": entry_id,
            "title": entry["title"],
            "source_path": str(path.resolve()),
            "content_hash": payload["content_hash"],
            "garden_versioned": versioned,
            "url": f"/entry/{entry_id}",
        }


def ingest_http(path: Path, base: str, token: str | None) -> dict:
    import requests

    text = path.read_text(encoding="utf-8")
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(
        base.rstrip("/") + "/api/ingest/agents-md",
        json={"path": str(path.resolve()), "content": text, "filename": path.name},
        headers=headers,
        timeout=60,
    )
    if resp.status_code >= 400:
        raise SystemExit(f"HTTP {resp.status_code}: {resp.text[:400]}")
    return resp.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest AGENTS.md into Idea Forge")
    parser.add_argument(
        "--path",
        default="",
        help="Path to AGENTS.md (default: discover under repo / cwd)",
    )
    parser.add_argument(
        "--data",
        default=os.environ.get("SEEDBANK_DATA", str(ROOT / "data")),
        help="Idea Forge data directory",
    )
    parser.add_argument("--http", default="", help="Optional running server base URL")
    parser.add_argument("--token", default=os.environ.get("SEEDBANK_TOKEN", ""))
    args = parser.parse_args()

    if args.path:
        path = Path(args.path).expanduser()
    else:
        candidates = [
            Path("/workspace/AGENTS.md"),
            Path.cwd() / "AGENTS.md",
            ROOT.parent.parent / "AGENTS.md",
            ROOT / "AGENTS.md",
        ]
        path = next((p for p in candidates if p.is_file()), None)
        if not path:
            raise SystemExit("No AGENTS.md found; pass --path")

    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    if args.http:
        result = ingest_http(path, args.http, args.token or None)
    else:
        result = ingest_local(path, Path(args.data))

    print(
        f"OK: entry #{result.get('entry_id')} {result.get('title')!r} "
        f"garden={result.get('garden_versioned')} → {result.get('url')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
