<!-- AUTO-GENERATED MERMAID START -->
<!-- This Mermaid diagram is auto-generated. Do not edit directly. -->

## Directory structure

<details>
<summary>Show directory tree diagram for `bash`</summary>

```mermaid
graph TD
	root["bash"]:::root --> n1("script-public-merge"):::folder
	root["bash"]:::root --> n2("user_manager"):::folder
	root["bash"]:::root --> n3("apache-proxy-wizard"):::folder
	root["bash"]:::root --> n4("openssl-certtool"):::folder
	root["bash"]:::root --> n5("remove_user"):::folder
	root["bash"]:::root --> n6["README.md"]:::file-md
	root["bash"]:::root --> n7["apt-get-tui.sh"]:::file-sh
	root["bash"]:::root --> n8["ai-devbox-init.sh"]:::file-sh
	n1 --> n1_2["README.md<br>script-public-merge.sh"]:::file-bundle
	n2 --> n2_2["README.md<br>user_manager.sh"]:::file-bundle
	n3 --> n3_2["README.md<br>apache-proxy-wizard.sh"]:::file-bundle
	n4 --> n4_2["openssl-certtool.sh<br>README.md"]:::file-bundle
	n5 --> n5_3["remove_user.md<br>README.md<br>remove_user.sh"]:::file-bundle
classDef root fill:#2563eb,stroke:#1e40af,stroke-width:2px,color:#ffffff;
classDef folder fill:#fbbf24,stroke:#d97706,stroke-width:1px,color:#451a03;
classDef file-bundle fill:#e2e8f0,stroke:#64748b,stroke-width:1px,color:#334155;
classDef file-md fill:#dbeafe,stroke:#3b82f6,stroke-width:1px,color:#1e3a8a;
classDef file-sh fill:#ccfbf1,stroke:#0d9488,stroke-width:1px,color:#134e4a;
```

</details>

<!-- AUTO-GENERATED MERMAID END -->

# AI Devbox Init Script

This directory contains `ai-devbox-init.sh`, an interactive Ubuntu/Debian bootstrap script for building a modern development environment quickly and consistently.

## What This Script Does

`ai-devbox-init.sh` provisions a development workstation or server with selectable tooling for:

- Core development: `git`, `gh`, `docker`, `python`, `nodejs`
- CLI extras: `ollama`, `jq`/`yq`, `btop`, `bat`, `fzf`
- Productivity tools: `ripgrep`, `httpie`, `sqlite3`, `postgresql-client`, `direnv`
- TUI tools: `lazygit`, `eza`, `fd-find`, `delta`, `tldr`, `neovim`
- GUI tools (desktop mode): `dbeaver-ce`, `remmina`, `alacritty`, `kitty`, `inkscape`, `gimp`
- IDEs (desktop mode): VS Code, Cursor, Antigravity IDE
- Python AI environment setup in `~/ai_dev_env`

It uses `gum` to provide a guided, menu-based experience and supports both dry-run and live install modes.

## Why Use It

Use this script when you want:

- Fast and repeatable machine setup
- A single guided flow for server and desktop profiles
- Clear dry-run previews before making changes
- Apt-first install strategy with selective upstream fallback where needed
- Optional alias prompts and lightweight post-install verification output

## How It Works

At a high level, the script runs in these stages:

1. Validates command flags and mode
2. Requests `sudo` (live mode only)
3. Ensures `gum` is available for interactive prompts
4. Collects selections for environment and tool groups
5. Displays a full action plan in dry-run mode, then exits
6. Performs installations in live mode by selected categories
7. Applies selected shell integration (for example `direnv` hook, optional aliases)
8. Prints installed-tool checks and final next steps

## Usage

From repository root:

```bash
./bash/ai-devbox-init.sh --help
./bash/ai-devbox-init.sh --dry-run
./bash/ai-devbox-init.sh --run
```

From the `bash/` directory:

```bash
./ai-devbox-init.sh --help
./ai-devbox-init.sh --dry-run
./ai-devbox-init.sh --run
```

## Flags

- `-h`, `--help`: show usage information and exit
- `-n`, `--dry-run`: show planned actions only, no changes
- `-r`, `--run`: execute full interactive installation

Behavior:

- If no flag is provided, help is shown and the script exits.
- `--run` and `--dry-run` are mutually exclusive.

## Notes and Safety

- Designed for Ubuntu/Debian systems with `apt`.
- Live mode modifies system packages, apt sources, and some user config files.
- Dry-run mode requires `gum` to render the interactive flow and plan output.
- Some GUI packages are large downloads and are intentionally opt-in.
- Alias changes are prompted before being written.

## Typical Workflow

1. Start with dry run:

```bash
./bash/ai-devbox-init.sh --dry-run
```

2. Review the printed plan and selections.
3. Run live install:

```bash
./bash/ai-devbox-init.sh --run
```

4. Reopen terminal session and activate the Python env if selected:

```bash
source ~/ai_dev_env/bin/activate
```
