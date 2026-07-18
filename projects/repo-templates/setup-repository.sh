#!/usr/bin/env bash
# ==============================================================================
# NAME: setup-repository.sh
# DESCRIPTION: Automates scaffolding of new project repositories matching the
#              standardized 4-folder blueprint (docs/, scripts/, frontend/, backend/).
#              Provides support for four development stacks (Python FastAPI, Node-Vite
#              React, Shell, and PowerShell Core), including automated Makefiles,
#              unit test suites, Cursor rule enforcement, gitleaks secrets scanning,
#              pre-commit validation hooks, and GitHub remote integration.
#
# DESIGN PATHS:
#   - Dry-Run by Default: Safe evaluation mode showing planned modifications.
#   - Portability: Zero hardcoded directories, personal credentials, or LAN IPs.
#   - Automated Autodocs: Automated initial commit triggers post-commit hook
#     scaffolding README layout graphs and commit change logs.
#
# USAGE:
#   ./setup-repository.sh <repo-name> <python|node-vite|shell|powershell> [options]
#
# OPTIONS:
#   Run ./setup-repository.sh --help for all configuration flags.
# ==============================================================================
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Global defaults
VISIBILITY="private"
LICENSE_TYPE="gpl3"
INTERACTIVE=true
DRY_RUN=true
TOPIC=""
STACK=""
REPO_NAME=""

show_help() {
  cat <<EOF
Standardized Repository Bootstrapper

Usage:
  $(basename "${0}") <repo-name> <python|node-vite|shell|powershell> [options]

Arguments:
  <repo-name>      Name of the repository to create.
  <stack-type>     Template stack: python, node-vite, shell, or powershell.

Options:
  -h, --help       Show this help message and exit.
  -y, --yes        Non-interactive mode (auto-confirm all prompts).
  --write, --apply Actually execute the scaffolding (writes files and syncs GitHub).
  --dry-run        Dry run mode (default; show planned actions without writing).
  --public         Scaffold as a public GitHub repository.
  --private        Scaffold as a private GitHub repository (default).
  --license TYPE   License for public repos: mit, gpl3, apache2 (default: gpl3).
  --topic TOPIC    Add topic tag to the created GitHub repository.
EOF
}

# Parse options
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      show_help
      exit 0
      ;;
    -y|--yes)
      INTERACTIVE=false
      shift
      ;;
    --public)
      VISIBILITY="public"
      shift
      ;;
    --private)
      VISIBILITY="private"
      shift
      ;;
    --write|--apply)
      DRY_RUN=false
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --license)
      LICENSE_TYPE="${2:?--license requires a value}"
      shift 2
      ;;
    --topic)
      TOPIC="${2:?--topic requires a value}"
      shift 2
      ;;
    -*)
      echo "Error: Unknown option $1" >&2
      show_help >&2
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#POSITIONAL_ARGS[@]} -lt 2 ]]; then
  echo "Error: Missing required arguments." >&2
  show_help >&2
  exit 1
fi

REPO_NAME="${POSITIONAL_ARGS[0]}"
STACK="${POSITIONAL_ARGS[1]}"

case "$STACK" in
  python|node-vite|shell|powershell) ;;
  *) echo "Error: Unknown stack $STACK (must be python, node-vite, shell, or powershell)" >&2; exit 1 ;;
esac

# Resolve paths
DEST="$HOME/repositories/projects/$REPO_NAME"

if [[ -e "$DEST" ]]; then
  echo "Error: Refusing to overwrite existing path: $DEST" >&2
  exit 1
fi

# Resolve GitHub user dynamically (no static linking)
GITHUB_USER="${GITHUB_USER:-$(gh api user -q .login 2>/dev/null || echo "")}"
if [[ -z "$GITHUB_USER" ]]; then
  GITHUB_USER="$(git config user.name || echo "Owner" | tr ' ' '_')"
fi

# ==================================================
# Environment Review Banner
# ==================================================
echo "=================================================="
echo "          SCAFFOLD ENVIRONMENT SUMMARY            "
echo "=================================================="
echo "Project Name:   $REPO_NAME"
echo "Target Location: $DEST"
echo "Stack Template: $STACK"
echo "Visibility:     $VISIBILITY"
echo "License Type:   $LICENSE_TYPE"
echo "GitHub User:    $GITHUB_USER"
echo "Git Remote URL: git@github.com:$GITHUB_USER/$REPO_NAME.git"
echo "=================================================="

