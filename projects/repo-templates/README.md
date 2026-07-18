# Standardized Project Templates & Bootstrapping Tools

This repository contains tools and boilerplate templates to bootstrap new projects or retrofit existing ones to a standardized 4-folder project blueprint. It integrates automated unit testing, static code linting, secrets/PII scanning, dynamic GitHub repository creation, and auto-updating README documentation.

---

## The Standard Blueprint Layout

Every project scaffolded or retrofitted contains the following directory tree:
```
your-project/
├── docs/             # Specifications, planning notes, logs, and guides
├── scripts/          # Automation scripts (DevOps, database, utilities)
├── frontend/         # Web application code (React, TypeScript, CSS, static assets)
├── backend/          # Server logic, APIs, and databases (FastAPI, Python)
├── .cursor/          # Cursor editor global rule settings
├── .github/          # GitHub Actions CI/CD workflows and dependabot configs
├── .gitignore        # Standard git ignore definitions
└── README.md         # Auto-generating README ( Mermaid file tree + recent changes )
```

---

## 1. Bootstrapping New Projects (`bootstrap.sh`)

Use `bootstrap.sh` to scaffold a brand-new project under `~/repositories/projects/`.

### Default Safety: Dry-Run
By default, running this script executes a **dry-run**. It checks your environment and prints out a summary of the directories and configuration files it would create without writing anything to disk.

### Usage
```bash
./bootstrap.sh <project-name> <stack-type> [options]
```

### Stack Types
* **`python`**: Scaffolds a Python backend app using FastAPI, uvicorn, Ruff, and Pytest.
* **`node-vite`**: Scaffolds a React + TypeScript frontend web app using Vite and ESLint.
* **`shell`**: Scaffolds automation scripts using Bash/Python CLI scripts, Shellcheck linting, and Bats unit testing.
* **`powershell`**: Scaffolds PowerShell Core scripts (`.ps1`) with PSScriptAnalyzer linting and Pester unit testing.

### Options
* `-h, --help` : Show help information.
* `--write, --apply` : **Required** to actually write changes to disk and create files.
* `-y, --yes` : Skip interactive review prompts (non-interactive mode).
* `--public` : Scaffold as a public repository (default is private).
* `--license TYPE` : License for public repos: `mit`, `gpl3`, or `apache2` (default: `gpl3`).
* `--topic TOPIC` : Add a topic tag to the created GitHub repository.

### Examples
**Dry-run (Check planned actions):**
```bash
./bootstrap.sh my-new-app node-vite
```

**Live Run (Create a private React app + GitHub remote):**
```bash
./bootstrap.sh my-new-app node-vite --write
```

---

## 2. Retrofitting Existing Projects (`retrofit.sh`)

Use `retrofit.sh` to reorganize an existing project repository into the standardized 4-folder blueprint.

### Default Safety: Dry-Run
Just like `bootstrap.sh`, this script runs in **dry-run** mode by default. It scans your existing files and lists the exact layout changes it would make before applying them.

### Usage
```bash
./retrofit.sh [options]
```

### Options
* `-h, --help` : Show help information.
* `-r, --repo PATH` : Path to the target repository (default: current directory `.`).
* `-b, --branch NAME` : Create and check out a new Git feature branch before applying migrations.
* `--write, --apply` : **Required** to execute the live re-organization.
* `-v, --verbose` : Output detailed step-by-step logging of file moves.
* `-f, --force` : Bypass Git working directory cleanliness checks.
* `--install-gh` : Automated installer for the GitHub CLI client (`gh`).

### Reorganization Rules
* Source folders like `src/` or `tests/` are automatically mapped to `backend/` (if Python layout is detected) or `frontend/` (if Vite layout is detected).
* Root files like `*.py` go to `backend/`, and `*.sh` scripts go to `scripts/bash/`.
* Root metadata configurations (like `.env`, `docker-compose.yml`, `.gitignore`, `README.md`, `LICENSE`) are **always excluded** and retained at the root.
* Standard stack-specific `Makefile`s and `.github/workflows/test.yml` CI runners are copied over if missing.

### Examples
**Dry-run (Scan current directory):**
```bash
./retrofit.sh
```

**Live Run (Move files on a new Git feature branch):**
```bash
./retrofit.sh -b feature/reorg --write --verbose
```

---

## Toolchain Setup & Dependencies

To take full advantage of linting, testing, and secret scanning, ensure the following utilities are installed:

### 1. GitHub CLI (`gh`)
If not installed, install it automatically via:
```bash
./retrofit.sh --install-gh
```

### 2. Secrets & PII Scanning (`gitleaks` & `pre-commit`)
Gitleaks prevents committing API keys, tokens, or credentials to Git. Install them via your package manager:
```bash
# macOS
brew install gitleaks pre-commit

# Debian/Ubuntu
sudo apt install gitleaks pre-commit
```
On bootstrap or retrofit, Git hooks are automatically configured to run checks before every commit.
