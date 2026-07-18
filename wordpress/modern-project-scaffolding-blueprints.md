Developing software across multiple programming languages and environments can quickly lead to a chaotic mess of disorganized repositories. When every project uses a different directory layout, it becomes challenging to automate deployment pipelines, integrate linters, run unit tests, and transition between frontend and backend code. To solve this problem, we created the **Standardized 4-Folder Project Blueprint**, a structural architecture that organizes every repository into four high-level directories: `docs/`, `scripts/`, `frontend/`, and `backend/`. 

To automate this workflow and retrofit existing systems, we developed two powerful shell utilities: `bootstrap.sh` (for scaffolding new projects) and `retrofit.sh` (for reorganizing existing projects). 

In this comprehensive guide, we will walk through the design philosophy, standard directories, template stacks (React, Python, Bash, and PowerShell), automated linting and unit testing suites, and the detailed implementations of these two automation utilities.

---

## Part 1: The Design Philosophy of the 4-Folder Blueprint

Many projects fail to maintain a clean codebase not because of poor coding, but due to structural rot. Directory layout plays a vital role in keeping files where they belong. The 4-Folder Project Blueprint establishes a clean separation of concerns at the root level of every repository:

*   **`docs/` (Documentation)**: Holds specifications, requirements, architecture designs, planning markdown documents, and logs. It serves as the single source of truth for project design and roadmap.
*   **`scripts/` (DevOps & Helpers)**: Contains automation scripts, database migration scripts, orchestration tools, and local utilities. Under `scripts/`, files are grouped strictly by extension or stack (e.g. `scripts/bash/`, `scripts/python/`, `scripts/powershell/`, `scripts/tests/`).
*   **`frontend/` (User Interfaces)**: Houses all user interface client code, static assets, HTML/CSS layouts, and React/Vite development stacks.
*   **`backend/` (Server APIs & Business Logic)**: Contains backend server logic, databases, API servers (like FastAPI), configuration managers, and business workflows.

By separating the user interface, server logic, operations scripts, and project documentation into these four folders, any developer (or AI coding assistant) can immediately navigate the repository and know exactly where files should live.

---

## Part 2: Enforcing Directory Standards Globally

To prevent repository rot, we must enforce these standards automatically. We achieve this by integrating an enforcer rule file inside the project's local Cursor rules: `.cursor/rules/global-rules/workspace-organization-always.mdc`. 

This rule file uses the following configuration to guide AI assistants to respect the boundary rules:

```markdown
---
description: Always enforce the standardized 4-folder structure (docs/, scripts/, frontend/, backend/) in this repository.
globs: *
alwaysApply: true
---
# Workspace Organization

## Critical Rules
- Every file created or moved must reside in one of the four main folders:
  - `docs/`: Specifications, logs, markdown planning files, and guides.
  - `scripts/`: Devops, utility, database, and automation scripts.
  - `frontend/`: Web app code, assets, and UI components.
  - `backend/`: Server APIs, business logic, and databases.
- If a folder is empty, preserve it with a placeholder README.md explaining its purpose.
- In utility/scripts repositories, subdirectories under `scripts/` must group files by extension (e.g. `scripts/bash/`, `scripts/python/`).
```

By keeping this rule active, we establish an automated guardrail that keeps the file layout standardized.

---

## Part 3: Deep Dive into the Stack Templates

A great bootstrapping tool should never create empty folders. Instead, it must scaffold a fully functioning, buildable start application with pre-configured linter and test suites. We created templates for four distinct stack types.

### 1. Python Stack (FastAPI Backend API)

The Python stack focuses on standard API development. When bootstrapped, it sets up:
*   A FastAPI backend application inside `backend/src/`.
*   A testing suite using `pytest` inside `backend/tests/`.
*   Code linting and formatting configured via `ruff`.
*   A local dependency installer `Makefile`.
*   A `.github/workflows/test.yml` runner.

