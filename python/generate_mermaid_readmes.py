#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

from dirtree_chart import config, diagram


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
CATALOG_START = "<!-- AUTO-GENERATED CATALOG START -->"
CATALOG_END = "<!-- AUTO-GENERATED CATALOG END -->"
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "env"}
MAX_FOLDER_DEPTH = 99
MAX_DESCRIPTION_LENGTH = 240
MAX_FILES_IN_NODE = 8
NUMERIC_ID_PATTERN = re.compile(r"\d+(?:\.\d+)*")
QUOTED_FILE_NODE = re.compile(r'\["([^"]*)"\](:::file)\b')

MERMAID_CLASS_STYLES = {
    "root": "fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff",
    "folder": "fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03",
    "file-md": "fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a",
    "file-py": "fill:#dcfce7,stroke:#16a34a,stroke-width:1px,color:#14532d",
    "file-sh": "fill:#ccfbf1,stroke:#0d9488,stroke-width:1px,color:#134e4a",
    "file-ps1": "fill:#e0e7ff,stroke:#6366f1,stroke-width:1px,color:#312e81",
    "file-html": "fill:#ffedd5,stroke:#ea580c,stroke-width:1px,color:#7c2d12",
    "file-config": "fill:#f3f4f6,stroke:#6b7280,stroke-width:1px,color:#374151",
    "file-text": "fill:#fafafa,stroke:#a3a3a3,stroke-width:1px,color:#404040",
    "file-git": "fill:#fee2e2,stroke:#ef4444,stroke-width:1px,color:#7f1d1d",
    "file-image": "fill:#f3e8ff,stroke:#a855f7,stroke-width:1px,color:#581c87",
    "file-binary": "fill:#fef3c7,stroke:#ca8a04,stroke-width:1px,color:#713f12",
    "file-bundle": "fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#334155",
    "file-other": "fill:#f2f2f2,stroke:#9ca3af,stroke-width:1px,color:#374151",
}

EXTENSION_TO_FILE_CLASS = {
    "md": "file-md",
    "markdown": "file-md",
    "mdx": "file-md",
    "py": "file-py",
    "sh": "file-sh",
    "bash": "file-sh",
    "ps1": "file-ps1",
    "html": "file-html",
    "htm": "file-html",
    "json": "file-config",
    "yml": "file-config",
    "yaml": "file-config",
    "toml": "file-config",
    "ini": "file-config",
    "cfg": "file-config",
    "xml": "file-config",
    "txt": "file-text",
    "rst": "file-text",
    "git": "file-git",
    "png": "file-image",
    "jpg": "file-image",
    "jpeg": "file-image",
    "gif": "file-image",
    "svg": "file-image",
    "webp": "file-image",
    "pdf": "file-binary",
    "zip": "file-binary",
    "cer": "file-binary",
    "crt": "file-binary",
    "key": "file-binary",
    "pem": "file-binary",
}

SECTION_HEADERS = {
    ".agents": "⚙️ Agent Guidelines (`/.agents`)",
    "bash": "🐚 Linux Bash (`/bash`)",
    "markdown": "📝 Markdown (`/markdown`)",
    "markup": "📄 Markup (`/markup`)",
    "PowerShell": "🔷 PowerShell (`/PowerShell`)",
    "powershell": "🔷 Windows PowerShell (`/powershell`)",
    "projects": "📁 Projects (`/projects`)",
    "python": "🐍 Python (`/python`)",
    "web": "🌐 Web (`/web`)",
    "wordpress": "📝 WordPress (`/wordpress`)",
}


