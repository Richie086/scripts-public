Developing software across multiple programming languages and environments can quickly lead to a chaotic mess of disorganized repositories. When every project uses a different directory layout, it becomes challenging to automate deployment pipelines, integrate linters, run unit tests, and transition between frontend and backend code. To solve this problem, we created the **Standardized 4-Folder Project Blueprint**, a structural architecture that organizes every repository into four high-level directories: `docs/`, `scripts/`, `frontend/`, and `backend/`. 

To automate this workflow and retrofit existing systems, we developed two powerful shell utilities: `setup-repository.sh` (for scaffolding new projects) and `organize-repository.sh` (for reorganizing existing projects). 

In this comprehensive guide, we will walk through the design philosophy, standard directories, template stacks (React, Python, Bash, and PowerShell), automated linting and unit testing suites, and the detailed usage of these two automation utilities.

---

## Part 1: The Design Philosophy of the 4-Folder Blueprint

Many projects fail to maintain a clean codebase not because of poor coding, but due to structural rot. Directory layout plays a vital role in keeping files where they belong. The 4-Folder Project Blueprint establishes a clean separation of concerns at the root level of every repository:

*   **`docs/` (Documentation)**: Holds specifications, requirements, architecture designs, planning markdown documents, and logs. It serves as the single source of truth for project design and roadmap.
*   **`scripts/` (DevOps & Helpers)**: Contains automation scripts, database migration scripts, orchestration tools, and local utilities. Under `scripts/`, files are grouped strictly by extension or stack (e.g. `scripts/bash/`, `scripts/python/`, `scripts/powershell/`, `scripts/tests/`).
*   **`frontend/` (User Interfaces)**: Houses all user interface client code, static assets, HTML/CSS layouts, and React/Vite development stacks.
*   **`backend/` (Server APIs & Business Logic)**: Contains backend server logic, databases, API servers (like FastAPI), configuration managers, and business workflows.

By separating the user interface, server logic, operations scripts, and project documentation into these four folders, any developer (or AI coding assistant) can immediately navigate the repository and know exactly where files should live.

### Why Separating Concerns Matters
When developers dump files directly into the repository root, projects become hard to navigate. For example, local scripts, Docker configurations, source code, and assets clash in a single flat directory. This confusion gets worse when sharing code with teammates or deploying via continuous integration (CI) environments. By enforcing a strict 4-folder boundary at the root:
1.  **Continuous Integration is Simplified**: Build pipelines can target the `frontend/` directory for assets compilation and `backend/` for server tests, ignoring operational scripts or documentation updates entirely.
2.  **AI Pairing Efficiency is Maximized**: Agentic coding assistants and IDE systems like Cursor are guided by explicit file-scoping rules. Rather than searching the entire repository, they focus directly on the target subfolder, reducing token usage and preventing errors.
3.  **Portability and Shareability are Retained**: New developers onboarding onto the project don't have to guess where documentation or scripts reside. The layout is identical across every project in the organization.

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

#### Understanding FastAPI and Uvicorn
FastAPI is a modern, high-performance web framework for building APIs with Python 3.7+ based on standard Python type hints. The primary reasons for standardizing on FastAPI are its speed, automatic documentation generation (via Swagger UI), and out-of-the-box support for asynchronous request handling. Uvicorn acts as the Lightning-fast ASGI server implementation, serving the application and handling concurrent HTTP requests.

To manage configurations and metadata cleanly, we use a single `pyproject.toml` file. This standardizes metadata declarations and declares dev dependencies (like pytest, httpx, and ruff) without relying on cluttered requirements files.

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

#### FastAPI Testing Strategy
To verify that the API functions correctly, we write unit tests using `pytest` and FastAPI's `TestClient` (which wraps the popular `httpx` client). This allows us to perform simulated requests against our FastAPI app endpoints without spinning up a live network port.

