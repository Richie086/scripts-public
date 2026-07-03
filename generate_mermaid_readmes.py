#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

REPO_ROOT = Path(__file__).resolve().parent
README_NAME = "README.md"
AUTO_START = "<!-- AUTO-GENERATED MERMAID START -->"
AUTO_END = "<!-- AUTO-GENERATED MERMAID END -->"
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "env"}


def escape_label(label: str) -> str:
    return label.replace('"', '\\"')


def build_mermaid_tree(directory: Path) -> str:
    node_ids: Dict[Path, str] = {}
    edges: list[str] = []
    current_id = 0

    def node_id(path: Path) -> str:
        nonlocal current_id
        if path not in node_ids:
            node_ids[path] = f"n{current_id}"
            current_id += 1
        return node_ids[path]

    def should_skip(path: Path) -> bool:
        return any(part in EXCLUDE_DIRS for part in path.parts)

    root_node = node_id(directory)
    nodes: dict[str, str] = {root_node: escape_label(directory.name or directory.drive or "/")}

    for child in sorted(directory.rglob("*"), key=lambda p: str(p).lower()):
        if should_skip(child):
            continue
        parent = child.parent
        if should_skip(parent):
            continue
        parent_id = node_id(parent)
        child_id = node_id(child)
        label = child.name + ("/" if child.is_dir() else "")
        nodes[child_id] = escape_label(label)
        edges.append(f"{parent_id} --> {child_id}")

    lines = ["```mermaid", "graph TD"]
    lines.append(f'{root_node}["{nodes[root_node]}"]')
    for path in sorted(node_ids, key=lambda p: str(p).lower()):
        nid = node_ids[path]
        if nid == root_node:
            continue
        lines.append(f'{nid}["{nodes[nid]}"]')
    lines.extend(edges)
    lines.append("```")
    return "\n".join(lines)


def build_generated_block(directory: Path) -> str:
    graph = build_mermaid_tree(directory)
    return (
        f"{AUTO_START}\n"
        f"<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->\n\n"
        f"{graph}\n\n"
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