if [[ "$DRY_RUN" == "true" ]]; then
  echo "--- DRY RUN MODE (No changes will be written to disk or GitHub) ---"
  echo "Would create folder: $DEST"
  echo "Would copy configurations: Makefile, .gitleaks.toml, .pre-commit-config.yaml, SECURITY.md, CONTRIBUTING.md, .editorconfig, .gitignore"
  echo "Would copy Cursor rule enforcer: .cursor/rules/global-rules/workspace-organization-always.mdc"
  if [[ "$VISIBILITY" == "public" ]]; then
    echo "Would create public LICENSE type: $LICENSE_TYPE"
  fi
  echo "Would scaffold stack structure: $STACK"
  case "$STACK" in
    python)
      echo "  - Create: backend/src/\$(echo $REPO_NAME | tr '-' '_')/main.py"
      echo "  - Create: backend/tests/test_main.py"
      echo "  - Create: backend/pyproject.toml"
      echo "  - Create: backend/Makefile"
      echo "  - Create: .github/workflows/test.yml"
      ;;
    node-vite)
      echo "  - Create: frontend/package.json"
      echo "  - Create: frontend/tsconfig.json"
      echo "  - Create: frontend/vite.config.ts"
      echo "  - Create: frontend/index.html"
      echo "  - Create: frontend/src/main.tsx"
      echo "  - Create: frontend/src/App.tsx"
      echo "  - Create: frontend/src/index.css"
      echo "  - Create: frontend/Makefile"
      echo "  - Create: .github/workflows/test.yml"
      ;;
    shell)
      echo "  - Create: scripts/bash/example.sh"
      echo "  - Create: scripts/python/example.py"
      echo "  - Create: scripts/tests/test_example.bats"
      echo "  - Create: scripts/Makefile"
      echo "  - Create: .github/workflows/test.yml"
      ;;
    powershell)
      echo "  - Create: scripts/powershell/example.ps1"
      echo "  - Create: scripts/tests/example.Tests.ps1"
      echo "  - Create: scripts/Makefile"
      echo "  - Create: .github/workflows/test.yml"
      ;;
  esac
  echo "Would run initial commit to trigger autodoc README."
  if command -v gh >/dev/null 2>&1; then
    echo "Would create GitHub repository: git@github.com:$GITHUB_USER/$REPO_NAME.git"
  fi
  echo "--- DRY RUN COMPLETE ---"
  exit 0
fi

if [[ "$INTERACTIVE" == "true" ]]; then
  read -r -p "Proceed with scaffolding? (y/N): " CONFIRM
  if [[ ! "$CONFIRM" =~ ^[yY]([eE][sS])?$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# Create target directories
mkdir -p "$DEST/docs" "$DEST/scripts" "$DEST/frontend" "$DEST/backend"

# Copy shared configurations
cp "$TEMPLATE_DIR/shared/Makefile" "$DEST/"
cp "$TEMPLATE_DIR/shared/.gitleaks.toml" "$DEST/"
cp "$TEMPLATE_DIR/shared/.pre-commit-config.yaml" "$DEST/"
cp "$TEMPLATE_DIR/shared/SECURITY.md" "$DEST/"
cp "$TEMPLATE_DIR/shared/CONTRIBUTING.md" "$DEST/"
mkdir -p "$DEST/.github/workflows"
cp "$TEMPLATE_DIR/shared/.github/workflows/secret-scan.yml" "$DEST/.github/workflows/"
cp "$TEMPLATE_DIR/shared/.editorconfig" "$DEST/"
cat "$TEMPLATE_DIR/shared/gitignore.common" > "$DEST/.gitignore"
if [[ -f "$TEMPLATE_DIR/$STACK/gitignore.extra" ]]; then
  echo >> "$DEST/.gitignore"
  cat "$TEMPLATE_DIR/$STACK/gitignore.extra" >> "$DEST/.gitignore"
fi

# Copy Cursor rules structure
mkdir -p "$DEST/.cursor/rules/global-rules"
cp "$TEMPLATE_DIR/shared/.cursor/rules/global-rules/workspace-organization-always.mdc" "$DEST/.cursor/rules/global-rules/"

# Setup license if public
if [[ "$VISIBILITY" == "public" ]]; then
  YEAR="$(date +%Y)"
  AUTHOR_NAME="$(git config user.name || echo "Owner")"
  
  case "$LICENSE_TYPE" in
    mit)
      cat > "$DEST/LICENSE" <<EOF
Copyright (c) $YEAR $AUTHOR_NAME

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
      ;;
    apache2)
      cat > "$DEST/LICENSE" <<EOF
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   Copyright $YEAR $AUTHOR_NAME

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
EOF
      ;;
    gpl3|*)
      if [[ -f "$TEMPLATE_DIR/shared/LICENSE-GPL3" ]]; then
        { printf 'Copyright (C) %s %s\n\n' "$YEAR" "$AUTHOR_NAME"; cat "$TEMPLATE_DIR/shared/LICENSE-GPL3"; } > "$DEST/LICENSE"
      else
        echo "GPL3 source not found on disk, writing fallback notice."
        echo "Copyright (C) $YEAR $AUTHOR_NAME (GPL-3.0 License)" > "$DEST/LICENSE"
      fi
      ;;
  esac