#### Python `pyproject.toml.tmpl` Configuration
```toml
[project]
name = "__REPO_NAME__"
version = "0.1.0"
description = ""
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn>=0.30.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.4.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

#### Python `backend/src/main.py` Boilerplate
```python
import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="Python App API",
    description="A boilerplate Python FastAPI backend API.",
    version="0.1.0"
)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "api"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

#### Python `backend/tests/test_main.py` Suite
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "api"}
```

#### Python `backend/Makefile` Commands
```makefile
.PHONY: setup lint test run

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -e .[dev]

lint:
	. .venv/bin/activate && ruff check .

test:
	. .venv/bin/activate && pytest

run:
	. .venv/bin/activate && python src/main.py
```

---

### 2. Node-Vite Stack (React + TypeScript Frontend)

The React stack sets up a gorgeous dark-mode web application dashboard aligned with modern design aesthetics (Dracula/Nord theme variables).

#### Node-Vite `package.json.tmpl`
```json
{
  "name": "__REPO_NAME__",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@typescript-eslint/eslint-plugin": "^7.15.0",
    "@typescript-eslint/parser": "^7.15.0",
    "@vitejs/plugin-react": "^4.3.1",
    "eslint": "^8.57.0",
    "typescript": "^5.2.2",
    "vite": "^5.3.4"
  }
}
```

#### Node-Vite `frontend/src/App.tsx`
```tsx
import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="container">
      <header className="header">
        <h1>Welcome to Your New Project</h1>
        <p className="subtitle">Scaffolded with standard 4-folder blueprint</p>
      </header>

      <main className="main-content">
        <div className="card">
          <h2>Interactive State Check</h2>
          <p>Click the button below to verify React state transitions are active:</p>
          <button className="btn" onClick={() => setCount((c) => c + 1)}>
            Count is {count}
          </button>
        </div>

        <div className="card">
          <h2>Workspace Design System</h2>
          <ul className="folder-list">
            <li><strong>📂 docs/</strong> — Specifications and guides</li>
            <li><strong>📂 scripts/</strong> — DevOps and helpers</li>
            <li><strong>📂 frontend/</strong> — UI client code (Vite + React)</li>
            <li><strong>📂 backend/</strong> — API servers and databases</li>
          </ul>
        </div>
      </main>

      <footer className="footer">
        <p>Built with ❤️ and Antigravity</p>
      </footer>
    </div>
  )
}

export default App
```

#### Node-Vite `frontend/src/index.css` (Nord Styling)
```css
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;

  /* Nord/Dracula Palette */
  --bg-primary: #2e3440;
  --bg-elevated: #3b4252;
  --text-primary: #eceff4;
  --text-secondary: #d8dee9;
  --border: #4c566a;
  --green: #a3be8c;
  --blue: #88c0d0;
  --radius: 12px;
  --shadow: 0 8px 30px rgba(0, 0, 0, 0.3);

  color-scheme: dark;
  color: var(--text-primary);
  background-color: var(--bg-primary);
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
  width: 100%;
}

.container {
  display: flex;
  flex-direction: column;
  min-height: 80vh;
  justify-content: space-between;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: var(--blue);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.main-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin: 2rem 0;
}

.card {
  background-color: var(--bg-elevated);
  border-radius: var(--radius);
  padding: 2rem;
  text-align: left;
  box-shadow: var(--shadow);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.45);
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
}

.card h2 {
  margin-top: 0;
  color: var(--green);
}

.btn {
  background-color: var(--blue);
  color: var(--bg-primary);
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.1s ease, filter 0.1s ease;
}

.btn:hover {
  filter: brightness(1.1);
}

.btn:active {
  transform: scale(0.98);
}
```

---

### 3. Shell Stack (Bash & Python CLI Scripts)

To make shell script repositories as robust as Python or React code bases, we integrated static code analysis (`shellcheck`) and unit testing (`bats-core`).

#### Shell `scripts/bash/example.sh`
This script demonstrates strict scripting guidelines (`set -euo pipefail`), dynamic options parsing, logging routines, and help displays.
```bash
#!/usr/bin/env bash
# Example template script demonstrating robust bash engineering standards.
set -euo pipefail

