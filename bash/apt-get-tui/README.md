# `apt-get-tui.sh` — Text User Interface for Apt / Apt-Get

A terminal-based menu system (TUI) for managing software packages on Debian and Ubuntu Linux systems. It simplifies standard `apt-get`, `apt-cache`, and `apt-mark` operations into an interactive, categorized interface with TAB auto-completion.

---

## Features

- **Categorized Dashboard**: Side-by-side vertical columns grouping common apt tasks (Find/Inspect, Install/Remove, Maintenance, Pinning/Sources, Other).
- **TAB Auto-Completion**: Integrated with `rlwrap` to provide real-time tab completion when searching, installing, or removing packages.
- **Theme Support**: Features dynamic 24-bit color themes (Catppuccin Latte light mode and Ayu Dark mode) toggleable via CLI flags (`--dark`/`--light`) or within the TUI.
- **Apt Proxy Configuration**: Built-in wizard to configure `/etc/apt/apt.conf.d/99proxy` for HTTP and HTTPS proxies.
- **Safety First**: Displays exact command line strings (`$ sudo apt-get ...`) before execution.

---

## Usage

```bash
# Make the script executable
chmod +x apt-get-tui.sh

# Launch the interactive menu (default light mode)
./apt-get-tui.sh

# Launch directly in Dark Mode
./apt-get-tui.sh --dark
```

---

## Dependencies

- **Debian / Ubuntu** environment (`apt-get`).
- **`rlwrap`** (optional, recommended for package name auto-completion; the script will prompt to install it if missing).
