# Idea Forge

Personal idea tracker with a built-in local git server — host repos, browse files, open pull requests, and auto-version entries. No GitHub required.

## Features

- Capture projects, sites, bookmarks, ideas, agent notes, AI rulebooks, and VS Code workspaces
- Category templates for new entries
- Related-entry linking
- Quick capture + pins
- JSON export at `/export/entries.json`
- JSON import (admin dry-run then apply)
- Full-text search (SQLite FTS5) across titles, notes, tags, URLs, and attachment names
- Collections / stacks to group related entries
- Media attachments (PDF, Word, images, audio, HTML/CSS/Markdown/config) with add-to-notes
- Local bare git repos with clone/push over **HTTP (token)** and **SSH (keys)**
- Web file browser (tree, blob, commits, diffs)
- Pull requests (open, diff, merge, close)
- Garden repo auto-commits every entry change as Markdown
- Admin panel + settings for tokens and SSH keys
- AI Assist (ChatGPT, Grok, Gemini, Claude, GitHub Models) for master prompt generation, feature suggestions, scaffolding, deployment script planning, format/elaborate, and security review
- External tracker IDs (Jira, Bitbucket, GitHub) with optional deep-link templates
- Local path browser for the URL/path field (admin, allowlisted roots)
- Ingest AGENTS.md → timestamped Agent Instruction entries (logged + garden-versioned)
- Mono UI with GitHub markdown light/dark themes

## Setup

```bash
cd projects/idea-tracker
pip3 install --user -r requirements.txt   # or use a venv
```

Requires the `git` binary on `PATH`.

## Run

```bash
python3 app.py
```

Open [http://127.0.0.1:5050](http://127.0.0.1:5050).

Default admin password: `seedbank` (change it under **Admin**).

### First-time git access

1. Log in → **Settings**
2. Create a personal access token (copy it once)
3. Optionally add an SSH public key
4. Create a repository under **Repos** (or “Create linked repo” on an entry)

Clone examples:

```bash
# HTTP (password = token)
git clone http://127.0.0.1:5050/git/my-project.git
# username: git
# password: <token>

# SSH
git clone ssh://git@127.0.0.1:2222/my-project.git
```

The `seedbank-garden` repo is **fetch-only** (entry history).

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `SEEDBANK_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` for LAN) |
| `SEEDBANK_PORT` | `5050` | HTTP port |
| `SEEDBANK_PUBLIC_HOST` | bind host (`0.0.0.0` → `127.0.0.1`) | Host printed in clone URLs |
| `SEEDBANK_SSH` | `1` | Enable embedded SSH git server |
| `SEEDBANK_SSH_PORT` | `2222` | SSH git port |
| `SEEDBANK_DEBUG` | `1` | Flask debug (reloader disabled when SSH on) |
| `SEEDBANK_DATA` | `./data` | Data directory |
| `SEEDBANK_SECRET` | dev default | Flask session secret |
| `SEEDBANK_ADMIN_PASSWORD` | `seedbank` | Initial admin password (first boot only) |
| `SEEDBANK_OPENAI_API_KEY` | — | Optional OpenAI key (Settings UI preferred) |
| `SEEDBANK_XAI_API_KEY` | — | Optional xAI / Grok key |
| `SEEDBANK_GOOGLE_API_KEY` | — | Optional Gemini key |
| `SEEDBANK_ANTHROPIC_API_KEY` | — | Optional Claude key |
| `SEEDBANK_GITHUB_TOKEN` | — | Optional GitHub Models / Copilot-compatible token |
| `SEEDBANK_AI_MOCK` | `0` | When `1`, Assist returns mock drafts (tests) |
| `SEEDBANK_FS_ROOTS` | — | Optional pathsep-separated browse roots |

## Companion plugins

- [Antigravity export plugin](../idea-forge-antigravity-export/README.md) — export Antigravity's global/project instruction files (`GEMINI.md`, `AGENTS.md`, `.agent/rules/*.md`) into Idea Forge entries.

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Bump [VERSION](VERSION) and add an entry there whenever a new feature is implemented.

## AI Assist actions (per item)

From each item page under **Assist**, you can run actions against the current item context only (title/category/status/tags/url/notes + attachment names and tracker IDs):

- **Master Prompt**: generates a reusable copy/paste prompt for external AI systems.
- **Suggest Features**: proposes additional feature ideas with impact and complexity (always between 5 and 10 suggestions).
- **Create Scaffold**: proposes architecture and implementation scaffolding (platform, OS, languages, database, frontend/backend, system type).
- **Deployment Script**: proposes deployment automation options and script templates for Proxmox VM, VMware VM, Container, Azure VM, Amazon EC2, Amazon containers, VirtualBox, and Virt Manager.
- **Format / Restructure**, **Elaborate**, and **Security Check** remain available.

When multiple providers are configured and enabled, Assist lets you choose the provider at run time for each action.

Assist-generated draft previews are capped at 20,000 characters per action run.

When applying an Assist draft to notes, Idea Forge prepends an H1 AI warning block to each generated Assist section, then normalizes Markdown formatting so headings are cleaned up, ordered lists are renumbered sequentially, and unclosed fenced code blocks are safely closed. Re-applying the same Assist action updates that action's existing section instead of duplicating it.

## Deploy (AWS free-tier Docker)

See [markdown/idea-forge-aws-docker-deploy.md](../../markdown/idea-forge-aws-docker-deploy.md).

```bash
./deploy_aws_docker.sh                 # dry-run
AWS_REGION=us-west-1 ./deploy_aws_docker.sh --apply
```

Local Compose (optional):

```bash
cp .env.example .env   # set secrets
docker compose up --build
```

## Smoke test

```bash
python3 smoke_test.py
```

Uses a temporary data directory; does not touch your real `data/`.

```
data/
  seedbank.db
  repos/<slug>.git      # bare repos
  garden/               # worktree for entry versioning
  ssh/host_key          # SSH host key
```

All of the above (except `.gitkeep` placeholders) are gitignored.