# Dynamic fallback variables (no hardcoded settings)
DEV_HOST="${DEV_HOST:-127.0.0.1}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

log() {
  local level="${1}"
  local msg="${2}"
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] [${level}] ${msg}" >&2
}

show_help() {
  cat <<EOF
Usage: $(basename "${0}") [options]

Options:
  -h, --help        Show this help message and exit.
  -d, --host HOST   Specify the host address (default: ${DEV_HOST}).
  -v, --verbose     Enable verbose debug logging.
EOF
}

# Parse command line options
VERBOSE=false
while [[ $# -gt 0 ]]; do
  case "${1}" in
    -h|--help)
      show_help
      exit 0
      ;;
    -d|--host)
      DEV_HOST="${2:?--host requires a value}"
      shift 2
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    *)
      echo "Unknown option: ${1}" >&2
      show_help >&2
      exit 1
      ;;
  esac
done

if [ "$VERBOSE" = true ]; then
  LOG_LEVEL="DEBUG"
fi

log "${LOG_LEVEL}" "Starting example execution..."
log "INFO" "Target host configured as: ${DEV_HOST}"
log "INFO" "Task completed successfully!"
```

#### Bats Unit Test `scripts/tests/test_example.bats`
Bats handles testing of the CLI output and return codes:
```bash
#!/usr/bin/env bats

setup() {
  DIR="$( cd "$( dirname "$BATS_TEST_FILENAME" )" >/dev/null 2>&1 && pwd )"
  SCRIPT="$DIR/../bash/example.sh"
}

@test "help flag returns 0 and outputs usage" {
  run "$SCRIPT" --help
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Usage:" ]]
}

@test "custom host flag sets host correctly" {
  run "$SCRIPT" --host 192.168.1.1
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Target host configured as: 192.168.1.1" ]]
}

@test "unknown flag returns 1" {
  run "$SCRIPT" --unknown-flag-test
  [ "$status" -eq 1 ]
}
```

---

### 4. PowerShell Stack (Automation & Windows/Cross-Platform Scripts)

Adding PowerShell Core support makes scripting robust across platforms, complete with PSScriptAnalyzer linting and Pester tests.

#### PowerShell `scripts/powershell/example.ps1`
```powershell
<#
.SYNOPSIS
    Example template PowerShell script demonstrating robust automation standards.
.DESCRIPTION
    A boilerplate script showing parameter definitions, standard logging, and error handling.
.PARAMETER Hostname
    Specify the target host address (default: 127.0.0.1).
.EXAMPLE
    .\example.ps1 -Hostname "192.168.1.1"
#>
[CmdletBinding()]
param (
    [string]$Hostname = "127.0.0.1"
)

# Strict option error action
$ErrorActionPreference = "Stop"

