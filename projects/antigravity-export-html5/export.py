import os
import json
import shutil
import re
from pathlib import Path
from datetime import datetime

SECRET_PATTERNS = [
    re.compile(r"ghp_[a-zA-Z0-9]{36,255}"),
    re.compile(r"gho_[a-zA-Z0-9]{36,255}"),
    re.compile(r"ghu_[a-zA-Z0-9]{36,255}"),
    re.compile(r"ghs_[a-zA-Z0-9]{36,255}"),
    re.compile(r"ghr_[a-zA-Z0-9]{36,255}"),
]

def scrub_string(val):
    if not isinstance(val, str):
        return val
    for p in SECRET_PATTERNS:
        val = p.sub("[REDACTED]", val)
    return val

def scrub_secrets(data):
    if isinstance(data, dict):
        scrubbed = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(s in k_lower for s in ["token", "password", "key", "secret", "credential", "auth", "passwd"]):
                scrubbed[k] = "[REDACTED]"
            else:
                scrubbed[k] = scrub_secrets(v)
        return scrubbed
    elif isinstance(data, list):
        return [scrub_secrets(item) for item in data]
    elif isinstance(data, str):
        return scrub_string(data)
    else:
        return data

def export_configurations():
    # Setup directories
    project_dir = Path("/home/rtroiano/repositories/scripts-public/scripts-public/projects/antigravity-export-html5")
    dist_dir = project_dir / "dist"
    md_dir = dist_dir / "markdown"
    skills_out_dir = md_dir / "skills"

    # Clean and recreate directories
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    os.makedirs(skills_out_dir, exist_ok=True)

    home = Path(os.path.expanduser("~"))
    agy_cli_settings_path = home / ".gemini/antigravity-cli/settings.json"
    gemini_config_path = home / ".gemini/config/config.json"
    mcp_config_path_1 = home / ".gemini/config/mcp_config.json"
    mcp_config_path_2 = home / ".gemini/antigravity/mcp_config.json"
    global_skills_dir = home / ".gemini/skills"
    workspace_rules_path = Path("/home/rtroiano/.agents/AGENTS.md")
    workspace_skills_dir = Path("/home/rtroiano/.agents/skills")

    print("[INFO] Loading settings and configurations...")

    # Load file contents
    agy_settings = scrub_secrets(read_json(agy_cli_settings_path))
    gemini_config = scrub_secrets(read_json(gemini_config_path))
    mcp_config_1 = scrub_secrets(read_json(mcp_config_path_1))
    mcp_config_2 = scrub_secrets(read_json(mcp_config_path_2))
    workspace_rules = scrub_string(read_file(workspace_rules_path))

    # 1. Generate General Settings Markdown
    generate_settings_md(md_dir / "general_settings.md", agy_settings, gemini_config)

    # 2. Generate MCP Configuration Markdown
    generate_mcp_md(md_dir / "mcp_servers.md", mcp_config_1, mcp_config_2)

    # 3. Generate Global Skills Markdown
    generate_skills_md(md_dir / "global_skills.md", global_skills_dir, skills_out_dir, is_global=True)

    # 4. Generate Workspace Rules Markdown
    generate_rules_md(md_dir / "workspace_rules.md", workspace_rules)

    # 5. Generate Workspace Skills Markdown
    generate_skills_md(md_dir / "workspace_skills.md", workspace_skills_dir, skills_out_dir, is_global=False)

    print("[SUCCESS] Configurations successfully exported to Markdown.")

