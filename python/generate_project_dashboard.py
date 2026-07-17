#!/usr/bin/env python3
# Script Name: generate_project_dashboard.py
# Description: Automated script to scan developers' active projects, check HTTP statuses,
#              extract Git commit histories (last update, branch, commit message),
#              and generate beautiful Markdown and HTML project status dashboards.
#
# Standards: Is compatible with Python 3.7+, uses no external dependencies.

import os
import json
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Config and output paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = SCRIPT_DIR / "projects_config.json"
MD_OUTPUT_PATH = REPO_ROOT / "markdown" / "PROJECT_DASHBOARD.md"
HTML_OUTPUT_PATH = REPO_ROOT / "web" / "index.html"

def load_projects():
    if not CONFIG_PATH.exists():
        print(f"Config file not found at {CONFIG_PATH}")
        return []
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def check_http_status(url):
    if not url:
        return "UNKNOWN", "No URL configured"
    try:
        # Create request with user-agent to bypass basic bot blocks
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (ExitCodeAutomations Dashboard)'}
        )
        # Timeout set to 3 seconds to keep script fast
        with urllib.request.urlopen(req, timeout=3.0) as response:
            code = response.getcode()
            if 200 <= code < 400:
                return "ONLINE", f"HTTP {code}"
            return "ONLINE", f"HTTP {code}"
    except urllib.error.HTTPError as e:
        # Auth errors (e.g. 401, 403) still mean the web app is alive!
        return "ONLINE", f"HTTP {e.code} (Auth/Restricted)"
    except Exception as e:
        return "OFFLINE", str(e)

def get_git_info(local_path):
    if not local_path or not os.path.isdir(local_path):
        return {
            "exists": False,
            "branch": "N/A",
            "commit": "N/A",
            "date": "N/A",
            "message": "N/A",
            "author": "N/A"
        }
    
    # Check if directory is a git repo
    git_dir = os.path.join(local_path, ".git")
    if not os.path.exists(git_dir):
        return {
            "exists": True,
            "branch": "Non-Git Folder",
            "commit": "N/A",
            "date": "N/A",
            "message": "N/A",
            "author": "N/A"
        }

    try:
        # 1. Get current branch
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=local_path, stderr=subprocess.DEVNULL
        ).decode().strip()

        # 2. Get last commit details: hash | author | date | subject
        git_log = subprocess.check_output(
            ["git", "log", "-1", "--format=%h|%an|%cd|%s", "--date=format:%Y-%m-%d %H:%M:%S"],
            cwd=local_path, stderr=subprocess.DEVNULL
        ).decode().strip()

        commit_hash, author, date, subject = git_log.split("|", 3)

        return {
            "exists": True,
            "branch": branch,
            "commit": commit_hash,
            "date": date,
            "message": subject,
            "author": author
        }
    except Exception as e:
        return {
            "exists": True,
            "branch": "Git Error",
            "commit": "N/A",
            "date": "N/A",
            "message": "N/A",
            "author": "N/A"
        }

