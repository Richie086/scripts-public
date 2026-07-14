#!/usr/bin/env python3
"""Minimal markdown -> Atlassian Document Format converter for simple docs
(headers, paragraphs, bold, inline code). No tables/lists support needed here."""
import json
import re
import sys

def parse_inline(text):
    tokens = []
    pattern = re.compile(r"(\*\*.+?\*\*|`.+?`)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            tokens.append({"type": "text", "text": text[pos:m.start()]})
        chunk = m.group(0)
        if chunk.startswith("**"):
            tokens.append({"type": "text", "text": chunk[2:-2], "marks": [{"type": "strong"}]})
        elif chunk.startswith("`"):
            tokens.append({"type": "text", "text": chunk[1:-1], "marks": [{"type": "code"}]})
        pos = m.end()
    if pos < len(text):
        tokens.append({"type": "text", "text": text[pos:]})
    if not tokens:
        tokens.append({"type": "text", "text": text})
    return tokens

def md_to_adf(md_text):
    lines = md_text.split("\n")
    content = []
    buffer = []

    def flush():
        if buffer:
            text = " ".join(buffer).strip()
            if text:
                content.append({"type": "paragraph", "content": parse_inline(text)})
            buffer.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush()
            level = len(m.group(1))
            content.append({
                "type": "heading",
                "attrs": {"level": level},
                "content": parse_inline(m.group(2))
            })
            continue
        buffer.append(stripped)
    flush()

    return {"type": "doc", "version": 1, "content": content}

if __name__ == "__main__":
    md_path = sys.argv[1]
    with open(md_path, "r") as f:
        md_text = f.read()
    print(json.dumps({"fields": {"description": md_to_adf(md_text)}}))
