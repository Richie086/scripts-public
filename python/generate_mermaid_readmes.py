#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict


def find_repo_root() -> Path:
    """Find the git repository root by searching for .git directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent


REPO_ROOT = find_repo_root()
README_NAME = "README.md"
AUTO_START = "<!-- AUTO-GENERATED MERMAID START -->"
AUTO_END = "<!-- AUTO-GENERATED MERMAID END -->"
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "env"}


def escape_label(label: str) -> str:
    return label.replace('"', '\\"')


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def describe_entry(path: Path) -> str:
    if path.is_dir():
        children = [p for p in path.iterdir() if not should_skip(p)]
        child_count = len(children)
        return f"dir: {path.name} ({child_count} entries)"

    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    return f"file: {path.name} ({size} bytes)"


def build_mermaid_gitgraph(directory: Path) -> str:
    entries = []
    for child in sorted(directory.iterdir(), key=lambda p: str(p).lower()):
        if should_skip(child):
            continue
        entries.append(child)

    lines = ["```mermaid", "gitGraph"]
    root_label = escape_label(f"root: {directory.name or directory.drive or '/'}")
    lines.append(f'    commit id: "{root_label}"')

    for child in entries:
        label = escape_label(describe_entry(child))
        lines.append(f'    commit id: "{label}"')

    if not entries:
        lines.append('    commit id: "(empty directory)"')

    lines.append("```")
    return "\n".join(lines)


def build_generated_block(directory: Path) -> str:
    graph = build_mermaid_gitgraph(directory)
    return (
        f"{AUTO_START}\n"
        f"<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->\n\n"
        f"## Directory structure\n\n"
        f"<details>\n"
        f"<summary>Show GitGraph diagram for `{directory.name or directory}`</summary>\n\n"
        f"{graph}\n\n"
        f"</details>\n\n"
        f"{AUTO_END}\n\n"
    )


def update_readme(directory: Path) -> bool:
    readme_path = directory / README_NAME
    generated_block = build_generated_block(directory)

    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        if AUTO_START in content and AUTO_END in content:
            pattern = re.compile(
                rf"{re.escape(AUTO_START)}.*?{re.escape(AUTO_END)}\n*",
                re.DOTALL,
            )
            new_content = pattern.sub(generated_block, content)
        else:
            new_content = generated_block + content
    else:
        title = f"# {directory.name or directory}\n\n"
        new_content = title + generated_block + "Auto-generated directory structure for this folder.\n"

    readme_path.write_text(new_content, encoding="utf-8")
    return True


def gather_directories(root: Path) -> list[Path]:
    directories = []
    for path in sorted(root.rglob("*"), key=lambda p: str(p).lower()):
        if path.is_dir() and not any(part in EXCLUDE_DIRS for part in path.parts):
            directories.append(path)
    directories.insert(0, root)
    return directories


def main() -> int:
    directories = gather_directories(REPO_ROOT)

    for directory in directories:
        update_readme(directory)
        print(f"Updated README in: {directory.relative_to(REPO_ROOT)}")

    print("\nFinished generating Mermaid README diagrams for every directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
