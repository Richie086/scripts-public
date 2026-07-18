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

# Check if target repo positional arg is passed as fallback
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
    # Add official github keys and repo
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

# 1. Execute gh install if requested
if [[ "$INSTALL_GH" == "true" ]]; then
  install_gh_client
  exit 0
fi

# 2. Pre-flight Target Repository Checks
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

# Cleanliness check
IS_DIRTY=false
if ! git diff --quiet || ! git diff --cached --quiet; then
  IS_DIRTY=true
fi
# Check for untracked files
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

# 3. Detect Layout type
HAS_PYTHON=false
HAS_VITE=false
HAS_SHELL=false

if [[ -f pyproject.toml ]] || [[ -f requirements.txt ]]; then
  HAS_PYTHON=true
fi
if [[ -f package.json ]] && { [[ -f vite.config.ts ]] || [[ -f vite.config.js ]]; }; then
  HAS_VITE=true
fi
# Detect if there are loose shell scripts in root (excluding target scripts)
if [[ -n "$(find . -maxdepth 1 -name "*.sh" ! -name "run.sh" ! -name "bootstrap.sh" ! -name "retrofit.sh" -print -quit 2>/dev/null)" ]]; then
  HAS_SHELL=true
fi

# Fallback: if nothing is matched, default to shell stack
if [[ "$HAS_PYTHON" == "false" && "$HAS_VITE" == "false" && "$HAS_SHELL" == "false" ]]; then
  HAS_SHELL=true
fi

# ==================================================
# Scaffolding Dry Run
# ==================================================
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
  echo "Planned Configuration Copies:"
  echo "  - Install global Cursor rule: .cursor/rules/global-rules/workspace-organization-always.mdc"
  
  # Metadata files
  for f in .gitleaks.toml .pre-commit-config.yaml .editorconfig SECURITY.md CONTRIBUTING.md; do
    if [[ ! -f "$f" ]]; then
      echo "  - Copy shared metadata configuration: $f"
    fi
  done
  
  if [[ ! -f .git/hooks/post-commit ]]; then
    echo "  - Install post-commit hook: .git/hooks/post-commit"
  fi
  
  # Stack specific dry-runs
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
  
  # Mixed coordination Makefile
  if [[ "$HAS_PYTHON" == "true" && "$HAS_VITE" == "true" ]]; then
    if [[ ! -f Makefile ]]; then
      echo "  - Install shared coordinator Makefile in root"
    fi
  fi
  
  echo "Would automatically stage and commit re-organized files."
  echo "--- DRY RUN COMPLETE ---"
  exit 0
fi

# ==================================================
# Live Re-organization execution
# ==================================================
log "INFO" "Applying live repository re-organization..."

# 1. Feature branching
if [[ -n "$BRANCH_NAME" ]]; then
  if git show-ref --quiet --verify "refs/heads/$BRANCH_NAME"; then
    log "WARNING" "Branch '$BRANCH_NAME' already exists. Switching to it..."
    git checkout "$BRANCH_NAME"
  else
    log "INFO" "Creating and switching to new branch '$BRANCH_NAME'..."
    git checkout -b "$BRANCH_NAME"
  fi
fi

# 2. Create the 4 folders
verbose_log "Creating directories: docs, scripts, frontend, backend"
mkdir -p docs scripts frontend backend

# 3. Copy shared files if missing
for f in .gitleaks.toml .pre-commit-config.yaml .editorconfig SECURITY.md CONTRIBUTING.md; do
  if [[ ! -f "$f" ]]; then
    verbose_log "Copying shared configuration: $f"
    cp "$TEMPLATE_DIR/shared/$f" "./$f"
  fi
done

# Install Cursor rule
verbose_log "Installing global Cursor rules"
mkdir -p .cursor/rules/global-rules
cp "$TEMPLATE_DIR/shared/.cursor/rules/global-rules/workspace-organization-always.mdc" .cursor/rules/global-rules/

# Distribute placeholder files where appropriate
for dir in docs scripts frontend backend; do
  if [ -z "$(ls -A "$dir" | grep -v "\.mdc" || true)" ]; then
    cp "$TEMPLATE_DIR/shared/$dir/README.md" "$dir/"
    verbose_log "Placed README placeholder in $dir/"
  fi
done