function Log-Message {
    param (
        [string]$Level = "INFO",
        [string]$Message
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    Write-Host "[$timestamp] [$Level] $Message"
}

Log-Message -Level "INFO" -Message "Starting PowerShell script execution..."
Log-Message -Level "INFO" -Message "Target hostname: $Hostname"
Log-Message -Level "INFO" -Message "Execution completed successfully!"
```

#### Pester Test `scripts/tests/example.Tests.ps1`
```powershell
Describe "PowerShell Example Script" {
    BeforeAll {
        $ScriptPath = "$PSScriptRoot/../powershell/example.ps1"
    }

    It "Should exist" {
        $ScriptPath | Should -Exist
    }

    It "Should run successfully and output hostname" {
        $result = & $ScriptPath -Hostname "10.0.0.1"
        $result | Should -Contain "[INFO] Target hostname: 10.0.0.1"
    }
}
```

---

## Part 4: The Top-Level Coordinating Makefile

When projects contain mixed layers (like a Python backend and a React frontend), the root level must have a way to build and run all parts. We created a top-level coordinative `Makefile` in the root of the project that delegates standard actions to the child directories:

```makefile
.PHONY: setup lint test run clean

setup:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend setup; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend setup; fi
	@if [ -d scripts ] && [ -f scripts/Makefile ]; then $(MAKE) -C scripts setup; fi

lint:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend lint; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend lint; fi
	@if [ -d scripts ] && [ -f scripts/Makefile ]; then $(MAKE) -C scripts lint; fi

test:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend test; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend test; fi
	@if [ -d scripts ] && [ -f scripts/Makefile ]; then $(MAKE) -C scripts test; fi

run:
	@if [ -d backend ] && [ -f backend/Makefile ]; then $(MAKE) -C backend run; fi
	@if [ -d frontend ] && [ -f frontend/Makefile ]; then $(MAKE) -C frontend run; fi
```

This ensures that running `make setup` or `make test` inside the project root works seamlessly regardless of the layout stack.

---

## Part 5: Automated Scaffolding with `bootstrap.sh`

The `bootstrap.sh` utility manages the complete initialization process for new directories.

### Key Design Enhancements
*   **Dry-Run Default**: The script runs in dry-run mode by default, displaying a review banner and listing all planned files. You must explicitly pass `--write` or `--apply` to write to disk.
*   **No Statically Linked Settings**: All usernames, emails, and remote paths are resolved dynamically via `gh api` and `git config`. No details are hardcoded to a specific user, making the script completely shareable.
*   **Auto-update Autodoc README**: The script commits the initial boilerplate and triggers the post-commit hook to instantly create a Mermaid tree diagram inside the root `README.md`.
*   **Interactive GitHub Remote Sync**: Automates creating public/private repositories on GitHub and pushing using SSH keys (`git@github.com:...`).

#### Detailed `bootstrap.sh` Implementation
```bash
#!/usr/bin/env bash
# Scaffold a new repository with standardized 4-folder blueprint, testing suite, and GitHub integration.
# Usage: ./bootstrap.sh <repo-name> <python|node-vite|shell|powershell> [options]
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

# Resolve GitHub user dynamically
GITHUB_USER="${GITHUB_USER:-$(gh api user -q .login 2>/dev/null || echo "")}"
if [[ -z "$GITHUB_USER" ]]; then
  GITHUB_USER="$(git config user.name || echo "Owner" | tr ' ' '_')"
fi

# Review Banner
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

# Copy configurations
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
... [Standard MIT license body]
EOF
      ;;
    apache2)
      cat > "$DEST/LICENSE" <<EOF
Copyright $YEAR $AUTHOR_NAME
... [Standard Apache 2.0 license body]
EOF
      ;;
    gpl3|*)
      if [[ -f "$TEMPLATE_DIR/shared/LICENSE-GPL3" ]]; then
        { printf 'Copyright (C) %s %s\n\n' "$YEAR" "$AUTHOR_NAME"; cat "$TEMPLATE_DIR/shared/LICENSE-GPL3"; } > "$DEST/LICENSE"
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

# README auto-update script
cp "$TEMPLATE_DIR/shared/scripts/update-readme.sh" "$DEST/scripts/"
chmod +x "$DEST/scripts/update-readme.sh"

# Stack layout & placeholder distribution
case "$STACK" in
  python)
    PKG="$(echo "$REPO_NAME" | tr '-' '_')"
    mkdir -p "$DEST/backend/src/$PKG" "$DEST/backend/tests"
    cp "$TEMPLATE_DIR/python/backend/src/main.py" "$DEST/backend/src/$PKG/main.py"
    cp "$TEMPLATE_DIR/python/backend/tests/test_main.py" "$DEST/backend/tests/test_main.py"
    touch "$DEST/backend/src/$PKG/__init__.py" "$DEST/backend/tests/__init__.py"
    sed "s/__REPO_NAME__/$REPO_NAME/" "$TEMPLATE_DIR/python/pyproject.toml.tmpl" > "$DEST/backend/pyproject.toml"
    cp "$TEMPLATE_DIR/python/Makefile" "$DEST/backend/"
    cp "$TEMPLATE_DIR/python/test.yml" "$DEST/.github/workflows/test.yml"
    
    # Placeholders for unused folders
    cp "$TEMPLATE_DIR/shared/docs/README.md" "$DEST/docs/"
    cp "$TEMPLATE_DIR/shared/frontend/README.md" "$DEST/frontend/"
    ;;
  node-vite)
    mkdir -p "$DEST/frontend/src/components" "$DEST/frontend/src/lib" "$DEST/frontend/public"
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