def _patch_dirtree_chart_duplicate_name_bug() -> None:
    """Fix UnboundLocalError when duplicate filenames appear at level 1."""

    def _add_ids_to_layer_hierarchy(self) -> None:
        self.layerHierarchyWithIds = self.layerHierarchy.copy()

        for level_id, level_group in self.layerHierarchyWithIds.items():
            new_layer_folders = {}
            layer_folder_group_counter = 1
            from_id_before = -1

            for layer_folder_group in level_group:
                layer_folder_counter = 1
                for folder in layer_folder_group:
                    if len(layer_folder_group) == layer_folder_counter:
                        if level_id > 1:
                            pos = layer_folder_counter - 1
                            parent_key = layer_folder_group[pos - 1]
                            parent_entry = self.layerHierarchyWithIds[pos].get(parent_key)
                            if parent_entry is None:
                                for key, value in self.layerHierarchyWithIds[pos].items():
                                    if key.split("__mermaid__")[0] == parent_key:
                                        parent_entry = value
                                        break
                            from_id = parent_entry["id"] if parent_entry else layer_folder_group_counter

                            if from_id_before != from_id:
                                layer_folder_group_counter = 1

                            val = f"{from_id}.{layer_folder_group_counter}"
                            from_id_before = from_id
                        else:
                            val = layer_folder_group_counter
                            from_id = val

                        typ = "d"
                        fn_split = folder.split(".")
                        if len(fn_split) > 1:
                            typ = "f"
                            if folder in new_layer_folders:
                                folder = f"{folder}__mermaid__{from_id}"
                            new_layer_folders[folder] = {
                                "id": val,
                                "type": typ,
                                "ext": fn_split[-1],
                            }
                        else:
                            if folder in new_layer_folders:
                                folder = f"{folder}__mermaid__{from_id}"
                            new_layer_folders[folder] = {
                                "id": val,
                                "type": typ,
                            }

                    layer_folder_counter += 1

                layer_folder_group_counter += 1

            self.layerHierarchyWithIds[level_id] = new_layer_folders

    diagram.DirStrucTree._addIdsToLayerHierarchy = _add_ids_to_layer_hierarchy


class CaptureDirStrucTree(diagram.DirStrucTree):
    """Generate Mermaid output in memory instead of writing a .mmd file."""

    mermaid_content = ""

    def generateFile(self) -> None:
        gen = diagram.FileGenerator(self)
        gen.buildFileBlocks()
        gen.setStyle(self.style)
        blocks = [*gen.headerBlock, *gen.rootBlock, *gen.mainBlock, *gen.style]
        self.mermaid_content = "\n".join(map(str, blocks))


_patch_dirtree_chart_duplicate_name_bug()


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def build_ignore_list() -> list[str]:
    ignore = list(config.ignore_list)
    ignore.extend(sorted(EXCLUDE_DIRS))
    return ignore


def safe_mermaid_id(node_id: str) -> str:
    if node_id == "root":
        return "root"
    return "n" + node_id.replace(".", "_")


def truncate_file_list_label(label: str) -> str:
    if "<br>" not in label:
        return label
    parts = label.split("<br>")
    if len(parts) <= MAX_FILES_IN_NODE:
        return label
    remaining = len(parts) - (MAX_FILES_IN_NODE - 1)
    visible = parts[: MAX_FILES_IN_NODE - 1]
    visible.append(f"... +{remaining} more")
    return "<br>".join(visible)


def quote_mermaid_label(label: str) -> str:
    label = truncate_file_list_label(label)
    escaped = label.replace('"', "'")
    return f'"{escaped}"'


def replace_numeric_ids(line: str, id_map: dict[str, str]) -> str:
    if not id_map:
        return line
    ordered_ids = sorted(id_map, key=len, reverse=True)
    pattern = re.compile(
        r"(?<![.\d])(" + "|".join(re.escape(node_id) for node_id in ordered_ids) + r")(?![.\d])"
    )
    return pattern.sub(lambda match: id_map[match.group(1)], line)


def quote_mermaid_labels(line: str) -> str:
    def bracket_repl(match: re.Match[str]) -> str:
        return f"[{quote_mermaid_label(match.group(1))}]"

    def paren_repl(match: re.Match[str]) -> str:
        return f"({quote_mermaid_label(match.group(1))})"

    line = re.sub(r"\[([^\]]*)\]", bracket_repl, line)
    line = re.sub(r"\(([^)]*)\)", paren_repl, line)
    return line


def mask_label_segments(line: str) -> tuple[str, list[str]]:
    labels: list[str] = []

    def save_label(match: re.Match[str]) -> str:
        labels.append(match.group(0))
        token = f"\uE000LBL{chr(65 + len(labels) - 1)}\uE001"
        return token

    masked = re.sub(r"(\[[^\]]*\]|\([^)]*\))", save_label, line)
    return masked, labels