Here is the testing suite inside `backend/tests/test_main.py`:
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "api"}
```

To run these tests, format the code, and start the app, we use a local `Makefile` that encapsulates the commands. This makes operations standardized and easy to recall:

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

#### The Power of Vite and TypeScript
Vite has become the modern standard for frontend development, replacing legacy configurations like Webpack. It leverages native ES modules in the browser to deliver near-instantaneous hot module replacement (HMR) and fast build times. Combined with TypeScript, we gain compile-time type validation, preventing bugs before assets are deployed.

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

#### UI Design System (index.css)
The design system defines typography, margins, rounded corners using CSS variables, and Dracula/Nord theme colors. We use card styles with subtle top highlights and dark bottom borders to convey physical depth.

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

#### Strict Bash Operations & Signals
For automation scripts, using standard shell safety flags is non-negotiable. We configure scripts with `set -euo pipefail`:
*   `set -e`: Aborts execution immediately if any command returns a non-zero exit status. This prevents cascading failures where a script continues running even after a critical step (like checking out a directory) fails.
*   `set -u`: Fails the script if an undeclared environment variable is referenced, preventing silent errors and crashes due to typos in variable names.
*   `set -o pipefail`: Propagates pipeline errors. In standard bash, a pipeline returns the exit status of the very last command. If `grep` fails in the middle of a pipeline, but `cat` succeeds at the end, the exit code is 0 (success). Enabling pipefail forces the entire pipeline expression to fail if any intermediate command fails.

Furthermore, we utilize the `trap` command to capture signals (like `SIGINT` or `SIGTERM`) and run cleanup routines (e.g. erasing temporary passwords from memory or deleting scratch directories).

#### Shell `scripts/bash/example.sh`
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

#### PowerShell Parameter Binding
PowerShell scripts should always specify `[CmdletBinding()]` to support advanced function parameters (like `-Verbose`, `-Debug`, `-ErrorAction`). We declare parameter types strictly (e.g. `[string]`) and enforce strict error action policies:

```powershell
# Stop execution on any error
$ErrorActionPreference = "Stop"
```

Using attributes like `[Parameter(Mandatory=$true)]` forces execution loops to ask for missing parameters cleanly or abort before runtime.

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
Pester acts as the testing framework for PowerShell code blocks, matching cmdlet outputs and validating logic:
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

## Part 5: Automated Scaffolding with `setup-repository.sh`

The `setup-repository.sh` utility manages the complete initialization process for new directories.

### Key Design Enhancements
*   **Dry-Run Default**: The script runs in dry-run mode by default, displaying a review banner and listing all planned files. You must explicitly pass `--write` or `--apply` to write to disk. This safety guardrail prevents accidental execution and overwrites of exist directories on disk.
*   **No Statically Linked Settings**: All usernames, emails, and remote paths are resolved dynamically via `gh api` and `git config` at runtime. No details are hardcoded to a specific user, making the script completely shareable across teams (e.g. sharing with Tyler).
*   **Auto-update Autodoc README**: The script commits the initial boilerplate and triggers the post-commit hook to instantly create a Mermaid tree diagram inside the root `README.md`.
*   **Interactive GitHub Remote Sync**: Automates creating public/private repositories on GitHub and pushing using SSH keys (`git@github.com:...`).
*   **Security Integration**: Automatically scaffolds GitLeaks checks (`.gitleaks.toml`) and pre-commit hooks (`.pre-commit-config.yaml`) to block developers from accidentally committing credentials or API keys.

#### High-level Execution Logic
The script begins by dynamically resolving your GitHub username and checking your git configuration. It prints a stylized environment summary banner outlining variables, visibility settings, and remote targets. If dry-run is active (which is the default behavior), it exits cleanly after displaying the planned steps.

When run with `--write`, the script:
1.  Creates root folders: `docs/`, `scripts/`, `frontend/`, and `backend/`.
2.  Copies template configurations: `.gitleaks.toml`, `.pre-commit-config.yaml`, `.editorconfig`, `.gitignore`, and Cursor rules.
3.  Injects stack-specific templates (FastAPI, React, Shell, or PowerShell).
4.  Initializes git, configures git hooks, runs the first commit to trigger documentation generation, and pushes to GitHub.

The full source code of the script is tracked on GitHub under the [setup-repository.sh](https://github.com/Richie086/scripts-public/blob/feature/repo-templates/projects/repo-templates/setup-repository.sh) path.

---

## Part 6: Retrofitting Existing Repositories with `organize-repository.sh`

The `organize-repository.sh` utility is designed to re-organize pre-existing codebases.

### Key Design Enhancements
*   **Dry-Run by Default**: Just like the bootstrapper, running the script directly scans the folder layout and shows exactly what it would move and copy without modifying files. To execute migrations, pass `--write` or `--apply`.
*   **Incremental Moves**: It scans the root folder for any newly added loose scripts (e.g. `*.py`, `*.sh`) and moves them to `backend/` or `scripts/bash/`, allowing you to run it repeatedly as a maintenance tool.
*   **Feature Branching (`-b` / `--branch`)**: Checks out a new Git branch automatically before reorganizing files. If the branch already exists locally, it checks it out and prints a warning rather than aborting.
*   **Dynamic `gh` Installer (`--install-gh`)**: Added a self-contained installation function that checks system package managers (`apt`, `dnf`, or `pacman`) and installs the official `gh` CLI.
*   **Root Folder Exclusion Guard**: Excludes meta-configurations (like `.env`, `docker-compose.yml`, `.gitignore`, `README.md`, `LICENSE`) from moves, keeping them safely at the root level.
*   **Auto-commit on Successful Migration**: Stages and commits re-organized files automatically with a descriptive message to immediately fire Git hooks and update the README autodocs.

#### High-level Execution Logic
Before making modifications, the script validates that the target folder is a valid Git repository and prompts for confirmation if there are uncommitted local edits. 

If live run is active:
1.  Switches to the designated feature branch if specified.
2.  Discovers and relocates existing source paths (`src/` and `tests/`) to their respective `backend/` or `frontend/` folders depending on file signatures.
3.  Moves loose scripts to the appropriate directories while safeguarding critical root configurations like `.env`.
4.  Deploys the global Cursor rules and missing stack configurations.
5.  Stages and commits the resulting state.

The full source code of the script is tracked on GitHub under the [organize-repository.sh](https://github.com/Richie086/scripts-public/blob/feature/repo-templates/projects/repo-templates/organize-repository.sh) path.

---

## Part 7: Dynamic Documentation & Autodocs

To ensure project documentation never becomes stale, we developed an automated documentation updating hook script that runs on every commit. When a commit completes, a `post-commit` hook is executed which automatically rebuilds the repository structure graph using a Mermaid diagram and lists recent changes directly in your `README.md`.

Here is the update script (`scripts/update-readme.sh`) that automates this workflow:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Dynamic directory path
REPO_DIR="$(git rev-parse --show-toplevel)"
README_FILE="$REPO_DIR/README.md"

if [ ! -f "$README_FILE" ]; then
  exit 0
fi

# 1. Generate Mermaid Graph
MERMAID_CONTENT="\`\`\`mermaid\ngraph TD\n"
MERMAID_CONTENT+="    Root[\"📂 Root\"] --> Docs[\"📂 docs\"]\n"
MERMAID_CONTENT+="    Root --> Scripts[\"📂 scripts\"]\n"
MERMAID_CONTENT+="    Root --> Frontend[\"📂 frontend\"]\n"
MERMAID_CONTENT+="    Root --> Backend[\"📂 backend\"]\n"

# Add dynamic child directories if present
if [ -d "$REPO_DIR/scripts/bash" ]; then
  MERMAID_CONTENT+="    Scripts --> ScriptsBash[\"📂 bash\"]\n"
fi
if [ -d "$REPO_DIR/scripts/powershell" ]; then
  MERMAID_CONTENT+="    Scripts --> ScriptsPS[\"📂 powershell\"]\n"
fi
if [ -d "$REPO_DIR/backend/src" ]; then
  MERMAID_CONTENT+="    Backend --> BackendSrc[\"📂 src\"]\n"
fi
if [ -d "$REPO_DIR/frontend/src" ]; then
  MERMAID_CONTENT+="    Frontend --> FrontendSrc[\"📂 src\"]\n"
fi
MERMAID_CONTENT+="\`\`\`"

# 2. Get recent git commits
GIT_LOGS="### Recent Git Commits\n"
GIT_LOGS+="\$(git log -n 5 --oneline || echo 'No commit logs available')"

# 3. Replace placeholder blocks in README
# Find placeholders and insert content dynamically
TEMP_FILE="\$(mktemp)"
awk -v mermaid="\$MERMAID_CONTENT" -v logs="\$GIT_LOGS" '
  /<!-- AUTO-GENERATED:START -->/ {
    print;
    print "\n### Repository Layout Map";
    print mermaid;
    print "\n" logs;
    skip=1;
    next;
  }
  /<!-- AUTO-GENERATED:END -->/ {
    skip=0;
  }
  !skip { print }
' "\$README_FILE" > "\$TEMP_FILE"

mv "\$TEMP_FILE" "\$README_FILE"
```