# Initialize git
cd "$DEST"
git init -q -b main
cp "$TEMPLATE_DIR/shared/hooks/post-commit" .git/hooks/post-commit
chmod +x .git/hooks/post-commit
git add -A

if command -v pre-commit >/dev/null 2>&1; then
  pre-commit install -q || echo "note: pre-commit hooks installation failed."
fi

git commit -m "Initial scaffold of repository templates" -q
echo "Local repository successfully scaffolded at $DEST"

# GitHub Remote Creation
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

if [[ "$INTERACTIVE" == "true" ]]; then
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
```

---

## Part 6: Retrofitting Existing Repositories with `retrofit.sh`

The `retrofit.sh` utility is designed to re-organize pre-existing codebases.

### Key Design Enhancements
*   **Dry-Run by Default**: Just like the bootstrapper, running the script directly scans the folder layout and shows exactly what it would move and copy without modifying files. To execute migrations, pass `--write` or `--apply`.
*   **Incremental Moves**: It scans the root folder for any newly added loose scripts (e.g. `*.py`, `*.sh`) and moves them to `backend/` or `scripts/bash/`, allowing you to run it repeatedly as a maintenance tool.
*   **Feature Branching (`-b` / `--branch`)**: Checks out a new Git branch automatically before reorganizing files. If the branch already exists locally, it checks it out and prints a warning rather than aborting.
*   **Dynamic `gh` Installer (`--install-gh`)**: Added a self-contained installation function that checks system package managers (`apt`, `dnf`, or `pacman`) and installs the official `gh` CLI.
*   **Root Folder Exclusion Guard**: Excludes meta-configurations (like `.env`, `docker-compose.yml`, `.gitignore`, `README.md`, `LICENSE`) from moves, keeping them safely at the root level.
*   **Auto-commit on Successful Migration**: Stages and commits re-organized files automatically with a descriptive message to immediately fire Git hooks and update the README autodocs.

#### Detailed `retrofit.sh` Implementation
```bash
#!/usr/bin/env bash
# Retrofit an existing repository to the standardized 4-folder blueprint.
# Usage: ./retrofit.sh [options]
set -euo pipefail

TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Global defaults
TARGET_REPO="."
BRANCH_NAME=""
DRY_RUN=true
VERBOSE=false
FORCE=false
INSTALL_GH=false

show_help() {
  cat <<EOF
Repository Retrofitter Utility

Usage:
  $(basename "${0}") [options]

Options:
  -h, --help           Show this help message and exit.
  -r, --repo PATH      Path to the repository to retrofit (default: current directory ".").
  -b, --branch NAME    Create and switch to a new Git branch before retrofitting.
  --write, --apply     Actually execute the migration (default is dry-run).
  -v, --verbose        Enable verbose output.
  -f, --force          Bypass Git working tree cleanliness check.
  --install-gh         Install the GitHub CLI (gh) on this system.
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
    -r|--repo)
      TARGET_REPO="${2:?--repo requires a value}"
      shift 2
      ;;
    -b|--branch)
      BRANCH_NAME="${2:?--branch requires a value}"
      shift 2
      ;;
    --write|--apply)
      DRY_RUN=false
      shift
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -f|--force)
      FORCE=true
      shift
      ;;
    --install-gh)
      INSTALL_GH=true
      shift
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