def restore_label_segments(line: str, labels: list[str]) -> str:
    for index, label in enumerate(labels):
        token = f"\uE000LBL{chr(65 + index)}\uE001"
        if label.startswith("["):
            quoted = f"[{quote_mermaid_label(label[1:-1])}]"
        else:
            quoted = f"({quote_mermaid_label(label[1:-1])})"
        line = line.replace(token, quoted)
    return line


def sanitize_mermaid_diagram(content: str) -> str:
    """Make dirtree-chart graph output safe for GitHub and VS Code Mermaid parsers."""
    numeric_ids = NUMERIC_ID_PATTERN.findall(content)
    id_map = {node_id: safe_mermaid_id(node_id) for node_id in set(numeric_ids)}

    sanitized_lines: list[str] = []
    for line in content.splitlines():
        if line.startswith("graph ") or line.startswith("classDef "):
            sanitized_lines.append(line)
            continue
        masked_line, labels = mask_label_segments(line)
        masked_line = replace_numeric_ids(masked_line, id_map)
        sanitized_lines.append(restore_label_segments(masked_line, labels))
    return "\n".join(sanitized_lines)


def extension_key(filename: str) -> str:
    lowered = filename.lower()
    if lowered in {"dockerfile", "makefile"}:
        return "sh"
    if filename.startswith(".") and filename.count(".") == 1:
        special = filename.lstrip(".").lower()
        if special in {"gitignore", "gitattributes", "dockerignore"}:
            return "git"
    extension = Path(filename).suffix.lower().lstrip(".")
    return extension or "other"


def file_class_for_name(filename: str) -> str:
    return EXTENSION_TO_FILE_CLASS.get(extension_key(filename), "file-other")


def infer_file_class(label: str) -> str:
    parts = [part.strip() for part in label.split("<br>") if part.strip()]
    if not parts:
        return "file-other"

    file_parts = [part for part in parts if not part.startswith("... +")]
    if len(file_parts) > 1:
        classes = {file_class_for_name(name) for name in file_parts}
        if len(classes) == 1:
            return classes.pop()
        return "file-bundle"

    return file_class_for_name(file_parts[0])


def style_file_node_line(line: str, used_classes: set[str]) -> str:
    def repl(match: re.Match[str]) -> str:
        file_class = infer_file_class(match.group(1))
        used_classes.add(file_class)
        return f'["{match.group(1)}"]:::{file_class}'

    if ":::folder" in line:
        used_classes.add("folder")
    if ":::root" in line:
        used_classes.add("root")
    return QUOTED_FILE_NODE.sub(repl, line)


def build_class_def_lines(used_classes: set[str]) -> list[str]:
    ordered = ["root", "folder"]
    ordered.extend(
        sorted(
            cls
            for cls in used_classes
            if cls not in {"root", "folder"}
        )
    )
    lines: list[str] = []
    for class_name in ordered:
        if class_name in MERMAID_CLASS_STYLES:
            lines.append(f"classDef {class_name} {MERMAID_CLASS_STYLES[class_name]};")
    return lines


def apply_mermaid_styling(content: str) -> str:
    """Apply root, folder, and file-type color classes to a sanitized Mermaid graph."""
    used_classes: set[str] = set()
    styled_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("classDef "):
            continue
        if line.startswith("graph "):
            styled_lines.append(line)
            continue
        styled_lines.append(style_file_node_line(line, used_classes))

    styled_lines.extend(build_class_def_lines(used_classes))
    return "\n".join(styled_lines)


def build_mermaid_tree(directory: Path) -> str:
    tree = CaptureDirStrucTree(
        root=str(directory),
        ignore=build_ignore_list(),
        files=True,
        include_to_readme=False,
        direction="TD",
        max_folder_depth=MAX_FOLDER_DEPTH,
    )
    sanitized = sanitize_mermaid_diagram(tree.mermaid_content)
    styled = apply_mermaid_styling(sanitized)
    return f"```mermaid\n{styled}\n```"