def read_json(path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to read/parse JSON: {str(e)}"}

def read_file(path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file: {str(e)}"

def generate_settings_md(out_path, agy_settings, gemini_config):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"""# General Settings Configuration

*Exported on: {now_str}*

This file contains the general configuration settings for the Antigravity CLI and the Gemini helper environments.

## Antigravity CLI Settings (`settings.json`)

"""
    if agy_settings:
        if "error" in agy_settings:
            content += f"> [!WARNING]\n> {agy_settings['error']}\n"
        else:
            # Render a summary table
            content += "### Configuration Parameters Summary\n\n"
            content += "| Parameter | Value |\n"
            content += "| :--- | :--- |\n"
            content += f"| **Model Selection** | `{agy_settings.get('model', 'Default')}` |\n"
            content += f"| **Agent Mode** | `{agy_settings.get('agentMode', 'plan')}` |\n"
            content += f"| **Color Scheme** | `{agy_settings.get('colorScheme', 'dark')}` |\n"
            content += f"| **Editor** | `{agy_settings.get('editor', 'vim')}` |\n"
            content += f"| **Allow Non-Workspace Access** | `{agy_settings.get('allowNonWorkspaceAccess', True)}` |\n"
            content += f"| **Tool Permission Mode** | `{agy_settings.get('toolPermission', 'proceed-in-sandbox')}` |\n"
            content += "\n### Permissions Configuration (`permissions.allow`)\n\n"
            allow_rules = agy_settings.get("permissions", {}).get("allow", [])
            if allow_rules:
                content += "The following commands are pre-approved to run without prompting:\n\n"
                for rule in allow_rules:
                    content += f"- `{rule}`\n"
            else:
                content += "*No pre-approved command rules configured.*\n"

            content += "\n### Trusted Workspaces\n\n"
            trusted = agy_settings.get("trustedWorkspaces", [])
            if trusted:
                for path in trusted:
                    content += f"- `{path}`\n"
            else:
                content += "*No trusted workspaces configured.*\n"

            content += "\n### Raw JSON Settings\n\n"
            content += "```json\n" + json.dumps(agy_settings, indent=2) + "\n```\n"
    else:
        content += "*No Antigravity CLI settings file found.*\n"

    content += "\n## Gemini Config (`config.json`)\n\n"
    if gemini_config:
        if "error" in gemini_config:
            content += f"> [!WARNING]\n> {gemini_config['error']}\n"
        else:
            content += "```json\n" + json.dumps(gemini_config, indent=2) + "\n```\n"
    else:
        content += "*No Gemini helper config file found.*\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

def generate_mcp_md(out_path, mcp_config_1, mcp_config_2):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"""# Model Context Protocol (MCP) Configuration

*Exported on: {now_str}*

This file summarizes the configured MCP servers used by the Antigravity agent to connect to external tools and services.

"""
    def format_mcp(mcp_config, source_name):
        res = f"## Source: {source_name}\n\n"
        if not mcp_config:
            res += f"*No MCP servers configured for this path.*\n\n"
            return res
        if "error" in mcp_config:
            res += f"> [!WARNING]\n> {mcp_config['error']}\n\n"
            return res
        
        servers = mcp_config.get("mcpServers", {})
        if not servers:
            res += f"*No servers defined under `mcpServers`.*\n\n"
            return res
        
        res += "| Server Name | Command | Arguments |\n"
        res += "| :--- | :--- | :--- |\n"
        for name, data in servers.items():
            cmd = data.get("command", "N/A")
            args = ", ".join([f"`{a}`" for a in data.get("args", [])])
            res += f"| **{name}** | `{cmd}` | {args if args else '*None*'} |\n"
        
        res += "\n### Raw JSON Configuration\n\n"
        res += "```json\n" + json.dumps(mcp_config, indent=2) + "\n```\n\n"
        return res

    content += format_mcp(mcp_config_1, "User Config (`~/.gemini/config/mcp_config.json`)")
    content += format_mcp(mcp_config_2, "Antigravity Config (`~/.gemini/antigravity/mcp_config.json`)")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

def generate_skills_md(out_path, skills_dir, skills_out_dir, is_global):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "Global" if is_global else "Workspace"
    content = f"""# {prefix} Skills Registry

*Exported on: {now_str}*

Skills are reusable packages of knowledge or workflows that teach the agent how to perform specific tasks.

"""
    if not skills_dir.exists():
        content += f"*No {prefix.lower()} skills directory found at `{skills_dir}`.*\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        return

    skills_list = []
    # Search for skills
    # Global skills are folders containing SKILL.md
    for entry in os.scandir(skills_dir):
        if entry.is_dir():
            skill_md_path = Path(entry.path) / "SKILL.md"
            if skill_md_path.exists():
                skill_content = read_file(skill_md_path)
                # Parse frontmatter name/description
                name, desc = parse_skill_metadata(skill_content, entry.name)
                
                # Copy the file to export destination
                safe_name = f"{prefix.lower()}_{entry.name}.md"
                shutil.copy2(skill_md_path, skills_out_dir / safe_name)
                
                skills_list.append({
                    "name": name,
                    "folder": entry.name,
                    "description": desc,
                    "export_file": f"markdown/skills/{safe_name}"
                })

    if skills_list:
        content += "| Skill Name | Description | Source Folder | Action |\n"
        content += "| :--- | :--- | :--- | :--- |\n"
        for s in sorted(skills_list, key=lambda x: x["name"]):
            content += f"| **{s['name']}** | {s['description']} | `{s['folder']}/` | [View Skill Documentation]({s['export_file']}) |\n"
    else:
        content += f"*No active {prefix.lower()} skills registered.*\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

def parse_skill_metadata(content, default_name):
    if not content:
        return default_name, "N/A"
    
    # Try parsing YAML frontmatter
    lines = content.splitlines()
    if len(lines) > 0 and lines[0].strip() == "---":
        yaml_lines = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            yaml_lines.append(line)
        
        metadata = {}
        for y_line in yaml_lines:
            if ":" in y_line:
                k, v = y_line.split(":", 1)
                metadata[k.strip().lower()] = v.strip().strip('"').strip("'")
        
        name = metadata.get("name", default_name)
        desc = metadata.get("description", "N/A")
        return name, desc
        
    return default_name, "N/A"

def generate_rules_md(out_path, workspace_rules):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"""# Workspace Guidelines and Rules

*Exported on: {now_str}*

These rules enforce directory organization, code standards, security scans, and custom actions within the workspace.

"""
    if workspace_rules:
        if workspace_rules.startswith("Failed to read file"):
            content += f"> [!WARNING]\n> {workspace_rules}\n"
        else:
            content += workspace_rules
    else:
        content += "*No active workspace guidelines (`AGENTS.md`) found.*\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    export_configurations()
