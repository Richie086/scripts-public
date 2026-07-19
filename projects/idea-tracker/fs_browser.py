"""Local filesystem browser helpers for Idea Forge path picking."""

from __future__ import annotations

import os
from pathlib import Path


class FSBrowserError(Exception):
    """User-facing filesystem browse error."""


def parse_roots(raw: str | None, env_fallback: str | None = None) -> list[Path]:
    chunks: list[str] = []
    if raw and raw.strip():
        for line in raw.splitlines():
            line = line.strip()
            if line:
                chunks.append(line)
    elif env_fallback and env_fallback.strip():
        chunks = [p.strip() for p in env_fallback.split(os.pathsep) if p.strip()]

    roots: list[Path] = []
    seen: set[str] = set()
    for chunk in chunks:
        expanded = Path(chunk).expanduser()
        try:
            resolved = expanded.resolve()
        except OSError:
            continue
        if not resolved.exists() or not resolved.is_dir():
            continue
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        roots.append(resolved)
    return roots


def is_under_root(path: Path, roots: list[Path]) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for root in roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def list_directory(
    path: Path,
    roots: list[Path],
    *,
    show_hidden: bool = False,
    max_entries: int = 500,
) -> dict:
    if not roots:
        raise FSBrowserError("No filesystem roots configured. Add roots in Settings.")
    try:
        resolved = path.expanduser().resolve()
    except OSError as exc:
        raise FSBrowserError(f"Cannot resolve path: {exc}") from exc
    if not is_under_root(resolved, roots):
        raise FSBrowserError("Path is outside allowed roots.")
    if not resolved.exists():
        raise FSBrowserError("Path does not exist.")
    if not resolved.is_dir():
        raise FSBrowserError("Path is not a directory.")

    parent = None
    at_root = any(resolved == root for root in roots)
    if not at_root:
        candidate = resolved.parent
        if is_under_root(candidate, roots):
            parent = candidate

    entries: list[dict] = []
    try:
        children = sorted(
            resolved.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )
    except PermissionError as exc:
        raise FSBrowserError("Permission denied.") from exc

    for child in children:
        name = child.name
        if not show_hidden and name.startswith("."):
            continue
        try:
            is_dir = child.is_dir()
            is_file = child.is_file()
            if child.is_symlink():
                target = child.resolve()
                if not is_under_root(target, roots):
                    continue
        except OSError:
            continue
        if not is_dir and not is_file:
            continue
        entries.append(
            {
                "name": name,
                "path": str(child.resolve() if not child.is_symlink() else child),
                "type": "dir" if is_dir else "file",
            }
        )
        if len(entries) >= max_entries:
            break

    return {
        "path": str(resolved),
        "parent": str(parent) if parent else None,
        "entries": entries,
        "truncated": len(entries) >= max_entries,
    }