def build_generated_block(directory: Path) -> str:
    graph = build_mermaid_tree(directory)
    return (
        f"{AUTO_START}\n"
        f"<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->\n\n"
        f"## Directory structure\n\n"
        f"<details>\n"
        f"<summary>Show directory tree diagram for `{directory.name or directory}`</summary>\n\n"
        f"{graph}\n\n"
        f"</details>\n\n"
        f"{AUTO_END}\n\n"
    )


def strip_auto_generated_blocks(content: str) -> str:
    content = re.sub(
        rf"{re.escape(AUTO_START)}.*?{re.escape(AUTO_END)}\n*",
        "",
        content,
        flags=re.DOTALL,
    )
    content = re.sub(
        rf"{re.escape(CATALOG_START)}.*?{re.escape(CATALOG_END)}\n*",
        "",
        content,
        flags=re.DOTALL,
    )
    return content


def truncate_description(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_DESCRIPTION_LENGTH:
        return cleaned
    return cleaned[: MAX_DESCRIPTION_LENGTH - 3].rstrip() + "..."


def get_shell_description(filepath: Path) -> str | None:
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None

    desc_lines: list[str] = []
    for line in content.splitlines():
        if line.startswith("#!"):
            continue
        if line.strip().startswith("#"):
            clean = line.strip().lstrip("#").strip()
            if clean and not clean.startswith("==="):
                if clean.isupper() and len(clean.split()) <= 5:
                    continue
                if clean.startswith(("FUNCTION:", "SECTION:")):
                    continue
                desc_lines.append(clean)
        elif desc_lines:
            break
    if desc_lines:
        return truncate_description(" ".join(desc_lines[:3]))
    return None


def get_powershell_description(filepath: Path) -> str | None:
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None

    match = re.search(
        r"Description:\s*(.*?)(?=\n\s*\n|\nUsage:|\nParameters:|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return truncate_description(match.group(1))

    match = re.search(
        r"\.DESCRIPTION\s+(.*?)(?=\.\w+|\s*#>|#\s*=)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        return truncate_description(match.group(1))
    return None


def get_python_description(filepath: Path) -> str | None:
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None

    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if match:
        return truncate_description(match.group(1))
    match = re.search(r"'''(.*?)'''", content, re.DOTALL)
    if match:
        return truncate_description(match.group(1))
    return None


def get_markdown_description(filepath: Path) -> str | None:
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None

    content = strip_auto_generated_blocks(content)

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return truncate_description(stripped[2:])

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("<!--", "---", "```", "* ", "- ", "#")):
            continue
        if stripped == "Auto-generated directory structure for this folder.":
            continue
        return truncate_description(stripped)
    return None


def get_html_description(filepath: Path) -> str | None:
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return None

    match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if match:
        return truncate_description(match.group(1))
    return None


def describe_directory(directory: Path) -> str:
    readme = directory / README_NAME
    if readme.exists():
        try:
            content = strip_auto_generated_blocks(readme.read_text(encoding="utf-8"))
        except OSError:
            content = ""

        title: str | None = None
        paragraph: str | None = None
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:]
            elif (
                paragraph is None
                and stripped
                and stripped != "Auto-generated directory structure for this folder."
                and not stripped.startswith(("-", "*", "#", "<!--", "---", "```"))
            ):
                paragraph = stripped

        if paragraph and (not title or title.lower() == directory.name.lower()):
            return truncate_description(paragraph)
        if title and title != "Auto-generated directory structure for this folder.":
            return truncate_description(title)

    children = [p for p in directory.iterdir() if not should_skip(p)]
    count = len(children)
    if count == 0:
        return "Empty directory."
    return f"Directory with {count} item{'s' if count != 1 else ''}."


def describe_file(filepath: Path) -> str:
    ext = filepath.suffix.lower()
    description: str | None = None

    if ext == ".sh":
        description = get_shell_description(filepath)
    elif ext == ".ps1":
        description = get_powershell_description(filepath)
    elif ext == ".py":
        description = get_python_description(filepath)
    elif ext in {".md", ".markdown"}:
        description = get_markdown_description(filepath)
    elif ext in {".html", ".htm"}:
        description = get_html_description(filepath)

    if description:
        return description

    try:
        size = filepath.stat().st_size
    except OSError:
        size = 0

    suffix = ext.lstrip(".") or "file"
    if suffix in {"md", "txt", "rst", "json", "yml", "yaml", "ini", "cfg", "toml", "xml", "html", "css", "js", "ts", "py", "sh", "ps1"}:
        kind = "text/config file"
    elif suffix in {"png", "jpg", "jpeg", "gif", "svg", "webp", "pdf"}:
        kind = "binary asset"
    else:
        kind = "file"
    return f"{kind} ({size} bytes)"


def get_entry_description(path: Path) -> str:
    if path.is_dir():
        return describe_directory(path)
    return describe_file(path)


def format_catalog_line(path: Path, indent: str) -> str:
    rel_path = path.relative_to(REPO_ROOT).as_posix()
    if path.is_dir():
        label = f"{path.name}/"
        link_target = f"{rel_path}/"
    else:
        label = path.name
        link_target = rel_path
    description = get_entry_description(path)
    return f"{indent}* [{label}]({link_target}): {description}"


def sorted_children(directory: Path) -> list[Path]:
    children = [child for child in directory.iterdir() if not should_skip(child)]
    dirs = sorted((p for p in children if p.is_dir()), key=lambda p: p.name.lower())
    files = sorted((p for p in children if p.is_file()), key=lambda p: p.name.lower())
    return [*dirs, *files]


def build_catalog_tree(directory: Path, indent: str = "") -> list[str]:
    lines: list[str] = []
    for child in sorted_children(directory):
        lines.append(format_catalog_line(child, indent))
        if child.is_dir():
            lines.extend(build_catalog_tree(child, indent + "  "))
    return lines


def section_header(name: str, path: Path) -> str:
    if name in SECTION_HEADERS:
        return SECTION_HEADERS[name]
    return f"📂 `{path.as_posix()}/`"


def build_catalog_block() -> str:
    sections: list[str] = [
        CATALOG_START,
        "<!-- This catalog is auto-generated. Do not edit directly. -->",
        "",
        "## Catalog of Tools",
        "",
        "### 📄 Repository Root (`/`)",
    ]
    for child in sorted_children(REPO_ROOT):
        sections.append(format_catalog_line(child, ""))
    sections.append("")

    top_level = sorted(
        [p for p in REPO_ROOT.iterdir() if p.is_dir() and not should_skip(p)],
        key=lambda p: p.name.lower(),
    )
    for path in top_level:
        sections.append(f"### {section_header(path.name, path)}")
        sections.extend(build_catalog_tree(path))
        sections.append("")

    sections.append(CATALOG_END)
    sections.append("")
    return "\n".join(sections)


def update_root_catalog(readme_path: Path) -> None:
    content = readme_path.read_text(encoding="utf-8")
    catalog_block = build_catalog_block()

    if CATALOG_START in content and CATALOG_END in content:
        pattern = re.compile(
            rf"{re.escape(CATALOG_START)}.*?{re.escape(CATALOG_END)}\n*",
            re.DOTALL,
        )
        new_content = pattern.sub(catalog_block, content)
    elif "## Catalog of Tools" in content:
        pattern = re.compile(
            r"## Catalog of Tools\n\n.*?(?=\n---\n|\n## ⚠️ Disclaimer)",
            re.DOTALL,
        )
        new_content = pattern.sub(catalog_block.rstrip(), content, count=1)
    else:
        disclaimer_pattern = re.compile(r"\n---\n\n## ⚠️ Disclaimer")
        if disclaimer_pattern.search(content):
            new_content = disclaimer_pattern.sub(
                f"\n\n{catalog_block}---\n\n## ⚠️ Disclaimer",
                content,
                count=1,
            )
        else:
            new_content = content.rstrip() + "\n\n" + catalog_block

    readme_path.write_text(new_content, encoding="utf-8")


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

    root_readme = REPO_ROOT / README_NAME
    if root_readme.exists():
        update_root_catalog(root_readme)
        print("Updated catalog in: README.md")

    print("\nFinished generating Mermaid README diagrams for every directory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