# 4. Perform dynamic migrations depending on layout
# 4.1 Python Stack migration
if [[ "$HAS_PYTHON" == "true" ]]; then
  log "INFO" "Migrating Python layout..."
  if [[ -d src ]]; then
    mkdir -p backend/src
    verbose_log "Moving src/ contents to backend/src/"
    cp -a src/. backend/src/ && rm -rf src
  fi
  if [[ -d tests ]]; then
    mkdir -p backend/tests
    verbose_log "Moving tests/ contents to backend/tests/"
    cp -a tests/. backend/tests/ && rm -rf tests
  fi
  
  # Move loose python files
  for f in *.py; do
    if [[ -f "$f" && "$f" != "scrape.py" ]]; then
      verbose_log "Moving loose script $f -> backend/"
      mv "$f" backend/
    fi
  done
  
  # Move config files
  for f in pyproject.toml requirements.txt requirements-dev.txt Makefile; do
    if [[ -f "$f" ]]; then
      verbose_log "Moving config file $f -> backend/"
      mv "$f" backend/
    fi
  done
  
  # Scaffold Makefile and workflow if missing
  if [[ ! -f backend/Makefile ]]; then
    verbose_log "Installing Python Makefile in backend/"
    cp "$TEMPLATE_DIR/python/Makefile" backend/
  fi
  if [[ ! -f .github/workflows/test.yml ]]; then
    verbose_log "Installing Python test.yml workflow"
    mkdir -p .github/workflows
    cp "$TEMPLATE_DIR/python/test.yml" .github/workflows/test.yml
  fi
fi

# 4.2 Node-Vite layout migration
if [[ "$HAS_VITE" == "true" ]]; then
  log "INFO" "Migrating Node-Vite layout..."
  for d in src public; do
    if [[ -d "$d" ]]; then
      verbose_log "Moving folder $d/ -> frontend/"
      mv "$d" frontend/
    fi
  done
  for f in package.json tsconfig.json vite.config.ts vite.config.js index.html Makefile; do
    if [[ -f "$f" ]]; then
      verbose_log "Moving config file $f -> frontend/"
      mv "$f" frontend/
    fi
  done
  
  # Scaffold Makefile and workflow if missing
  if [[ ! -f frontend/Makefile ]]; then
    verbose_log "Installing Node-Vite Makefile in frontend/"
    cp "$TEMPLATE_DIR/node-vite/Makefile" frontend/
  fi
  if [[ ! -f .github/workflows/test.yml ]]; then
    verbose_log "Installing Node-Vite test.yml workflow"
    mkdir -p .github/workflows
    cp "$TEMPLATE_DIR/node-vite/test.yml" .github/workflows/test.yml
  fi
fi

# 4.3 Shell script layout migration
if [[ "$HAS_SHELL" == "true" ]]; then
  log "INFO" "Migrating loose shell script layout..."
  # Move loose shell files (except run.sh, bootstrap.sh, retrofit.sh) to scripts/
  for f in *.sh; do
    if [[ -f "$f" && "$f" != "run.sh" && "$f" != "bootstrap.sh" && "$f" != "retrofit.sh" ]]; then
      mkdir -p scripts/bash
      verbose_log "Moving loose shell script $f -> scripts/bash/"
      mv "$f" scripts/bash/
    fi
  done
  
  # Scaffold Makefile and workflow if missing
  if [[ ! -f scripts/Makefile ]]; then
    verbose_log "Installing Shell Makefile in scripts/"
    cp "$TEMPLATE_DIR/shell/Makefile" scripts/
  fi
  if [[ ! -f .github/workflows/test.yml ]]; then
    verbose_log "Installing Shell test.yml workflow"
    mkdir -p .github/workflows
    cp "$TEMPLATE_DIR/shell/test.yml" .github/workflows/test.yml
  fi
fi

# 4.4 Mixed stack orchestration Makefile
if [[ "$HAS_PYTHON" == "true" && "$HAS_VITE" == "true" ]]; then
  if [[ ! -f Makefile ]]; then
    verbose_log "Installing shared coordinates Makefile in root"
    cp "$TEMPLATE_DIR/shared/Makefile" ./Makefile
  fi
fi

# 5. Git hook installation
if [[ ! -f .git/hooks/post-commit ]]; then
  verbose_log "Installing post-commit hook for auto-README update"
  cp "$TEMPLATE_DIR/shared/hooks/post-commit" .git/hooks/post-commit
  chmod +x .git/hooks/post-commit
fi
# Copy updater script
if [[ ! -f scripts/update-readme.sh ]]; then
  verbose_log "Installing update-readme.sh"
  mkdir -p scripts
  cp "$TEMPLATE_DIR/shared/scripts/update-readme.sh" scripts/
  chmod +x scripts/update-readme.sh
fi

# Stage and Auto-commit changes
git add -A || true
if ! git diff --cached --quiet; then
  log "INFO" "Staging and committing re-organization changes..."
  git commit -m "Retrofit repository layout to standard 4-folder blueprint"
  log "INFO" "Migration commit successfully completed!"
else
  log "INFO" "No layout adjustments were necessary (repository already standardized)."
fi

log "INFO" "Retrofit successfully applied!"