This guarantees that whenever anyone checks out the codebase, they are immediately greeted by an accurate visualization of the structure and the latest development logs!

---

## Part 8: Local Setup and Toolchain Guide

To get the full power of the automated linting, testing, and secret detection, developers should install the core toolchain tools on their workstations.

### 1. Pre-commit Hooks Setup
Pre-commit coordinates code checks prior to staging commits. Install it via pip or your system package manager:
```bash
# Ubuntu/Debian
sudo apt-get install -y pre-commit

# macOS
brew install pre-commit
```
Run `pre-commit install` inside your repository to register the Git hooks. From then on, every `git commit` runs Ruff checks, shellcheck linting, and GitLeaks scans automatically!

### 2. Secrets Filtering (GitLeaks)
GitLeaks intercepts commits containing credentials. Install it via:
```bash
# macOS
brew install gitleaks

# Direct Binary Download (Linux)
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz
tar -xf gitleaks_8.18.2_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/
```

### 3. Continuous Integration Pipelines
When you push code to GitHub, the configured `.github/workflows/test.yml` automatically instantiates clean virtual environments to test your code:
*   **Python tests**: Runs inside Ubuntu containers using `pytest` and `ruff check`.
*   **Frontend tests**: Checks TypeScript syntax and lints using ESLint.
*   **Shell tests**: Performs syntax checks with Shellcheck and executes Bats tests.
*   **PowerShell tests**: Installs PowerShell Core and executes Pester test blocks.

