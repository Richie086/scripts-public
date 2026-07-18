#!/usr/bin/env bash
# Retrofit an existing repository to the 4-folder organization layout.
# Usage: ./retrofit.sh <existing-repo-path>
set -euo pipefail

TARGET_DIR="${1:?usage: retrofit.sh <existing-repo-path>}"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$TARGET_DIR" ]; then
  echo "Directory $TARGET_DIR does not exist." >&2
  exit 1
fi

echo "Retrofitting repository in $TARGET_DIR..."
cd "$TARGET_DIR"

# Create the 4 folders
mkdir -p docs scripts frontend backend

# Install the Cursor rule
mkdir -p .cursor/rules/global-rules
cp "$TEMPLATE_DIR/shared/.cursor/rules/global-rules/workspace-organization-always.mdc" .cursor/rules/global-rules/

# Distribute placeholder files where appropriate
for dir in docs scripts frontend backend; do
  if [ -z "$(ls -A "$dir" | grep -v "\.mdc" || true)" ]; then
    cp "$TEMPLATE_DIR/shared/$dir/README.md" "$dir/"
    echo "Placed README placeholder in $dir/"
  fi
done

# Perform dynamic migrations depending on layout
# 1. FastAPI/Python migration
if [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  echo "Detected Python layout. Moving Python files to backend/..."
  # Move source code if in src/
  if [ -d src ]; then
    mkdir -p backend/src
    mv src/* backend/src/ 2>/dev/null || true
    rmdir src 2>/dev/null || true
  fi
  # Move tests if in tests/
  if [ -d tests ]; then
    mkdir -p backend/tests
    mv tests/* backend/tests/ 2>/dev/null || true
    rmdir tests 2>/dev/null || true
  fi
  # Move python files in root (except scrape.py)
  for f in *.py; do
    if [ -f "$f" ] && [ "$f" != "scrape.py" ]; then
      mv "$f" backend/
    fi
  done
  # Move config files
  for f in pyproject.toml requirements.txt requirements-dev.txt Makefile; do
    if [ -f "$f" ]; then
      mv "$f" backend/
    fi
  done
fi

# 2. Node-Vite layout migration
if [ -f package.json ] && [ -f vite.config.ts ] || [ -f vite.config.js ]; then
  echo "Detected Node-Vite layout. Moving web files to frontend/..."
  # Move code
  for dir in src public; do
    if [ -d "$dir" ]; then
      mv "$dir" frontend/
    fi
  done
  # Move configuration
  for f in package.json tsconfig.json vite.config.ts vite.config.js index.html Makefile; do
    if [ -f "$f" ]; then
      mv "$f" frontend/
    fi
  done
fi

# 3. Shell script layout migration
# Move loose shell files (except run.sh, bootstrap.sh, retrofit.sh) to scripts/
for f in *.sh; do
  if [ -f "$f" ] && [ "$f" != "run.sh" ] && [ "$f" != "bootstrap.sh" ] && [ "$f" != "retrofit.sh" ]; then
    mkdir -p scripts/bash
    mv "$f" scripts/bash/
  fi
done

# Stage all files
git add -A || true
echo "Retrofit complete for $TARGET_DIR."
