#!/usr/bin/env bash
# Regenerates the auto-generated section of README.md: directory structure
# (mermaid diagram) + recent commit log with changed files. Everything above
# the START marker is hand-written and left untouched.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
README="README.md"
START="<!-- AUTO-GENERATED:START -->"
END="<!-- AUTO-GENERATED:END -->"
COMMIT_COUNT=8

[[ -f "$README" ]] || printf '# %s\n\n## About\n\nTODO: describe this repo.\n\n%s\n%s\n' \
  "$(basename "$REPO_ROOT")" "$START" "$END" > "$README"

grep -qF "$START" "$README" || { printf '\n%s\n%s\n' "$START" "$END" >> "$README"; }

# --- mermaid directory diagram (2 levels, skip noise dirs) ---
mermaid_body="$(
  {
    echo '```mermaid'
    echo 'graph TD'
    echo "    root[$(basename "$REPO_ROOT")]"
    find . -mindepth 1 -maxdepth 2 \
      \( -path ./.git -o -path ./node_modules -o -path ./.venv -o -path ./dist -o -path ./build \) -prune -o \
      -type d -print | sed 's|^\./||' | sort | while read -r d; do
        parent="$(dirname "$d")"
        node_id="$(echo "$d" | tr './ -' '____')"
        parent_id="$(echo "$parent" | tr './ -' '____')"
        [[ "$parent" == "." ]] && parent_id="root"
        parent_label="${parent##*/}"
        [[ "$parent" == "." ]] && parent_label="$(basename "$REPO_ROOT")"
        echo "    ${parent_id}[${parent_label}] --> ${node_id}[$(basename "$d")]"
      done
    echo '```'
  }
)"
[[ -z "$(find . -mindepth 1 -maxdepth 2 -type d ! -path ./.git -print -quit 2>/dev/null)" ]] && \
  mermaid_body='```mermaid
graph TD
    root[repo] --> flat[flat file layout, no subdirectories yet]
```'

# --- recent commits with changed files ---
if git rev-parse HEAD >/dev/null 2>&1; then
  commits_body="$( { git log -n "$COMMIT_COUNT" --pretty=format:'%n### %h — %s (%ad)' --date=short; echo; } | while IFS= read -r line; do
    echo "$line"
    if [[ "$line" == "### "* ]]; then
      hash="$(echo "$line" | sed -E 's/^### ([a-f0-9]+).*/\1/')"
      git diff-tree --no-commit-id --name-status -r --root "$hash" | sed 's/^/- `/; s/\t/` /'
    fi
  done)"
else
  commits_body="_no commits yet_"
fi

tmp="$(mktemp)"
awk -v start="$START" -v end="$END" '
  BEGIN{skip=0}
  index($0, start){print; skip=1; next}
  index($0, end){skip=0}
  skip{next}
  {print}
' "$README" > "$tmp"

# insert new body right after START (which awk already printed) and before END
awk -v start="$START" -v end="$END" -v mermaid="$mermaid_body" -v commits="$commits_body" '
  { print }
  index($0, start) {
    print ""
    print "## Structure"
    print ""
    print mermaid
    print ""
    print "## Recent changes"
    print commits
    print ""
  }
' "$tmp" > "$README"
rm -f "$tmp"

git add "$README"