This guarantees that any changes to your code maintain continuous quality standards, preventing regressions from merging into your main branches.

---

## Part 9: Advanced Architectural Best Practices

Standardizing codebase layouts is only half the battle. To build truly robust, enterprise-ready projects, teams should adhere to advanced architectural principles:

### 1. Decoupling Configurations from Code
Never hardcode environment-specific variables like database URIs, API tokens, port configurations, or hostnames inside your application code or automation scripts. 
- **Application Level**: Load settings from environment variables using packages like `pydantic-settings` in Python or `dotenv` in Node.js.
- **Script Level**: Define fallback values using shell parameter expansion (e.g., `DEV_HOST="${DEV_HOST:-127.0.0.1}"`). This guarantees that scripts run out-of-the-box locally, but remain flexible enough to be overridden by CI/CD systems or cloud orchestration runners.

### 2. Secret Management
Hardcoded secrets (passwords, SSH keys, private keys, API credentials) are the single largest source of security breaches.
- **Local Development**: Keep local secrets in `.env` files that are strictly listed in your root `.gitignore` file, ensuring they are never committed to your Git history.
- **Production Deployments**: For cloud configurations (such as AWS EC2 or Elastic Beanstalk), retrieve credentials dynamically from AWS Systems Manager Parameter Store or Secrets Manager using IAM instance profiles. This eliminates the need to write credentials to disk.

### 3. Strict Signal Handling and State Cleanup
Automated tools and daemons should handle interruptions gracefully.
- **Bash Scripts**: Use the `trap` command to capture signals like `SIGINT` (Ctrl+C), `SIGTERM`, and `ERR`. Register cleanup functions to delete temporary files or unset variables.
- **Server Applications**: Ensure your backend services intercept termination signals and complete active client operations (graceful shutdown) before exiting.