fi

# Copy Dependabot
case "$STACK" in
  python) DEPENDABOT_ECOSYSTEM="pip" ;;
  node-vite) DEPENDABOT_ECOSYSTEM="npm" ;;
  shell|powershell) DEPENDABOT_ECOSYSTEM="" ;;
esac
if [[ -n "$DEPENDABOT_ECOSYSTEM" ]]; then
  sed "s/__ECOSYSTEM__/$DEPENDABOT_ECOSYSTEM/" "$TEMPLATE_DIR/shared/dependabot.yml" > "$DEST/.github/dependabot.yml"
else
  cat > "$DEST/.github/dependabot.yml" <<'DEP_EOF'
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
DEP_EOF
fi

touch "$DEST/.env.example"

# README auto-update (mermaid structure diagram + recent commits)
cp "$TEMPLATE_DIR/shared/scripts/update-readme.sh" "$DEST/scripts/"
chmod +x "$DEST/scripts/update-readme.sh"

# Stack layout & placeholder distribution
case "$STACK" in
  python)
    PKG="$(echo "$REPO_NAME" | tr '-' '_')"
    mkdir -p "$DEST/backend/src/$PKG" "$DEST/backend/tests"
    
    # Copy source boilerplates
    cp "$TEMPLATE_DIR/python/backend/src/main.py" "$DEST/backend/src/$PKG/main.py"
    cp "$TEMPLATE_DIR/python/backend/tests/test_main.py" "$DEST/backend/tests/test_main.py"
    touch "$DEST/backend/src/$PKG/__init__.py" "$DEST/backend/tests/__init__.py"
    
    # Configure pyproject and Makefile
    sed "s/__REPO_NAME__/$REPO_NAME/" "$TEMPLATE_DIR/python/pyproject.toml.tmpl" > "$DEST/backend/pyproject.toml"
    cp "$TEMPLATE_DIR/python/Makefile" "$DEST/backend/"
    cp "$TEMPLATE_DIR/python/test.yml" "$DEST/.github/workflows/test.yml"
    
    # Placeholders for unused folders
    cp "$TEMPLATE_DIR/shared/docs/README.md" "$DEST/docs/"
    cp "$TEMPLATE_DIR/shared/frontend/README.md" "$DEST/frontend/"
    ;;
    
  node-vite)
    mkdir -p "$DEST/frontend/src/components" "$DEST/frontend/src/lib" "$DEST/frontend/public"
    
    # Copy boilerplates
    sed "s/__REPO_NAME__/$REPO_NAME/" "$TEMPLATE_DIR/node-vite/package.json.tmpl" > "$DEST/frontend/package.json"
    cp "$TEMPLATE_DIR/node-vite/tsconfig.json" "$DEST/frontend/"
    cp "$TEMPLATE_DIR/node-vite/vite.config.ts" "$DEST/frontend/"
    cp "$TEMPLATE_DIR/node-vite/index.html" "$DEST/frontend/"
    cp "$TEMPLATE_DIR/node-vite/src/main.tsx" "$DEST/frontend/src/"
    cp "$TEMPLATE_DIR/node-vite/src/App.tsx" "$DEST/frontend/src/"
    cp "$TEMPLATE_DIR/node-vite/src/index.css" "$DEST/frontend/src/"
    cp "$TEMPLATE_DIR/node-vite/Makefile" "$DEST/frontend/"
    cp "$TEMPLATE_DIR/node-vite/test.yml" "$DEST/.github/workflows/test.yml"
    
    # Placeholders for unused folders
    cp "$TEMPLATE_DIR/shared/docs/README.md" "$DEST/docs/"
    cp "$TEMPLATE_DIR/shared/scripts/README.md" "$DEST/scripts/"
    cp "$TEMPLATE_DIR/shared/backend/README.md" "$DEST/backend/"
    ;;
    
  shell)
    mkdir -p "$DEST/scripts/bash" "$DEST/scripts/python" "$DEST/scripts/tests"
    
    # Copy boilerplates
    cp "$TEMPLATE_DIR/shell/scripts/bash/example.sh" "$DEST/scripts/bash/example.sh"
    chmod +x "$DEST/scripts/bash/example.sh"
    cp "$TEMPLATE_DIR/shell/scripts/python/example.py" "$DEST/scripts/python/example.py"
    chmod +x "$DEST/scripts/python/example.py"
    cp "$TEMPLATE_DIR/shell/scripts/tests/test_example.bats" "$DEST/scripts/tests/test_example.bats"
    cp "$TEMPLATE_DIR/shell/Makefile" "$DEST/scripts/"
    cp "$TEMPLATE_DIR/shell/test.yml" "$DEST/.github/workflows/test.yml"
    
    # Placeholders for unused folders
    cp "$TEMPLATE_DIR/shared/docs/README.md" "$DEST/docs/"
    cp "$TEMPLATE_DIR/shared/frontend/README.md" "$DEST/frontend/"
    cp "$TEMPLATE_DIR/shared/backend/README.md" "$DEST/backend/"
    ;;
    
  powershell)
    mkdir -p "$DEST/scripts/powershell" "$DEST/scripts/tests"
    
    # Copy boilerplates
    cp "$TEMPLATE_DIR/powershell/scripts/powershell/example.ps1" "$DEST/scripts/powershell/example.ps1"
    cp "$TEMPLATE_DIR/powershell/scripts/tests/example.Tests.ps1" "$DEST/scripts/tests/example.Tests.ps1"
    cp "$TEMPLATE_DIR/powershell/Makefile" "$DEST/scripts/"
    cp "$TEMPLATE_DIR/powershell/test.yml" "$DEST/.github/workflows/test.yml"
    
    # Placeholders for unused folders
    cp "$TEMPLATE_DIR/shared/docs/README.md" "$DEST/docs/"
    cp "$TEMPLATE_DIR/shared/frontend/README.md" "$DEST/frontend/"
    cp "$TEMPLATE_DIR/shared/backend/README.md" "$DEST/backend/"
    ;;