if [[ ${#POSITIONAL_ARGS[@]} -gt 0 ]]; then
  TARGET_REPO="${POSITIONAL_ARGS[0]}"
fi

log() {
  local level="${1}"
  local msg="${2}"
  echo "[$(date +'%Y-%m-%dT%H:%M:%S')] [${level}] ${msg}" >&2
}

verbose_log() {
  if [[ "$VERBOSE" == "true" ]]; then
    log "DEBUG" "$1"
  fi
}

install_gh_client() {
  log "INFO" "Checking if gh client is already installed..."
  if command -v gh >/dev/null 2>&1; then
    log "INFO" "GitHub CLI (gh) is already installed at: $(command -v gh)"
    return 0
  fi

  log "INFO" "Installing gh client on this system..."
  if command -v apt-get >/dev/null 2>&1; then
    log "INFO" "Using apt-get package manager..."
    sudo mkdir -p -m 755 /etc/apt/keyrings
    wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
    sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y gh
  elif command -v dnf >/dev/null 2>&1; then
    log "INFO" "Using dnf package manager..."
    sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
    sudo dnf install -y gh
  elif command -v pacman >/dev/null 2>&1; then
    log "INFO" "Using pacman package manager..."
    sudo pacman -S --noconfirm github-cli
  else
    log "ERROR" "Unsupported package manager. Please install gh manually: https://github.com/cli/cli#installation"
    exit 1
  fi
  log "INFO" "GitHub CLI (gh) installed successfully!"
}

if [[ "$INSTALL_GH" == "true" ]]; then
  install_gh_client
  exit 0
fi

TARGET_DIR="$(cd "$TARGET_REPO" && pwd)"
if [[ ! -d "$TARGET_DIR" ]]; then
  log "ERROR" "Target directory $TARGET_REPO does not exist."
  exit 1
fi

if [[ ! -d "$TARGET_DIR/.git" ]]; then
  log "ERROR" "Target path $TARGET_DIR is not a Git repository."
  exit 1
fi

cd "$TARGET_DIR"

IS_DIRTY=false
if ! git diff --quiet || ! git diff --cached --quiet; then
  IS_DIRTY=true
fi
if [[ -n "$(git status --porcelain | grep -E '^\?\?')" ]]; then
  IS_DIRTY=true
fi

if [[ "$IS_DIRTY" == "true" && "$DRY_RUN" == "false" && "$FORCE" == "false" ]]; then
  log "WARNING" "Git working tree in $TARGET_DIR has uncommitted changes or untracked files."
  read -r -p "Do you want to proceed anyway? (y/N): " DIRTY_CONFIRM
  if [[ ! "$DIRTY_CONFIRM" =~ ^[yY]([eE][sS])?$ ]]; then
    log "INFO" "Aborted."
    exit 1
  fi
fi

# Detect Layout
HAS_PYTHON=false
HAS_VITE=false
HAS_SHELL=false

if [[ -f pyproject.toml ]] || [[ -f requirements.txt ]]; then
  HAS_PYTHON=true
fi
if [[ -f package.json ]] && { [[ -f vite.config.ts ]] || [[ -f vite.config.js ]]; }; then
  HAS_VITE=true
fi
if [[ -n "$(find . -maxdepth 1 -name "*.sh" ! -name "run.sh" ! -name "bootstrap.sh" ! -name "retrofit.sh" -print -quit 2>/dev/null)" ]]; then
  HAS_SHELL=true
fi

if [[ "$HAS_PYTHON" == "false" && "$HAS_VITE" == "false" && "$HAS_SHELL" == "false" ]]; then
  HAS_SHELL=true
fi

# Dry Run Summary
if [[ "$DRY_RUN" == "true" ]]; then
  echo "=================================================="
  echo "          RETROFIT DRY RUN SUMMARY                "
  echo "=================================================="
  echo "Target Repository: $TARGET_DIR"
  echo "Target Branch:     ${BRANCH_NAME:-(Current Active Branch)}"
  echo "Detected Layouts:  Python=$HAS_PYTHON, Vite=$HAS_VITE, Shell=$HAS_SHELL"
  echo "--------------------------------------------------"
  echo "Planned Directory Scaffolding:"
  echo "  - Create folders docs/, scripts/, frontend/, backend/ (if missing)"
  
  for f in .gitleaks.toml .pre-commit-config.yaml .editorconfig SECURITY.md CONTRIBUTING.md; do
    if [[ ! -f "$f" ]]; then
      echo "  - Copy shared metadata configuration: $f"
    fi
  done
  
  if [[ ! -f .git/hooks/post-commit ]]; then
    echo "  - Install post-commit hook: .git/hooks/post-commit"
  fi
  
  if [[ "$HAS_PYTHON" == "true" ]]; then
    echo "Planned Python migrations:"
    if [[ -d src ]]; then echo "  - Move folder: src/ -> backend/src/"; fi
    if [[ -d tests ]]; then echo "  - Move folder: tests/ -> backend/tests/"; fi
    echo "  - Move loose python files (*.py) in root -> backend/"
    for f in pyproject.toml requirements.txt requirements-dev.txt Makefile; do
      if [[ -f "$f" ]]; then echo "  - Move config file: $f -> backend/"; fi
    done
    if [[ ! -f backend/Makefile ]]; then echo "  - Install Python Makefile in backend/"; fi
    if [[ ! -f .github/workflows/test.yml ]]; then echo "  - Install Python test.yml workflow"; fi
  fi
  
  if [[ "$HAS_VITE" == "true" ]]; then
    echo "Planned Node-Vite migrations:"
    for d in src public; do
      if [[ -d "$d" ]]; then echo "  - Move folder: $d/ -> frontend/$d/"; fi
    done
    for f in package.json tsconfig.json vite.config.ts vite.config.js index.html Makefile; do
      if [[ -f "$f" ]]; then echo "  - Move config file: $f -> frontend/"; fi
    done
    if [[ ! -f frontend/Makefile ]]; then echo "  - Install Node-Vite Makefile in frontend/"; fi
    if [[ ! -f .github/workflows/test.yml ]]; then echo "  - Install Node-Vite test.yml workflow"; fi
  fi
  
  if [[ "$HAS_SHELL" == "true" ]]; then
    echo "Planned Shell migrations:"
    echo "  - Move loose root shell scripts (*.sh) -> scripts/bash/"
    if [[ ! -f scripts/Makefile ]]; then echo "  - Install Shell Makefile in scripts/"; fi
    if [[ ! -f .github/workflows/test.yml ]]; then echo "  - Install Shell test.yml workflow"; fi
  fi
  
  if [[ "$HAS_PYTHON" == "true" && "$HAS_VITE" == "true" ]]; then
    if [[ ! -f Makefile ]]; then echo "  - Install shared coordinator Makefile in root"; fi
  fi
  
  echo "Would automatically stage and commit re-organized files."
  echo "--- DRY RUN COMPLETE ---"
  exit 0
fi

# Live execution
log "INFO" "Applying live repository re-organization..."

if [[ -n "$BRANCH_NAME" ]]; then
  if git show-ref --quiet --verify "refs/heads/$BRANCH_NAME"; then
    log "WARNING" "Branch '$BRANCH_NAME' already exists. Switching to it..."
    git checkout "$BRANCH_NAME"
  else
    log "INFO" "Creating and switching to new branch '$BRANCH_NAME'..."
    git checkout -b "$BRANCH_NAME"
  fi
fi

mkdir -p docs scripts frontend backend

for f in .gitleaks.toml .pre-commit-config.yaml .editorconfig SECURITY.md CONTRIBUTING.md; do
  if [[ ! -f "$f" ]]; then
    verbose_log "Copying shared configuration: $f"
    cp "$TEMPLATE_DIR/shared/$f" "./$f"
  fi
done

mkdir -p .cursor/rules/global-rules
cp "$TEMPLATE_DIR/shared/.cursor/rules/global-rules/workspace-organization-always.mdc" .cursor/rules/global-rules/

for dir in docs scripts frontend backend; do
  if [ -z "$(ls -A "$dir" | grep -v "\.mdc" || true)" ]; then
    cp "$TEMPLATE_DIR/shared/$dir/README.md" "$dir/"
  fi
done

# Python Stack migration
if [[ "$HAS_PYTHON" == "true" ]]; then
  log "INFO" "Migrating Python layout..."
  if [[ -d src ]]; then
    mkdir -p backend/src
    cp -a src/. backend/src/ && rm -rf src
  fi
  if [[ -d tests ]]; then
    mkdir -p backend/tests
    cp -a tests/. backend/tests/ && rm -rf tests
  fi
  for f in *.py; do
    if [[ -f "$f" && "$f" != "scrape.py" ]]; then
      mv "$f" backend/
    fi
  done
  for f in pyproject.toml requirements.txt requirements-dev.txt Makefile; do
    if [[ -f "$f" ]]; then
      mv "$f" backend/
    fi
  done
  if [[ ! -f backend/Makefile ]]; then
    cp "$TEMPLATE_DIR/python/Makefile" backend/
  fi
  if [[ ! -f .github/workflows/test.yml ]]; then
    mkdir -p .github/workflows
    cp "$TEMPLATE_DIR/python/test.yml" .github/workflows/test.yml
  fi
fi

# Node-Vite layout migration
if [[ "$HAS_VITE" == "true" ]]; then
  log "INFO" "Migrating Node-Vite layout..."
  for d in src public; do
    if [[ -d "$d" ]]; then
      mv "$d" frontend/
    fi
  done
  for f in package.json tsconfig.json vite.config.ts vite.config.js index.html Makefile; do
    if [[ -f "$f" ]]; then
      mv "$f" frontend/
    fi
  done
  if [[ ! -f frontend/Makefile ]]; then
    cp "$TEMPLATE_DIR/node-vite/Makefile" frontend/
  fi
  if [[ ! -f .github/workflows/test.yml ]]; then
    mkdir -p .github/workflows
    cp "$TEMPLATE_DIR/node-vite/test.yml" .github/workflows/test.yml
  fi
fi

# Shell script layout migration
if [[ "$HAS_SHELL" == "true" ]]; then
  log "INFO" "Migrating loose shell script layout..."
  for f in *.sh; do
    if [[ -f "$f" && "$f" != "run.sh" && "$f" != "bootstrap.sh" && "$f" != "retrofit.sh" ]]; then
      mkdir -p scripts/bash
      mv "$f" scripts/bash/
    fi
  done
  if [[ ! -f scripts/Makefile ]]; then
    cp "$TEMPLATE_DIR/shell/Makefile" scripts/
  fi
  if [[ ! -f .github/workflows/test.yml ]]; then
    mkdir -p .github/workflows
    cp "$TEMPLATE_DIR/shell/test.yml" .github/workflows/test.yml
  fi
fi

# Mixed coordinates Makefile
if [[ "$HAS_PYTHON" == "true" && "$HAS_VITE" == "true" ]]; then
  if [[ ! -f Makefile ]]; then
    cp "$TEMPLATE_DIR/shared/Makefile" ./Makefile
  fi
fi

# Git hook
if [[ ! -f .git/hooks/post-commit ]]; then
  cp "$TEMPLATE_DIR/shared/hooks/post-commit" .git/hooks/post-commit
  chmod +x .git/hooks/post-commit
fi
if [[ ! -f scripts/update-readme.sh ]]; then
  mkdir -p scripts
  cp "$TEMPLATE_DIR/shared/scripts/update-readme.sh" scripts/
  chmod +x scripts/update-readme.sh
fi

git add -A || true
if ! git diff --cached --quiet; then
  log "INFO" "Staging and committing re-organization changes..."
  git commit -m "Retrofit repository layout to standard 4-folder blueprint"
  log "INFO" "Migration commit successfully completed!"
else
  log "INFO" "No layout adjustments were necessary (repository already standardized)."
fi

log "INFO" "Retrofit successfully applied!"
```

---

## Conclusion

Standardizing repository directories ensures structural sanity across projects. By using the `bootstrap.sh` and `retrofit.sh` utilities, you can enforce the 4-folder blueprint automatically with zero manual file moves, full validation pipelines, and instant local and remote repository synchronization. 

You can checkout the latest version of these tools inside the [feature/repo-templates](https://github.com/Richie086/scripts-public/tree/feature/repo-templates/projects/repo-templates) branch of the `scripts-public` repository.