def generate_markdown(projects_data, scan_time):
    lines = [
        "# Exit Code Automations: Project Status Dashboard",
        f"*Last Scanned: {scan_time}*",
        "",
        "This dashboard is automatically generated to track the status, deployment nodes, and recent changes of active company repositories.",
        "",
        "## Active Project Overview",
        "",
        "| Project | Status | Health / Code | Active Branch | Last Update | Recent Commit |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for p in projects_data:
        status_emoji = "🟢 ONLINE" if p["status"] == "ONLINE" else "🔴 OFFLINE" if p["status"] == "OFFLINE" else "⚪ UNKNOWN"
        
        # Format links
        name_link = f"[{p['name']}]({p['url']})" if p['url'] else p['name']
        git = p["git"]
        git_info = f"`{git['commit']}`" if git["commit"] != "N/A" else "N/A"
        
        lines.append(
            f"| **{name_link}** | {status_emoji} | {p['details']} | `{git['branch']}` | {git['date']} | {git_info} - *{git['message']}* |"
        )

    lines.append("\n## Detailed Project Paths")
    for p in projects_data:
        lines.append(f"\n### {p['name']}")
        lines.append(f"- **Description**: {p['description']}")
        lines.append(f"- **Local Directory**: `{p['local_path']}`")
        lines.append(f"- **URL**: [{p['url']}]({p['url']})")
        if p["git"]["exists"]:
            lines.append(f"- **Git Status**: Branch `{p['git']['branch']}` | Author: {p['git']['author']} | Commit: `{p['git']['commit']}`")

    os.makedirs(MD_OUTPUT_PATH.parent, exist_ok=True)
    with open(MD_OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"Markdown dashboard generated at {MD_OUTPUT_PATH}")

def generate_html(projects_data, scan_time):
    cards_html = []
    
    for p in projects_data:
        status_class = "status-online" if p["status"] == "ONLINE" else "status-offline"
        status_text = p["status"]
        git = p["git"]
        
        git_details = ""
        if git["exists"] and git["commit"] != "N/A":
            git_details = f"""
            <div class="git-details">
                <p><strong>Active Branch:</strong> <span class="badge">{git['branch']}</span></p>
                <p><strong>Last Update:</strong> {git['date']}</p>
                <p><strong>Commit:</strong> <code class="commit-hash">{git['commit']}</code></p>
                <p><strong>Message:</strong> <em>"{git['message']}"</em></p>
                <p><strong>Author:</strong> {git['author']}</p>
            </div>
            """
        else:
            git_details = f"""
            <div class="git-details">
                <p><strong>Folder Status:</strong> <span class="badge">{"Non-Git Folder" if git["exists"] else "Missing Directory"}</span></p>
            </div>
            """

        cards_html.append(f"""
        <div class="card">
            <div class="card-header">
                <h2>{p['name']}</h2>
                <span class="status-badge {status_class}">{status_text}</span>
            </div>
            <p class="description">{p['description']}</p>
            <p class="path"><code>{p['local_path']}</code></p>
            <div class="url-section">
                <a href="{p['url']}" target="_blank" class="btn">Launch Service</a>
                <span class="health-code">{p['details']}</span>
            </div>
            <hr class="card-divider">
            {git_details}
        </div>
        """)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exit Code Automations Dashboard</title>
    <style>
        :root {{
            --bg: #1e1e2e;
            --bg-elevated: #252538;
            --border: #44475a;
            --radius: 12px;
            --fg: #cdd6f4;
            --fg-dim: #a6adc8;
            --green: #a6e3a1;
            --red: #f38ba8;
            --blue: #89b4fa;
        }}

        body {{
            background-color: var(--bg);
            color: var(--fg);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        header {{
            text-align: center;
            margin-bottom: 40px;
            max-width: 800px;
        }}

        h1 {{
            color: #ffffff;
            margin: 0 0 10px 0;
            font-size: 2.5rem;
            letter-spacing: -0.5px;
        }}

        .scan-time {{
            color: var(--fg-dim);
            font-size: 0.95rem;
            margin: 0;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            width: 100%;
            max-width: 1200px;
        }}

        .card {{
            background-color: var(--bg-elevated);
            border-radius: var(--radius);
            padding: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(0, 0, 0, 0.45);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}

        .card-header h2 {{
            margin: 0;
            color: #ffffff;
            font-size: 1.4rem;
        }}

        .status-badge {{
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }}

        .status-online {{
            background-color: rgba(166, 227, 161, 0.15);
            color: var(--green);
            border: 1px solid var(--green);
        }}

        .status-offline {{
            background-color: rgba(243, 139, 168, 0.15);
            color: var(--red);
            border: 1px solid var(--red);
        }}

        .description {{
            color: var(--fg-dim);
            font-size: 0.95rem;
            margin: 0 0 16px 0;
            line-height: 1.5;
        }}

        .path {{
            margin: 0 0 20px 0;
            font-size: 0.85rem;
        }}

        .path code {{
            background-color: rgba(0, 0, 0, 0.25);
            padding: 6px 10px;
            border-radius: 6px;
            color: var(--blue);
            display: block;
            overflow-x: auto;
        }}

        .url-section {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}

        .btn {{
            background-color: var(--blue);
            color: #1e1e2e;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            font-size: 0.9rem;
            transition: opacity 0.2s;
        }}

        .btn:hover {{
            opacity: 0.9;
        }}

        .health-code {{
            font-size: 0.85rem;
            color: var(--fg-dim);
        }}

        .card-divider {{
            border: 0;
            border-top: 1px solid var(--border);
            margin: 0 0 16px 0;
        }}

        .git-details {{
            font-size: 0.9rem;
        }}

        .git-details p {{
            margin: 8px 0;
            color: var(--fg-dim);
        }}

        .git-details strong {{
            color: var(--fg);
        }}

        .badge {{
            background-color: var(--border);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
            color: #ffffff;
        }}

        .commit-hash {{
            background-color: rgba(0, 0, 0, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            color: var(--green);
        }}
    </style>
</head>
<body>
    <header>
        <h1>Exit Code Automations</h1>
        <p class="scan-time">System Status Dashboard • Generated at {scan_time}</p>
    </header>
    <main class="grid">
        {"".join(cards_html)}
    </main>
</body>
</html>
"""
    os.makedirs(HTML_OUTPUT_PATH.parent, exist_ok=True)
    with open(HTML_OUTPUT_PATH, "w") as f:
        f.write(html_template)
    print(f"HTML dashboard generated at {HTML_OUTPUT_PATH}")

def main():
    print("Starting Exit Code Automations scan...")
    projects = load_projects()
    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    enriched_projects = []
    for p in projects:
        print(f"Scanning {p['name']}...")
        status, details = check_http_status(p.get("url"))
        git_info = get_git_info(p.get("local_path"))
        
        enriched_projects.append({
            "name": p["name"],
            "description": p["description"],
            "local_path": p["local_path"],
            "url": p["url"],
            "status": status,
            "details": details,
            "git": git_info
        })
        
    generate_markdown(enriched_projects, scan_time)
    generate_html(enriched_projects, scan_time)
    print("System status dashboard generation completed.")

if __name__ == "__main__":
    main()
