# Shell Alias & Function Suggester

`suggest_aliases.py` is a Python utility that analyzes your command history (from `.bash_history` or `.zsh_history`) to identify commands you run frequently. It generates clean, conflict-free shorthand aliases and functions, and offers to add them to your shell configuration (like `~/.bash_aliases` or `~/.bashrc`) with safety backups.

## Key Features

1. **Dry-run by Default**: Does not write any configurations unless explicitly approved or run with `--apply` or `--interactive` flags.
2. **Recency Weighting**:
   - Applies a weighted score to command history based on how recently the command was run.
   - Most recent commands carry a `2.0` weight, middle commands `1.5`, and older commands `1.0`.
   - Ensures that recent work patterns appear first in recommendations.
3. **Service Suite Recommendations**:
   - Automatically detects systemd service control interactions (like `systemctl start/stop/restart/status <service>`) and journalctl unit queries (`journalctl -u <service>`).
   - Proposes a cohesive suite of control shortcuts:
     - `[service]-status` -> `[sudo] systemctl status [service]`
     - `[service]-start` -> `[sudo] systemctl start [service]`
     - `[service]-stop` -> `[sudo] systemctl stop [service]`
     - `[service]-restart` -> `[sudo] systemctl restart [service]`
     - `[service]-journalctl` -> `[sudo] journalctl -u [service] -f`
4. **Shell Function Generation**:
   - Scans history for common multi-step sequences where standard aliases are insufficient (e.g. `mkdir dirname && cd dirname`).
   - Proposes a custom shell function instead of a static alias.
   - Example function:
     ```bash
     mkcd() {
         mkdir -p "$1" && cd "$1"
     }
     ```
5. **Configuration Sourcing Verification**:
   - If writing to `~/.bash_aliases`, automatically verifies whether it is sourced in your `~/.bashrc`.
   - If not sourced, prompts to safely append the sourcing block with a configuration backup first.

## File Locations

- Script: [suggest_aliases.py](file:///home/rtroiano/repositories/scripts/python/suggest_aliases.py)
- Documentation: [suggest_aliases.md](file:///home/rtroiano/repositories/scripts/markdown/suggest_aliases.md)

## Usage

```bash
python3 ~/repositories/scripts/python/suggest_aliases.py [options]
```

### Options

- `-f`, `--history-file <path>`: Command history file path (defaults to auto-detecting `~/.bash_history` or `~/.zsh_history`).
- `-n`, `--limit <num>`: Max general frequency aliases to display (default: `15`).
- `-m`, `--min-uses <num>`: Minimum command appearances in history to consider (default: `3`).
- `-i`, `--interactive`: Walk through suggestions one by one, giving options to accept, rename, or skip.
- `-d`, `--dest <path>`: Shell profile target file (defaults to `~/.bash_aliases` if exists, otherwise `~/.bashrc`).
- `-a`, `--apply`: Commit selections without prompting at the end.
