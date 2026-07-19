"""Auto-version Idea Forge entries into the garden git repo."""

from __future__ import annotations

import logging
from pathlib import Path

from git_util import GARDEN_SLUG, GitError, ensure_garden, run_git, slugify

logger = logging.getLogger("seedbank.garden")


def entry_relpath(entry: dict) -> str:
    slug = slugify(entry["title"]) or "entry"
    return f"entries/{entry['category']}/{entry['id']}-{slug}.md"


def _escape_frontmatter(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def render_entry_markdown(entry: dict) -> str:
    tags = _escape_frontmatter(entry.get("tags") or "")
    url = _escape_frontmatter(entry.get("url") or "")
    body = entry.get("body") or ""
    title = _escape_frontmatter(entry["title"])
    lines = [
        "---",
        f"id: {entry['id']}",
        f'title: "{title}"',
        f"category: {entry['category']}",
        f"status: {entry['status']}",
        f'url: "{url}"',
        f'tags: "{tags}"',
        f"updated_at: {entry['updated_at']}",
        "---",
        "",
        body,
        "",
    ]
    return "\n".join(lines)


def _paths_for_entry(garden_dir: Path, entry: dict) -> list[Path]:
    """All on-disk markdown files that belong to this entry id (any category/slug)."""
    entries_root = garden_dir / "entries"
    if not entries_root.exists():
        return []
    return sorted(entries_root.glob(f"*/{entry['id']}-*.md"))


def _push_garden(garden_dir: Path) -> None:
    result = run_git(["push", "origin", "HEAD:main"], cwd=garden_dir, check=False)
    if result.returncode != 0:
        msg = result.stderr.strip() or result.stdout.strip() or "garden push failed"
        logger.error("Garden push failed: %s", msg)
        raise GitError(msg)


def sync_entry(
    *,
    repos_dir: Path,
    garden_dir: Path,
    entry: dict,
    action: str,
) -> None:
    """action: create | update | delete"""
    ensure_garden(repos_dir, garden_dir)
    rel = entry_relpath(entry)
    abs_path = garden_dir / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove any stale paths for this entry id (old title/category).
    for old in _paths_for_entry(garden_dir, entry):
        if action == "delete" or old.resolve() != abs_path.resolve():
            old.unlink(missing_ok=True)

    if action == "delete":
        run_git(["add", "-A", "entries"], cwd=garden_dir)
        status = run_git(["status", "--porcelain"], cwd=garden_dir)
        if not status.stdout.strip():
            return
        run_git(
            ["commit", "-m", f"Delete {entry['category']}: {entry['title']}"],
            cwd=garden_dir,
        )
        _push_garden(garden_dir)
        return

    abs_path.write_text(render_entry_markdown(entry), encoding="utf-8")
    run_git(["add", "-A", "entries"], cwd=garden_dir)
    status = run_git(["status", "--porcelain"], cwd=garden_dir)
    if not status.stdout.strip():
        return
    verb = "Create" if action == "create" else "Update"
    run_git(
        ["commit", "-m", f"{verb} {entry['category']}: {entry['title']}"],
        cwd=garden_dir,
    )
    _push_garden(garden_dir)


def entry_history(
    repos_dir: Path, garden_dir: Path, entry: dict, limit: int = 20
) -> list[dict]:
    from git_util import log_commits

    ensure_garden(repos_dir, garden_dir)
    bare = repos_dir / f"{GARDEN_SLUG}.git"
    rel = entry_relpath(entry)
    commits = log_commits(bare, "main", path=rel, limit=limit)
    if commits:
        return commits
    for path in _paths_for_entry(garden_dir, entry):
        rel2 = str(path.relative_to(garden_dir))
        commits = log_commits(bare, "main", path=rel2, limit=limit)
        if commits:
            return commits
    return []
