# repo-templates

Standardized structure + secret/PII scanning for new repos.

## Layout

- `shared/` — files every repo gets regardless of stack: `.gitleaks.toml` (secret + PII rules), `.pre-commit-config.yaml`, `.github/workflows/secret-scan.yml`, `gitignore.common`, `SECURITY.md`.
- `python/` — layout for Python projects.
- `node-vite/` — layout for Vite/TS web apps (matches connectivity/omnimtu/nmap-pro style).
- `shell/` — layout for shell-script/automation repos (matches scripts/scripts-public/exitcodezero style).

## Usage

Bootstrap a new repo:

```
./bootstrap.sh <repo-name> <python|node-vite|shell> [--public] [--topic <topic>]
```

This creates `~/repositories/<repo-name>` with the shared security tooling plus the
stack layout, runs `git init`, and installs the pre-commit hook if `pre-commit` is
available.

## One-time local setup

```
# gitleaks (secret/PII scanner)
brew install gitleaks        # macOS
# or download a release binary: https://github.com/gitleaks/gitleaks/releases

# pre-commit (hook runner)
pipx install pre-commit      # or: pip install --user pre-commit
```

## Retrofitting an existing repo

```
cp shared/.gitleaks.toml shared/.pre-commit-config.yaml <existing-repo>/
mkdir -p <existing-repo>/.github/workflows
cp shared/.github/workflows/secret-scan.yml <existing-repo>/.github/workflows/
cp shared/SECURITY.md <existing-repo>/
cat shared/gitignore.common >> <existing-repo>/.gitignore   # dedupe manually after
cd <existing-repo> && pre-commit install
```
