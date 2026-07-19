"""Entry media/attachment helpers for Idea Forge."""

from __future__ import annotations

import mimetypes
import re
import uuid
from pathlib import Path

MEDIA_KINDS = [
    ("image", "Images"),
    ("audio", "Audio"),
    ("pdf", "PDF"),
    ("word", "Word"),
    ("html", "HTML"),
    ("css", "CSS"),
    ("markdown", "Markdown"),
    ("markup", "Markup"),
    ("config", "Config"),
    ("other", "Other"),
]
MEDIA_KIND_LABELS = dict(MEDIA_KINDS)

EXT_TO_KIND = {
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",
    ".bmp": "image",
    ".ico": "image",
    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".m4a": "audio",
    ".flac": "audio",
    ".aac": "audio",
    ".pdf": "pdf",
    ".doc": "word",
    ".docx": "word",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".md": "markdown",
    ".markdown": "markdown",
    ".xml": "markup",
    ".xsl": "markup",
    ".xsd": "markup",
    ".json": "config",
    ".yaml": "config",
    ".yml": "config",
    ".toml": "config",
    ".ini": "config",
    ".conf": "config",
    ".cfg": "config",
    ".env": "config",
    ".properties": "config",
}

ALLOWED_EXTENSIONS = set(EXT_TO_KIND) | {".txt", ".log"}
TEXT_KINDS = {"html", "css", "markdown", "markup", "config", "other"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_INSERT_CHARS = 50_000


def safe_filename(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^\w.\- ()\[\]]+", "_", base).strip("._ ")
    return (base or "file")[:180]


def detect_kind(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in EXT_TO_KIND:
        return EXT_TO_KIND[ext]
    if ext in {".txt", ".log"}:
        return "other"
    return "other"


def is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def guess_mime(filename: str) -> str:
    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def store_path(files_dir: Path, entry_id: int, stored_name: str) -> Path:
    folder = files_dir / str(entry_id)
    folder.mkdir(parents=True, exist_ok=True)
    return folder / stored_name


def new_stored_name(original: str) -> str:
    ext = Path(original).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


def notes_snippet(
    *,
    kind: str,
    original_name: str,
    raw_url: str,
    text_content: str | None = None,
) -> str:
    """Markdown snippet to append into entry notes."""
    lines = [f"\n\n### Attachment: {original_name}\n"]
    if kind == "image":
        lines.append(f"![{original_name}]({raw_url})\n")
    elif kind == "audio":
        lines.append(f"[{original_name}]({raw_url})\n")
        lines.append(f'<audio controls src="{raw_url}"></audio>\n')
    elif kind in TEXT_KINDS and text_content is not None:
        fence = "markdown" if kind == "markdown" else kind if kind != "other" else "text"
        if kind == "config":
            # pick language from extension
            ext = Path(original_name).suffix.lower().lstrip(".")
            fence = {"yml": "yaml", "yaml": "yaml", "json": "json", "toml": "toml", "xml": "xml"}.get(
                ext, "text"
            )
        clipped = text_content[:MAX_INSERT_CHARS]
        if len(text_content) > MAX_INSERT_CHARS:
            clipped += "\n…(truncated)…"
        lines.append(f"```{fence}\n{clipped.rstrip()}\n```\n")
        lines.append(f"[Open file]({raw_url})\n")
    else:
        lines.append(f"[{original_name}]({raw_url})\n")
    return "".join(lines)


def group_attachments(rows: list[dict]) -> dict[str, list[dict]]:
    grouped = {key: [] for key, _ in MEDIA_KINDS}
    for row in rows:
        kind = row.get("media_kind") or "other"
        grouped.setdefault(kind, []).append(row)
    return {k: v for k, v in grouped.items() if v}