---

## Part 10: Comparative Analysis of Open Source Licenses

When publishing packages publicly, selecting the appropriate open source license is vital. We support MIT, GPL-3, and Apache 2.0 in the bootstrapper:

### 1. MIT License (Permissive)
The MIT license is one of the most popular open-source licenses. It is extremely permissive, allowing anyone to use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software with only one requirement: including the original copyright notice in all copies.
*   **Best for**: Libraries where maximum adoption is desired and commercial reuse is encouraged.

### 2. GNU GPL-3 (Strong Copyleft)
The GPL-3 is a strong copyleft license. It guarantees end-users the freedom to run, study, share, and modify the software. However, any modified versions of the software or derivative works must also be open-sourced under the GPL-3.
*   **Best for**: Standalone applications, CLI tools, and community-centric operations where you want to prevent proprietary forks.

### 3. Apache 2.0 (Permissive with Patent Grants)
The Apache 2.0 license is permissive like MIT, but includes explicit patent rights grants from contributors to users, protecting users from patent infringement lawsuits. It also requires keeping notices of modified files.
*   **Best for**: Enterprise-grade cloud native tools where patent safety is critical.

---

## Part 11: Step-by-Step Scaffolding Walkthrough

To see how these concepts align in a real workflow, let's trace a step-by-step example of bootstrapping a new repository from start to finish.

### 1. Running the Dry-Run Check
Before writing any files to disk, run the bootstrapper in its default mode. This validates the environment and ensures the toolchains exist:
```bash
./setup-repository.sh my-sample-api python
```
The console will display the **Scaffold Environment Summary** banner, detailing the target directory, stack, license, and resolved GitHub user info. It lists all folders and file assets it plans to create and exits cleanly with return code 0.

### 2. Performing the Scaffolding Write
To execute the scaffolding on disk, add the `--write` or `--apply` parameter:
```bash
./setup-repository.sh my-sample-api python --write
```
When run, the script creates the directories under `~/repositories/projects/my-sample-api/` and prints live confirmation logs of files written. Because we ran the script interactively, it starts the background virtual environment setup (`make setup`) automatically.

### 3. Verification of Files & Layout
Change directory to the new project and inspect the results:
```bash
cd ~/repositories/projects/my-sample-api
ls -la
```
The root folder is cleanly organized. Now verify the test suite:
```bash
make test
```
The local Makefile executes `pytest` inside the virtual environment, running the client checks and confirming that the scaffolding is 100% operational.

---

## Part 12: Step-by-Step Retrofitting Walkthrough

Now let's trace how to transition an existing repository into this exact standard blueprint using the retrofitting utility.

### 1. Pre-flight Check in Dry-Run
Run the organizer inside your project folder:
```bash
cd ~/repositories/projects/my-old-project
./organize-repository.sh
```
The utility scans the codebase, identifies existing files (such as python scripts or configuration directories), and prints the planned moves. No edits take place on disk.

### 2. Reorganizing on a Feature Branch
To safely isolate changes, run the live migration on a new Git feature branch:
```bash
./organize-repository.sh -b feature/standardize-layout --write --verbose
```
The utility automatically:
*   Checks out the new Git branch `feature/standardize-layout`.
*   Relocates source directories into the `backend/` folder.
*   Copies missing configurations (`.gitleaks.toml`, `.pre-commit-config.yaml`).
*   Installs the Cursor rules and the `post-commit` hook.
*   Stages and commits the changes under the message *"Retrofit repository layout to standard 4-folder blueprint"*.

Now you can review the git diff, test the project makefile, and push the branch to open a pull request!

---

## Part 13: Detailed Analysis of Linters and Formatters

High-quality linters and code formatters are essential to prevent styling arguments and bugs during pull request reviews. In this section, we compare the linting tools pre-configured inside our templates:

### 1. Ruff (Python)
Ruff is an extremely fast Python linter and formatter written in Rust. It replaces tools like Flake8, Black, isort, and autoflake, executing checks up to 100 times faster. By configuring Ruff inside our standard `pyproject.toml`, developers gain instant feedback on imports organization, unused variables, and style infractions:
*   **Fast execution**: Because it runs natively, it reduces local pre-commit check times to milliseconds.
*   **Autofix capabilities**: Integrates code replacement capabilities that fix common warnings dynamically on save.

### 2. Shellcheck (Bash)
Shellcheck is a static analysis tool for shell scripts. It flags syntax issues, non-portable commands, and subtle logic errors:
*   **Common warnings**: Catching variables that lack double quotes (triggering word splitting), unhandled command failures, and non-standard shell expansion.
*   **Bypassing warnings**: Developers can selectively disable checks by adding comments (e.g. `# shellcheck disable=SC2086`) above specific lines.

### 3. ESLint & TypeScript compiler (React/TS)
For frontend code, ESLint enforces coding patterns and catches bugs. In our templates, ESLint works alongside the TypeScript compiler (`tsc`) to validate components, verify hooks rules (such as `react-hooks/rules-of-hooks`), and confirm props typing.

---

## Part 14: Integrating Git Hooks and Secret Scanning (GitLeaks)

Securing codebases against leaked API credentials is one of the most critical aspects of modern DevOps. By combining Git hooks with GitLeaks, we establish a local security perimeter that prevents leaks before code is committed.

### How Pre-commit Works
Git hooks are scripts triggered during specific Git lifecycle events (like `pre-commit`, `commit-msg`, `post-commit`). The `pre-commit` framework manages these hooks. When a developer runs `git commit`:
1.  **Intercepting changes**: The pre-commit runner intercepts the staged files.
2.  **Running checks**: It executes configured checks (Ruff, ESLint, shellcheck, and GitLeaks) in parallel.
3.  **Aborting on failure**: If any check fails, the commit process is aborted, preventing modifications from registering in your Git log.

### How GitLeaks Scans for Keys
GitLeaks uses regular expressions and entropy calculations to check file diffs. It scans for patterns resembling:
*   AWS access keys and secret tokens.
*   GitHub OAuth credentials and personal access tokens.
*   Database connection strings with embedded passwords.
*   Private SSH keys.

If a credential is found, GitLeaks halts the commit and outputs the exact file path and line number of the leak, keeping your repository secure.

---

## Part 15: Frequently Asked Questions (FAQ)

### Q1: Can I customize the four default directories in the blueprint?
The root folders (`docs/`, `scripts/`, `frontend/`, and `backend/`) are standardized. While you can add directories or nest subdirectories (e.g., `scripts/db/` or `backend/configs/`), you should avoid creating new top-level directories in the root. Keeping a uniform root directory structure across all projects in your team enables sharing CI/CD pipelines, enforcer rules, and deployment scripts without refactoring.

### Q2: What happens if I have an existing project that does not match these stacks?
The `organize-repository.sh` utility is designed to handle this gracefully. By default, it moves unrecognized root directories or loose scripts into standard fallbacks (like `scripts/` or `backend/`). For custom setups, you can run the script with `--write` to lay down the baseline folder structure and configurations, and then manually drag and drop your application folders into place.

### Q3: How do I handle GitLeaks false positives in tests?
Occasionally, GitLeaks may flag fake test credentials (such as dummy tokens or dummy certificate strings) as leaks. You can handle this by adding a `.gitleaksignore` file in the root directory, listing the specific files (e.g., `backend/tests/test_main.py`) or rule IDs to skip during scans. Alternatively, you can add inline comments to bypass checks on specific lines.

---

## Conclusion

Standardizing repository directories ensures structural sanity across projects. By using the `setup-repository.sh` and `organize-repository.sh` utilities, you can enforce the 4-folder blueprint automatically with zero manual file moves, full validation pipelines, and instant local and remote repository synchronization. 

You can checkout the latest version of these tools inside the [feature/repo-templates](https://github.com/Richie086/scripts-public/tree/feature/repo-templates/projects/repo-templates) branch of the `scripts-public` repository.
