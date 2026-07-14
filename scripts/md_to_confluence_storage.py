#!/usr/bin/env python3
"""Minimal markdown -> Confluence storage format (XHTML) converter for simple docs."""
import html
import re
import sys

def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text

def md_to_storage(md_text):
    lines = md_text.split("\n")
    out = []
    buffer = []

    def flush():
        if buffer:
            text = " ".join(buffer).strip()
            if text:
                out.append(f"<p>{inline(text)}</p>")
            buffer.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            flush()
            level = min(len(m.group(1)), 6)
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            continue
        buffer.append(stripped)
    flush()
    return "\n".join(out)

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        print(md_to_storage(f.read()))