esac

# Create base README
cat > "$DEST/README.md" <<README_EOF
# $REPO_NAME

## About

TODO: describe this repo.

<!-- AUTO-GENERATED:START -->
<!-- AUTO-GENERATED:END -->
README_EOF

# Initialize git repository
cd "$DEST"
git init -q -b main
cp "$TEMPLATE_DIR/shared/hooks/post-commit" .git/hooks/post-commit
chmod +x .git/hooks/post-commit
git add -A

# Install pre-commit hooks locally if available
if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install -q || echo "note: pre-commit hooks installation failed."
fi

# Automated first commit to populate README autodoc structure via hook
git commit -m "Initial scaffold of repository templates" -q

echo "Local repository successfully scaffolded at $DEST"

# ==================================================
# GitHub Remote Creation
# ==================================================
GH_SETUP=false
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    if [[ "$INTERACTIVE" == "true" ]]; then
      read -r -p "Create and push to GitHub repository $GITHUB_USER/$REPO_NAME? (y/N): " GH_CONFIRM
      if [[ "$GH_CONFIRM" =~ ^[yY]([eE][sS])?$ ]]; then
        GH_SETUP=true
      fi
    else
      GH_SETUP=true
    fi
  fi
fi

if [[ "$GH_SETUP" == "true" ]]; then
  echo "Creating GitHub repository git@github.com:$GITHUB_USER/$REPO_NAME.git..."
  # gh repo create command supports SSH url when using ssh protocol configuration or git@github.com format
  gh repo create "$GITHUB_USER/$REPO_NAME" --"$VISIBILITY" --source=. --remote=origin --push -y
  if [[ -n "$TOPIC" ]]; then
    gh repo edit "$GITHUB_USER/$REPO_NAME" --add-topic "$TOPIC" >/dev/null
  fi
  echo "GitHub repository successfully created and pushed!"
else
  echo "To manually push to GitHub later, run:"
  echo "  cd $DEST"
  echo "  gh repo create $GITHUB_USER/$REPO_NAME --$VISIBILITY --source=. --remote=origin --push"
fi

# Run background toolchain installation
if [[ "$INTERACTIVE" == "false" ]]; then
  # Non-interactive mode, skip installing to speed up tests
  echo "Skipping background dependency installations in non-interactive mode."
else
  # Background installations
  case "$STACK" in
    python)
      if command -v python3 >/dev/null 2>&1; then
        echo "Starting python virtual environment setup in the background..."
        ( cd "$DEST/backend" && make setup >/dev/null 2>&1 ) &
      fi
      ;;
    node-vite)
      if command -v npm >/dev/null 2>&1; then
        echo "Starting npm package installation in the background..."
        ( cd "$DEST/frontend" && make setup >/dev/null 2>&1 ) &
      fi
      ;;
  esac
fi

echo "Done: $REPO_NAME ($STACK, $VISIBILITY)"
