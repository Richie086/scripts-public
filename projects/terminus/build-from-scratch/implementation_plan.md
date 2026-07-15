# Implementation Plan - Terminus Master Prompt Generation

This document outlines the design and proposed content for the master prompt that will enable another instance of Antigravity (or another AI assistant) to build the **Terminus Network Operations Monitor** application from scratch.

---

## 1. Goal Description

The user wants a **master prompt** to reconstruct the Terminus monitoring app. Through research, we have identified that Terminus is a standalone network operations monitor with the following components:
- **`terminus.py`**: A unified Python 3 script that operates in multiple modes:
  - **TUI (Terminal User Interface)**: Default execution. Shows a dashboard with environments, nodes, live statuses, average ping latency, down times, and a 24-point uptime sparkline history. Uses raw `termios`/`tty` capture and ANSI sequences for render drawing without `curses`.
  - **Daemon Mode (`--daemon`)**: Periodic parallel ping sweeps utilizing `ThreadPoolExecutor` and updating status files under `~/.config/terminus/status/`.
  - **Web Mode (`--web`)**: BaseHTTPRequestHandler-based server exposing the HTML dashboard, admin configuration pages, and an Nginx metrics visualizer.
  - **CLI Commands**: Modifiers for adding/deleting nodes, stopping services, etc.
- **`build.sh`**: A shell script to compile/validate syntax.
- **`deploy.sh`**: A deployment bash script that syncs code to the remote server, configures an Nginx reverse-proxy (with Basic Auth protection for write/admin paths), and provisions systemd service configs.
- **`DEPLOYMENT.md`**: Architectural overview and operations documentation.

Our objective is to compose a master prompt that specifies all functional and design requirements (such as the Dracula/Nord aesthetic, the termios raw input loop, the 24-character sparkline history tracking, the Nginx reverse proxy basic auth integration, and the systemd unit files).

---

## 2. Proposed Changes

We will generate a markdown artifact:
- `[NEW] master_prompt.md`: The finalized master prompt ready to copy-paste.

The master prompt will include:
1. **App Architecture Overview**: De-coupled architecture (Daemon, Web, CLI, TUI).
2. **Configuration & Storage Spec**: YAML config at `~/.config/terminus/config.yaml` and status files at `~/.config/terminus/status/*.status`.
3. **`terminus.py` Detailed Specification**:
   - Argument parser routes.
   - Sweeper daemon logic (Thread pool execution, standard `ping` command invocation, response parsing, and shifting 24-point sparkline strings).
   - TUI Console Interface (Clear screen via ANSI codes, tab-based environment switching, arrow-key row selection, process status panel, raw `termios` setup).
   - Web Server pages: Public Dashboard, Admin Dashboard (protected by Basic Auth via Nginx), and Nginx metrics (pulling from loopback stub status).
4. **Validation and Build Script**: Check syntax using `py_compile`.
5. **Deployment Automation**: Nginx proxy configuration, basic authentication provisioning (generation of `.terminus_htpasswd` using `openssl`), and systemd `.service` files creation.
6. **Code Aesthetics Guidelines**: Dracula color scheme variables, console output formatting, strict shell scripting conventions (`set -euo pipefail`).

---

## 3. Verification Plan

Since we are generating a prompt, we will verify:
- The clarity and completeness of the prompt by verifying that it covers all details of the existing codebase.
- The formatting and structure of the markdown.
