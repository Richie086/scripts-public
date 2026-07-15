# Terminus Network Operations Monitor Rebuilder - Master Prompt

Use the following master prompt to reconstruct the Terminus Network Operations Monitor application from scratch in another environment.

***

```markdown
You are an expert system administrator and software engineer. Your task is to build the **Terminus Standalone Network Operations Monitor** from scratch. The application consists of a unified Python 3 monitor script (`terminus.py`), a local validation script (`build.sh`), an automated deployment bash script (`deploy.sh`), and a deployment architecture guide (`DEPLOYMENT.md`).

Follow the strict specifications below for code structure, storage, user interface aesthetics, and deployment configs.

---

### Project Architecture & File Structure

Create the project inside a directory `terminus/` with the following structure:
```
terminus/
├── build.sh
├── deploy.sh
├── DEPLOYMENT.md
└── terminus.py
```

---

### 1. Unified Application: `terminus.py`

Write a single executable script `terminus.py` in pure Python 3 (using standard libraries, with optional `pyyaml` import falling back to standard dictionary loading if not present).

#### A. Command Line Interface Modes
The script must check command-line arguments:
- **Default (No Arguments)**: Launches TUI mode. It must first verify whether the background daemon and web server are running by checking `~/.config/terminus/pids/daemon.pid` and `~/.config/terminus/pids/web.pid` and checking if those processes are currently running in the OS. If not running, it must spawn them in the background using `subprocess.Popen([sys.executable, __file__, "--daemon"/"--web"])` before launching the interactive console loop.
- `--daemon`: Runs the background sweeper daemon loop in the foreground.
- `--web`: Runs the web configuration HTTP server.
- `--add <env> <name> <addr> [dev_type]`: CLI helper to add a node to a specific environment.
- `--del <env> <id>`: CLI helper to delete a node by ID.
- `--stop`: Stops background services by sending `SIGTERM (15)` to the PIDs in the pid files and then removes the pid files.
- `--help` or `-h`: Prints usage and options.

#### B. Storage & Configuration Spec
- **Path Config**:
  - Base Directory: `~/.config/terminus`
  - YAML Config Path: `~/.config/terminus/config.yaml`
  - Status Directory: `~/.config/terminus/status`
  - PID Directory: `~/.config/terminus/pids`
- **Default YAML Config Layout**:
  ```yaml
  settings:
    sweep_frequency: 60
    ping_count: 5
    ping_interval: 0.2
    room_name: "Server Room B"
    physical_address: "456 Enterprise Way"
    company_name: "General Corp"
    env_1: "Tenant A"
    env_2: "Tenant B"
    env_3: "Tenant C"
  device_types: ["Server", "Router", "Switch", "Firewall", "Gateway", "Other"]
  environments:
    "Tenant A": []
    "Tenant B": []
    "Tenant C": []
  ```
- **Status Files**:
  - Saved under `~/.config/terminus/status/{environment_name_lowercase_with_underscores}.status`.
  - Format: Line-based, pipe-delimited values: `nid|status|latency|down_since|history\n`
    - `nid`: Node ID (integer).
    - `status`: "UP", "DOWN", or "PENDING".
    - `latency`: RTT latency (e.g. `2.5 ms` or `N/A`).
    - `down_since`: Time when the node went down (format `HH:MM:S`) or empty.
    - `history`: 24-character string. `1` represents UP, `0` represents DOWN, and `.` represents empty/pending. In each sweep, shift the history left and append the newest status point to the right.

#### C. Core Operations Functions
- `add_node(env, name, addr, dev_type="Server")`: Add node to config. If `name` or `addr` is missing, resolve it dynamically using forward/reverse DNS (`socket`). Assigns the next incremental ID, saves the configuration, and spawns a thread to run an immediate initial status ping.
- `delete_node(env, nid)`: Delete node from configuration and also remove its corresponding line from the environment status file.
- `run_sweeper_daemon()`: Periodic loop. Writes the current daemon PID to `daemon.pid`. For each environment's nodes, triggers concurrent sweeps using a `ThreadPoolExecutor` (max 20 workers). Use standard shell `ping` command:
  `ping -c {ping_count} -i {ping_interval} -w {ping_count + 2} {addr}`
  Extract average latency using regex `rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/`. Perform atomic writes/replaces to the status files. Sleep for `sweep_frequency` seconds between sweeps.
- `load_statuses(env)`: Reads pipe-separated status file into dictionary lookup.

#### D. Console TUI (Interactive CLI)
- **Controls**:
  - `[TAB]`: Cycle through environment tabs.
  - `[UP]` / `[DOWN]`: Select rows in the current node list.
  - `[A]`: Add node. Asks for Name, IP/Hostname, and Device Type at the bottom console line.
  - `[D]`: Delete selected node. Asks for `(y/n)` confirmation.
  - `[C]`: Open Configuration menu.
  - `[R]`: Trigger manual sweep now (runs parallel thread pool and updates status immediately).
  - `[Q]`: Quit interactive console.
- **Rendering**:
  - Draw border frames using ANSI box characters (`┌`, `┐`, `└`, `┘`, `├`, `┤`, `─`, `│`).
  - Clear console screen using `\033[H\033[J`.
  - Highlight selected node row with reverse video (`\033[7m`), but do not reverse the color sequences inside sparklines.
  - TUI Uptime History Sparkline: Render 24 characters using `\033[1;32m■\033[0m` for UP, `\033[1;31m■\033[0m` for DOWN, and `\033[1;30m·\033[0m` for empty.
  - Draw a **Host System Specs** panel at the bottom showing: Hostname, OS version (read from `/etc/os-release`), RAM Total (`/proc/meminfo`), and CPU Model (`/proc/cpuinfo`), as well as config settings (Room, Address, Company).
  - Draw process status line (Daemon: RUNNING/OFFLINE, Web Server: RUNNING/OFFLINE).
- **Keyboard Input**:
  - Do NOT use `curses`. Implement raw input mode using `termios`, `tty`, and non-blocking input checking via `select.select` on `sys.stdin` with a `0.5s` timeout. Restores termios attributes on input/exit.

#### E. Web Server Logic (`TerminusHTTPHandler`)
- Base server on `http.server.HTTPServer` listening on port `8085` (overrideable via `TERMINUS_PORT` environment variable).
- **Endpoints**:
  - `GET /`: Renders main dashboard HTML page.
  - `GET /add`: Adds a node via query string parameters. Redirects back to dashboard or admin.
  - `GET /delete`: Deletes a node by ID. Redirects back.
  - `GET /admin`: Renders admin settings HTML panel.
  - `GET /admin/save_tabs`: Saves environment tab names, renaming status files accordingly to prevent history data loss.
  - `GET /admin/save_ping`: Saves sweep configuration values.
  - `GET /admin/save_host`: Saves room location and company metadata override.
  - `GET /admin/add_type` / `/admin/del_type`: Adds or removes custom device types.
  - `GET /nginx_status`: Query loopback status `http://127.0.0.1/nginx_status_raw` using `curl` and parse active, accepts, handled, requests, reading, writing, waiting connections. Display them in a beautiful performance dashboard.
- **Web UI Aesthetics**:
  - Use Dracula colors in CSS variables:
    ```css
    --bg-base: #1e1f29;
    --bg-elevated: #282a36;
    --border: #44475a;
    --fg-base: #f8f8f2;
    --fg-dim: #6272a4;
    --green: #50fa7b;
    --red: #ff5555;
    --orange: #ffb86c;
    --purple: #bd93f9;
    --cyan: #8be9fd;
    ```
  - Body background: `#0c0d12`. Font: `'Spline Sans Mono', monospace`.
  - Design panels and headers mimicking a premium CLI terminal dashboard. Add simulated window control dots (red, yellow, green).
  - Main Table: IDs, Device Type, Node Name, Target IP, Status Badge (green for ONLINE, red for ALERT, yellow for PENDING), Latency or Down time description, and 24-character sparkline blocks (`■` or `·`).
  - System Info: Include specs at the bottom.
  - Forms: Style all inputs, selectors, and buttons to match the Dracula theme.

---

### 2. local syntax check: `build.sh`

Create a validation script `build.sh` that checks python file syntax:
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Validating terminus.py syntax..."
python3 -m py_compile terminus.py
chmod +x terminus.py

echo "Verification: checking built script syntax..."
python3 -c "import py_compile; py_compile.compile('terminus.py')"
echo "Valid! Terminus Python script is ready."
```

---

### 3. Automated Deployment Script: `deploy.sh`

Create a production deployment script `deploy.sh` incorporating strict options: `set -euo pipefail`.
- **Properties**:
  - Configurable environment variable overrides: `DEV_HOST` (default `webserver@192.168.1.80`), `SSH_KEY` (default `~/.ssh/id_webserver`), `TERMINUS_PORT` (default `8085`).
- **Steps**:
  1. Runs `./build.sh` locally.
  2. Spawns remote SSH commands to ensure `/home/webserver/terminus` is created and owned by `webserver`.
  3. Copies `terminus.py` to the target server via `scp`, sets execution permission, and deletes legacy compiled C binaries or shell files.
  4. Provisions Nginx reverse-proxy and Basic Auth credentials:
     - Check if `/etc/nginx/.terminus_htpasswd` exists. If not, prompt or generate admin credentials (`admin` / `admin` defaults) using `openssl passwd -apr1` locally and write to the remote location. Make it owned by `root:www-data` and permissioned `640`.
     - Generate Nginx server configuration block at `/etc/nginx/sites-available/default`:
       - Public route `/` proxies to `127.0.0.1:8085`.
       - Secure admin routes (`/admin`, `/delete`, `/add`) proxy to `127.0.0.1:8085` protected under basic authentication (`auth_basic_user_file /etc/nginx/.terminus_htpasswd`).
       - Metric route `/nginx_status_raw` configures `stub_status on`, restricting access to `127.0.0.1` only.
       - Tests nginx syntax (`nginx -t`) and reloads Nginx.
  5. Configures two Systemd services:
     - **`terminus-daemon.service`**: Run `/usr/bin/python3 /home/webserver/terminus/terminus.py --daemon` as user `webserver`.
     - **`terminus-web.service`**: Run `/usr/bin/python3 /home/webserver/terminus/terminus.py --web` with port environment `TERMINUS_PORT` as user `webserver`.
     - Enables and restarts both services.

---

### 4. Documentation: `DEPLOYMENT.md`

Provide a markdown document summarizing:
- **System architecture diagram** using Mermaid showing the interaction between Nginx (proxy pass, basic auth, stub status), Terminus Web Backend, Terminus Sweep Daemon, configuration folder, and the target nodes.
- **Remote security notes** on Nginx reverse proxy routes basic auth configurations.
- **Systemd service configuration files** and management commands (`systemctl status/restart/stop`, `journalctl -u -f`).
```

***

Write the code files cleanly, handling error bounds and preserving terminal/HTTP configurations properly.
