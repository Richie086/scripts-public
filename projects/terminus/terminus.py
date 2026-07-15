#!/usr/bin/env python3
# TERMINUS - Standalone Network Operations Monitor (Pure Python 3)
import sys
import os
import time
import re
import socket
import json
import subprocess
import threading
import select
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configuration Paths
CONFIG_DIR = os.path.expanduser("~/.config/terminus")
STATUS_DIR = os.path.join(CONFIG_DIR, "status")
PID_DIR = os.path.join(CONFIG_DIR, "pids")
YAML_PATH = os.path.join(CONFIG_DIR, "config.yaml")

DEFAULT_CONFIG = {
    "settings": {
        "sweep_frequency": 60,
        "ping_count": 5,
        "ping_interval": 0.2,
        "room_name": "Server Room B",
        "physical_address": "456 Enterprise Way",
        "company_name": "General Corp",
        "env_1": "Tenant A",
        "env_2": "Tenant B",
        "env_3": "Tenant C"
    },
    "device_types": ["Server", "Router", "Switch", "Firewall", "Gateway", "Other"],
    "environments": {
        "Tenant A": [],
        "Tenant B": [],
        "Tenant C": []
    }
}

# Ensure directories exist
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(STATUS_DIR, exist_ok=True)
os.makedirs(PID_DIR, exist_ok=True)

# Try importing pyyaml, fallback to simple flat loader/saver if not installed
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

def load_yaml():
    if not os.path.exists(YAML_PATH):
        save_yaml(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    if HAS_YAML:
        try:
            with open(YAML_PATH, "r") as f:
                data = yaml.safe_load(f)
                if not data or not isinstance(data, dict):
                    return DEFAULT_CONFIG
                # Merge defaults for top level
                for k in DEFAULT_CONFIG:
                    if k not in data:
                        data[k] = DEFAULT_CONFIG[k]
                return data
        except Exception:
            return DEFAULT_CONFIG
    else:
        # Mini-parser fallback (JSON or basic YAML-like flat parser)
        # In this workspace, pyyaml is verified to be installed.
        return DEFAULT_CONFIG

def save_yaml(data):
    if HAS_YAML:
        try:
            with open(YAML_PATH, "w") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        except Exception:
            pass

# Global Variables
config = load_yaml()

def reload_config():
    global config
    config = load_yaml()

def get_settings():
    return config.get("settings", DEFAULT_CONFIG["settings"])

def get_environments():
    settings = get_settings()
    return [
        settings.get("env_1", "Tenant A"),
        settings.get("env_2", "Tenant B"),
        settings.get("env_3", "Tenant C")
    ]

def get_device_types():
    return config.get("device_types", DEFAULT_CONFIG["device_types"])

def is_ip(addr):
    return bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", addr))

def resolve_dns(input_val, mode):
    if mode == "forward":
        try:
            return socket.gethostbyname(input_val)
        except Exception:
            return "N/A"
    else:
        try:
            return socket.gethostbyaddr(input_val)[0]
        except Exception:
            return "N/A"

def add_node(env, name, addr, dev_type="Server"):
    # Resolve fallback DNS names/IPs if blank
    if not name and addr:
        name = resolve_dns(addr, "reverse")
        if not name or name == "N/A":
            name = addr
    elif name and not addr:
        if is_ip(name):
            addr = name
        else:
            addr = resolve_dns(name, "forward")
            if not addr or addr == "N/A":
                addr = name

    if not name or not addr:
        return None

    # Resolve FQDN if possible
    fqdn = ""
    if is_ip(addr):
        fqdn = resolve_dns(addr, "reverse")
        if not fqdn or fqdn == addr or fqdn == "N/A":
            fqdn = ""
    else:
        fqdn = addr
        resolved_ip = resolve_dns(addr, "forward")
        if resolved_ip and resolved_ip != "N/A":
            addr = resolved_ip

    reload_config()
    envs = config.setdefault("environments", {})
    nodes = envs.setdefault(env, [])
    
    max_id = 0
    for n in nodes:
        try:
            nid = int(n.get("id", 0))
            if nid > max_id:
                max_id = nid
        except ValueError:
            pass
    next_id = max_id + 1
    
    nodes.append({
        "id": next_id,
        "name": name,
        "addr": addr,
        "dev_type": dev_type,
        "fqdn": fqdn
    })
    save_yaml(config)
    
    # Spawn background thread for quick initial sweep
    threading.Thread(target=quick_node_sweep, args=(env, next_id, name, addr), daemon=True).start()
    return next_id

def quick_node_sweep(env, nid, name, addr):
    lower_env = env.lower().replace(" ", "_")
    status_file = os.path.join(STATUS_DIR, f"{lower_env}.status")
    
    # Generate initial status row
    cmd = ["ping", "-c", "1", "-w", "1", addr]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        history = "." * 23 + "1"
        avg_rtt = "0.0 ms"
        match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", res.stdout)
        if match:
            avg_rtt = f"{match.group(1)} ms"
        status_line = f"{nid}|UP|{avg_rtt}||{history}\n"
    else:
        history = "." * 23 + "0"
        status_line = f"{nid}|DOWN|N/A|{time.strftime('%H:%M:%S')}|{history}\n"
        
    try:
        # Atomic append/write
        lines = []
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                lines = [l for l in f.readlines() if not l.startswith(f"{nid}|")]
        lines.append(status_line)
        with open(status_file, "w") as f:
            f.writelines(lines)
    except Exception:
        pass

def delete_node(env, nid):
    reload_config()
    envs = config.setdefault("environments", {})
    nodes = envs.get(env, [])
    
    new_nodes = [n for n in nodes if str(n.get("id")) != str(nid)]
    envs[env] = new_nodes
    save_yaml(config)
    
    # Remove from status file
    lower_env = env.lower().replace(" ", "_")
    status_file = os.path.join(STATUS_DIR, f"{lower_env}.status")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                lines = f.readlines()
            new_lines = [l for l in lines if not l.startswith(f"{nid}|")]
            with open(status_file, "w") as f:
                f.writelines(new_lines)
        except Exception:
            pass

# Status Reader Helper
def load_statuses(env):
    lower_env = env.lower().replace(" ", "_")
    status_file = os.path.join(STATUS_DIR, f"{lower_env}.status")
    statuses = {}
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) >= 2:
                        nid = parts[0]
                        stat = parts[1]
                        lat = parts[2] if len(parts) > 2 else "N/A"
                        dsince = parts[3] if len(parts) > 3 else ""
                        hist = parts[4] if len(parts) > 4 else "." * 24
                        statuses[str(nid)] = {
                            "status": stat,
                            "latency": lat,
                            "down_since": dsince,
                            "history": hist
                        }
        except Exception:
            pass
    return statuses

# Background Sweeper loop
def run_sweeper_daemon():
    print(f"Sweep daemon started (PID: {os.getpid()}).")
    with open(os.path.join(PID_DIR, "daemon.pid"), "w") as f:
        f.write(str(os.getpid()))
        
    try:
        while True:
            reload_config()
            settings = get_settings()
            environments = get_environments()
            freq = int(settings.get("sweep_frequency", 60))
            ping_count = int(settings.get("ping_count", 5))
            ping_interval = float(settings.get("ping_interval", 0.2))
            
            for env in environments:
                envs = config.get("environments", {})
                nodes = envs.get(env, [])
                if not nodes:
                    continue
                
                statuses = load_statuses(env)
                
                def ping_node(node):
                    nid = str(node.get("id"))
                    addr = node.get("addr")
                    prev = statuses.get(nid, {"status": "UP", "down_since": "", "history": "." * 24})
                    prev_h = prev["history"]
                    if len(prev_h) < 24:
                        prev_h = "." * (24 - len(prev_h)) + prev_h
                        
                    cmd = ["ping", "-c", str(ping_count), "-i", str(ping_interval), "-w", str(ping_count + 2), addr]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if res.returncode == 0:
                        new_h = prev_h[1:] + "1"
                        avg_rtt = "0.0 ms"
                        match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", res.stdout)
                        if match:
                            avg_rtt = f"{match.group(1)} ms"
                        return f"{nid}|UP|{avg_rtt}||{new_h}\n"
                    else:
                        new_h = prev_h[1:] + "0"
                        since = prev["down_since"]
                        if prev["status"] != "DOWN" or not since:
                            since = time.strftime('%H:%M:%S')
                        return f"{nid}|DOWN|N/A|{since}|{new_h}\n"
                
                # Execute in parallel thread pool
                with ThreadPoolExecutor(max_workers=20) as executor:
                    results = list(executor.map(ping_node, nodes))
                
                lower_env = env.lower().replace(" ", "_")
                status_file = os.path.join(STATUS_DIR, f"{lower_env}.status")
                tmp_file = status_file + ".tmp"
                try:
                    with open(tmp_file, "w") as f:
                        f.writelines(results)
                    os.replace(tmp_file, status_file)
                except Exception:
                    pass
            
            time.sleep(freq)
    finally:
        try:
            os.remove(os.path.join(PID_DIR, "daemon.pid"))
        except OSError:
            pass

# HTTP Server request handler
class TerminusHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence default terminal logs
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        reload_config()
        settings = get_settings()
        environments = get_environments()
        
        if path == "/":
            active_env = query.get("env", [environments[0]])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(self.render_dashboard(active_env).encode("utf-8"))
            
        elif path == "/add":
            env = query.get("env", [""])[0]
            name = query.get("name", [""])[0]
            addr = query.get("addr", [""])[0]
            dtype = query.get("dev_type", ["Server"])[0]
            
            add_node(env, name, addr, dtype)
            self.send_response(302)
            self.send_header("Location", f"/?env={env.replace(' ', '+')}")
            self.send_header("Connection", "close")
            self.end_headers()
            
        elif path == "/delete":
            env = query.get("env", [""])[0]
            nid = query.get("id", [""])[0]
            
            delete_node(env, nid)
            self.send_response(302)
            self.send_header("Location", f"/?env={env.replace(' ', '+')}")
            self.send_header("Connection", "close")
            self.end_headers()
            
        elif path == "/admin":
            success = query.get("success", [""])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(self.render_admin(success).encode("utf-8"))
            
        elif path == "/admin/save_tabs":
            env1 = query.get("env1", ["Tenant A"])[0]
            env2 = query.get("env2", ["Tenant B"])[0]
            env3 = query.get("env3", ["Tenant C"])[0]
            
            # Rename status files if modified
            self.rename_status_file(environments[0], env1)
            self.rename_status_file(environments[1], env2)
            self.rename_status_file(environments[2], env3)
            
            # Save settings JSON via YAML helper
            new_set = {
                "env_1": env1,
                "env_2": env2,
                "env_3": env3,
                "room_name": settings.get("room_name", "Server Room B"),
                "physical_address": settings.get("physical_address", "456 Enterprise Way"),
                "company_name": settings.get("company_name", "General Corp"),
                "sweep_frequency": settings.get("sweep_frequency", 60),
                "ping_count": settings.get("ping_count", 5),
                "ping_interval": settings.get("ping_interval", 0.2)
            }
            self.save_settings_dict(new_set)
            
            self.send_response(302)
            self.send_header("Location", "/admin?success=1")
            self.send_header("Connection", "close")
            self.end_headers()
            
        elif path == "/admin/save_ping":
            pcount = query.get("pcount", [5])[0]
            pinterval = query.get("pinterval", [0.2])[0]
            freq = query.get("frequency", [60])[0]
            
            new_set = {
                "env_1": environments[0],
                "env_2": environments[1],
                "env_3": environments[2],
                "room_name": settings.get("room_name", "Server Room B"),
                "physical_address": settings.get("physical_address", "456 Enterprise Way"),
                "company_name": settings.get("company_name", "General Corp"),
                "sweep_frequency": int(freq),
                "ping_count": int(pcount),
                "ping_interval": float(pinterval)
            }
            self.save_settings_dict(new_set)
            
            self.send_response(302)
            self.send_header("Location", "/admin?success=2")
            self.send_header("Connection", "close")
            self.end_headers()
            
        elif path == "/admin/save_host":
            room = query.get("room", ["Server Room B"])[0]
            addr = query.get("address", ["456 Enterprise Way"])[0]
            comp = query.get("company", ["General Corp"])[0]
            
            new_set = {
                "env_1": environments[0],
                "env_2": environments[1],
                "env_3": environments[2],
                "room_name": room,
                "physical_address": addr,
                "company_name": comp,
                "sweep_frequency": settings.get("sweep_frequency", 60),
                "ping_count": settings.get("ping_count", 5),
                "ping_interval": settings.get("ping_interval", 0.2)
            }
            self.save_settings_dict(new_set)
            
            self.send_response(302)
            self.send_header("Location", "/admin?success=5")
            self.send_header("Connection", "close")
            self.end_headers()
            
        elif path == "/admin/add_type":
            new_type = query.get("type", [""])[0]
            if new_type:
                reload_config()
                types = config.setdefault("device_types", [])
                if new_type not in types:
                    types.append(new_type)
                save_yaml(config)
                
            self.send_response(302)
            self.send_header("Location", "/admin?success=3")
            self.send_header("Connection", "close")
            self.end_headers()
            
        elif path == "/admin/del_type":
            del_type = query.get("type", [""])[0]
            if del_type:
                reload_config()
                types = config.setdefault("device_types", [])
                if del_type in types:
                    types.remove(del_type)
                save_yaml(config)
                
            self.send_response(302)
            self.send_header("Location", "/admin?success=4")
            self.send_header("Connection", "close")
            self.end_headers()
            
        elif path == "/nginx_status":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(self.render_nginx_status().encode("utf-8"))
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def rename_status_file(self, old_name, new_name):
        if old_name == new_name:
            return
        old_file = os.path.join(STATUS_DIR, f"{old_name.lower().replace(' ', '_')}.status")
        new_file = os.path.join(STATUS_DIR, f"{new_name.lower().replace(' ', '_')}.status")
        if os.path.exists(old_file):
            try:
                os.rename(old_file, new_file)
            except Exception:
                pass

    def save_settings_dict(self, new_settings):
        reload_config()
        config["settings"] = new_settings
        
        # Remap environments dict keys to prevent data loss
        envs = config.setdefault("environments", {})
        old_keys = list(envs.keys())
        new_keys = [new_settings.get("env_1"), new_settings.get("env_2"), new_settings.get("env_3")]
        
        updated_envs = {}
        for i, new_k in enumerate(new_keys):
            old_k = old_keys[i] if i < len(old_keys) else new_k
            updated_envs[new_k] = envs.get(old_k, [])
            
        config["environments"] = updated_envs
        save_yaml(config)

    def render_dashboard(self, active_env):
        settings = get_settings()
        environments = get_environments()
        device_types = get_device_types()
        
        envs_data = config.get("environments", {})
        nodes = envs_data.get(active_env, [])
        statuses = load_statuses(active_env)
        
        # Populate tabs HTML
        tabs_html = ""
        for e in environments:
            active_class = "active" if e == active_env else ""
            tabs_html += f'<a href="/?env={e.replace(" ", "+")}" class="tab-btn {active_class}">[ {e} ]</a>'
            
        # Populate rows HTML
        table_rows = ""
        for n in nodes:
            nid = str(n.get("id"))
            dtype = n.get("dev_type", "Server")
            name = n.get("name")
            addr = n.get("addr")
            fqdn = n.get("fqdn", "")
            
            stat_info = statuses.get(nid, {"status": "PENDING", "latency": "N/A", "down_since": "", "history": "." * 24})
            stat = stat_info["status"]
            lat = stat_info["latency"]
            dsince = stat_info["down_since"]
            hist = stat_info["history"]
            
            if len(hist) < 24:
                hist = "." * (24 - len(hist)) + hist
                
            badge_class = "status-online" if stat == "UP" else ("status-alert" if stat == "DOWN" else "status-pending")
            badge_str = "ONLINE" if stat == "UP" else ("ALERT" if stat == "DOWN" else "PENDING")
            status_badge = f'<span class="status-badge {badge_class}">{badge_str}</span>'
            
            detail_str = f"Since: {dsince}" if stat == "DOWN" else lat
            
            addr_html = f'<code>{addr}</code>'
            if fqdn:
                addr_html += f'<br><span style="font-size: 0.75rem; color: var(--fg-dim); font-family: inherit;">{fqdn}</span>'
                
            spark_html = ""
            for i in range(24):
                char = hist[i]
                if char == "1":
                    spark_html += f'<span style="color: var(--green); font-size: 1.15rem; line-height: 1; letter-spacing: -2px; margin-right: 1px;" title="Sweep {i+1}: UP">■</span>'
                elif char == "0":
                    spark_html += f'<span style="color: var(--red); font-size: 1.15rem; line-height: 1; letter-spacing: -2px; margin-right: 1px;" title="Sweep {i+1}: DOWN">■</span>'
                else:
                    spark_html += f'<span style="color: var(--fg-dim); font-size: 1.15rem; line-height: 1; letter-spacing: -2px; margin-right: 1px;" title="Sweep {i+1}: PENDING">·</span>'
            
            table_rows += f"""
            <tr>
                <td>{nid}</td>
                <td>{dtype}</td>
                <td><strong>{name}</strong></td>
                <td>{addr_html}</td>
                <td>{status_badge}</td>
                <td>{detail_str}</td>
                <td style="white-space: nowrap;">{spark_html}</td>
                <td>
                    <a href="/delete?env={active_env.replace(' ', '+')}&id={nid}" class="btn btn-danger">[Delete]</a>
                </td>
            </tr>"""
            
        if not table_rows:
            table_rows = '<tr><td colspan="8" style="text-align: center; color: var(--fg-dim); padding: 40px;">No nodes configured in this environment.</td></tr>'
            
        device_options = "".join(f'<option value="{t}">{t}</option>' for t in device_types)
        
        # System parameters
        hostname_running = socket.gethostname()
        time_utc = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        time_local = time.strftime('%Y-%m-%d %H:%M:%S %Z')
        
        # OS running
        os_running = "Linux"
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_running = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass
            
        # Mem Total
        ram_total = "N/A"
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        ram_total = f"{kb / (1024*1024):.1f}Gi"
                        break
        except Exception:
            pass
            
        # CPU model
        cpu_model = "N/A"
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu_model = line.split(":")[1].strip()
                        break
        except Exception:
            pass
            
        # IP Addresses
        ip_addresses = "127.0.0.1"
        try:
            ips = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.strip()
            if ips:
                ip_addresses = ips
        except Exception:
            pass

        # Return dynamic HTML string (Dracula theme template)
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Terminus Operations Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Spline+Sans+Mono:wght@300;400;500;600;700&display=swap');
        :root {{
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
        }}
        * {{ box-sizing: border-box; }}
        body {{
            background-color: #0c0d12;
            color: var(--fg-base);
            font-family: 'Spline Sans Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .terminal-window {{
            width: 100%;
            max-width: 950px;
            background-color: var(--bg-base);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.6);
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .terminal-header {{
            background-color: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
            padding: 10px 15px;
            display: flex;
            align-items: center;
            position: relative;
        }}
        .terminal-buttons {{
            display: flex;
            gap: 8px;
        }}
        .btn-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        .dot-red {{ background-color: var(--red); }}
        .dot-yellow {{ background-color: var(--orange); }}
        .dot-green {{ background-color: var(--green); }}
        .terminal-title {{
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            color: var(--fg-dim);
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .terminal-body {{
            padding: 25px;
        }}
        .prompt-line {{
            margin-bottom: 15px;
            font-size: 0.95rem;
        }}
        .prompt-symbol {{
            color: var(--green);
            font-weight: bold;
        }}
        .prompt-path {{
            color: var(--cyan);
        }}
        .command-text {{
            color: var(--fg-base);
        }}
        .nav-links {{
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            font-size: 1rem;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 15px;
        }}
        .nav-links a {{
            color: var(--cyan);
            text-decoration: none;
        }}
        .nav-links a:hover {{
            text-decoration: underline;
        }}
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }}
        .tab-btn {{
            color: var(--fg-dim);
            padding: 6px 12px;
            text-decoration: none;
            font-weight: 500;
        }}
        .tab-btn:hover {{
            color: var(--fg-base);
        }}
        .tab-btn.active {{
            color: var(--green);
            font-weight: bold;
        }}
        .card {{
            background-color: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 25px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(0, 0, 0, 0.45);
        }}
        .section-title {{
            font-size: 1.1rem;
            color: var(--purple);
            margin: 0 0 15px 0;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
        }}
        th {{
            color: var(--cyan);
            border-bottom: 2px solid var(--border);
            font-weight: bold;
        }}
        td {{
            border-bottom: none;
        }}
        .status-badge {{
            font-weight: bold;
        }}
        .status-online {{ color: var(--green); }}
        .status-alert {{ color: var(--red); }}
        .status-pending {{ color: var(--orange); }}
        code {{
            background-color: rgba(0, 0, 0, 0.25);
            padding: 2px 6px;
            border-radius: 4px;
            color: var(--cyan);
        }}
        .btn {{
            background-color: var(--green);
            color: #0c0d12;
            border: none;
            padding: 6px 12px;
            font-family: inherit;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
            text-decoration: none;
            display: inline-block;
        }}
        .btn-danger {{
            background-color: transparent;
            color: var(--red);
            border: 1px solid var(--red);
            padding: 2px 8px;
        }}
        .btn-danger:hover {{
            background-color: var(--red);
            color: var(--fg-base);
        }}
        .form-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr auto;
            gap: 16px;
            align-items: end;
        }}
        .form-group {{
            display: flex;
            flex-direction: column;
        }}
        label {{
            color: var(--fg-dim);
            margin-bottom: 6px;
        }}
        input, select {{
            background-color: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--fg-base);
            padding: 8px 12px;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
        }}
        input:focus, select:focus {{
            border-color: var(--purple);
        }}
    </style>
    <meta http-equiv="refresh" content="10">
</head>
<body>
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-buttons">
                <span class="btn-dot dot-red"></span>
                <span class="btn-dot dot-yellow"></span>
                <span class="btn-dot dot-green"></span>
            </div>
            <div class="terminal-title">rtroiano@{hostname_running}: ~/terminus</div>
        </div>
        
        <div class="terminal-body">
            <div class="nav-links">
                <a href="/" style="color: var(--green); font-weight: bold;">[ Dashboard ]</a>
                <a href="/admin">[ Admin Settings ]</a>
                <a href="/nginx_status">[ Nginx Status ]</a>
            </div>

            <div class="prompt-line">
                <span class="prompt-symbol">rtroiano@{hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">terminus --show-nodes --env "{active_env}"</span>
            </div>

            <div class="tabs">
                {tabs_html}
            </div>

            <div class="card">
                <div class="section-title">&gt;_ Environment Nodes Grid</div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px;">ID</th>
                            <th>Device Type</th>
                            <th>Node Name</th>
                            <th>Target Host/IP</th>
                            <th>Status</th>
                            <th>Performance Details</th>
                            <th>Uptime History (Last 24 Sweeps)</th>
                            <th style="width: 80px;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <div class="section-title">&gt;_ Add Node Configuration</div>
                <form action="/add" method="GET">
                    <input type="hidden" name="env" value="{active_env}">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="name">Node Name</label>
                            <input type="text" id="name" name="name" placeholder="e.g. Gateway" required>
                        </div>
                        <div class="form-group">
                            <label for="addr">IP / Hostname</label>
                            <input type="text" id="addr" name="addr" placeholder="e.g. 192.168.1.1" required>
                        </div>
                        <div class="form-group">
                            <label for="dev_type">Device Type</label>
                            <select id="dev_type" name="dev_type">
                                {device_options}
                            </select>
                        </div>
                        <button type="submit" class="btn">Add Node</button>
                    </div>
                </form>
            </div>

            <div class="prompt-line" style="margin-top: 30px;">
                <span class="prompt-symbol">rtroiano@{hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">terminus --show-host-info</span>
            </div>

            <div class="card">
                <div class="section-title">&gt;_ Host System Specs</div>
                <table>
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Configured / Dynamic System Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>System Hostname</td>
                            <td><code>{hostname_running}</code></td>
                        </tr>
                        <tr>
                            <td>Physical Room Location</td>
                            <td><code>{settings.get('room_name', 'Server Room B')}</code></td>
                        </tr>
                        <tr>
                            <td>Physical Address</td>
                            <td><code>{settings.get('physical_address', '456 Enterprise Way')}</code></td>
                        </tr>
                        <tr>
                            <td>Company Name</td>
                            <td><code>{settings.get('company_name', 'General Corp')}</code></td>
                        </tr>
                        <tr>
                            <td>Time (UTC)</td>
                            <td><code>{time_utc}</code></td>
                        </tr>
                        <tr>
                            <td>Time (Local Zone)</td>
                            <td><code>{time_local}</code></td>
                        </tr>
                        <tr>
                            <td>Operating System (OS)</td>
                            <td><code>{os_running}</code></td>
                        </tr>
                        <tr>
                            <td>Total Memory (RAM)</td>
                            <td><code>{ram_total}</code></td>
                        </tr>
                        <tr>
                            <td>Processor (CPU)</td>
                            <td><code>{cpu_model}</code></td>
                        </tr>
                        <tr>
                            <td>Active Network IP(s)</td>
                            <td><code>{ip_addresses}</code></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""

    def render_admin(self, success_code):
        settings = get_settings()
        environments = get_environments()
        device_types = get_device_types()
        
        success_msg = ""
        if success_code == "1":
            success_msg = '<div class="alert alert-success">Tab Names Saved Successfully!</div>'
        elif success_code == "2":
            success_msg = '<div class="alert alert-success">Sweep & Ping Configuration Updated!</div>'
        elif success_code == "3":
            success_msg = '<div class="alert alert-success">Device Type Added!</div>'
        elif success_code == "4":
            success_msg = '<div class="alert alert-success">Device Type Deleted!</div>'
        elif success_code == "5":
            success_msg = '<div class="alert alert-success">Host System Configurations Saved!</div>'
            
        error_msg = ""
        
        types_html = ""
        for t in device_types:
            types_html += f"""
            <div style="display: flex; justify-content: space-between; padding: 6px 10px; border-bottom: 1px dashed #44475a;">
                <span>{t}</span>
                <a href="/admin/del_type?type={t}" style="color: #ff5555; text-decoration: none;">[Delete]</a>
            </div>"""
            
        hostname_running = socket.gethostname()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Terminus Admin Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Spline+Sans+Mono:wght@300;400;500;600;700&display=swap');
        :root {{
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
        }}
        * {{ box-sizing: border-box; }}
        body {{
            background-color: #0c0d12;
            color: var(--fg-base);
            font-family: 'Spline Sans Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .terminal-window {{
            width: 100%;
            max-width: 950px;
            background-color: var(--bg-base);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.6);
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .terminal-header {{
            background-color: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
            padding: 10px 15px;
            display: flex;
            align-items: center;
            position: relative;
        }}
        .terminal-buttons {{
            display: flex;
            gap: 8px;
        }}
        .btn-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        .dot-red {{ background-color: var(--red); }}
        .dot-yellow {{ background-color: var(--orange); }}
        .dot-green {{ background-color: var(--green); }}
        .terminal-title {{
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            color: var(--fg-dim);
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .terminal-body {{
            padding: 25px;
        }}
        .prompt-line {{
            margin-bottom: 15px;
            font-size: 0.95rem;
        }}
        .prompt-symbol {{
            color: var(--green);
            font-weight: bold;
        }}
        .prompt-path {{
            color: var(--cyan);
        }}
        .command-text {{
            color: var(--fg-base);
        }}
        .nav-links {{
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            font-size: 1rem;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 15px;
        }}
        .nav-links a {{
            color: var(--cyan);
            text-decoration: none;
        }}
        .nav-links a:hover {{
            text-decoration: underline;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .card {{
            background-color: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(0, 0, 0, 0.45);
        }}
        .card-title {{
            color: var(--purple);
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }}
        .form-group {{
            display: flex;
            flex-direction: column;
            margin-bottom: 15px;
        }}
        label {{
            color: var(--fg-dim);
            margin-bottom: 5px;
            font-size: 0.9rem;
        }}
        input {{
            background-color: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--fg-base);
            padding: 8px 12px;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
        }}
        input:focus {{
            border-color: var(--purple);
        }}
        .btn {{
            background-color: var(--green);
            color: #0c0d12;
            border: none;
            padding: 10px 15px;
            font-family: inherit;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
            display: inline-block;
        }}
        .btn:hover {{
            box-shadow: 0 2px 8px rgba(80,250,123,0.4);
        }}
        .alert {{
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-weight: bold;
        }}
        .alert-success {{
            background-color: rgba(80,250,123,0.15);
            color: var(--green);
            border: 1px solid var(--green);
        }}
        .alert-error {{
            background-color: rgba(255,85,85,0.15);
            color: var(--red);
            border: 1px solid var(--red);
        }}
    </style>
</head>
<body>
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-buttons">
                <span class="btn-dot dot-red"></span>
                <span class="btn-dot dot-yellow"></span>
                <span class="btn-dot dot-green"></span>
            </div>
            <div class="terminal-title">rtroiano@{hostname_running}: ~/terminus (admin)</div>
        </div>
        
        <div class="terminal-body">
            <div class="nav-links">
                <a href="/">[ Dashboard ]</a>
                <a href="/admin" style="color: var(--green); font-weight: bold;">[ Admin Settings ]</a>
                <a href="/nginx_status">[ Nginx Status ]</a>
            </div>

            <div class="prompt-line">
                <span class="prompt-symbol">rtroiano@{hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">terminus --admin-settings</span>
            </div>
            
            {success_msg}
            {error_msg}
            
            <div class="grid">
                <div class="card">
                    <div class="card-title">&gt;_ Tab Name Editor</div>
                    <form action="/admin/save_tabs" method="GET">
                        <div class="form-group">
                            <label>Tab 1 Name</label>
                            <input type="text" name="env1" value="{environments[0]}">
                        </div>
                        <div class="form-group">
                            <label>Tab 2 Name</label>
                            <input type="text" name="env2" value="{environments[1]}">
                        </div>
                        <div class="form-group">
                            <label>Tab 3 Name</label>
                            <input type="text" name="env3" value="{environments[2]}">
                        </div>
                        <button type="submit" class="btn">Save Tabs</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Sweep &amp; Ping Config</div>
                    <form action="/admin/save_ping" method="GET">
                        <div class="form-group">
                            <label>Sweep Frequency (seconds)</label>
                            <input type="number" name="frequency" value="{settings.get('sweep_frequency', 60)}">
                        </div>
                        <div class="form-group">
                            <label>Ping Count per Sweep</label>
                            <input type="number" name="pcount" value="{settings.get('ping_count', 5)}">
                        </div>
                        <div class="form-group">
                            <label>Ping Interval (seconds)</label>
                            <input type="text" name="pinterval" value="{settings.get('ping_interval', 0.2)}">
                        </div>
                        <button type="submit" class="btn">Save Configuration</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Host System Configurations</div>
                    <form action="/admin/save_host" method="GET">
                        <div class="form-group">
                            <label>Physical Room Location</label>
                            <input type="text" name="room" value="{settings.get('room_name', 'Server Room B')}">
                        </div>
                        <div class="form-group">
                            <label>Physical Address</label>
                            <input type="text" name="address" value="{settings.get('physical_address', '456 Enterprise Way')}">
                        </div>
                        <div class="form-group">
                            <label>Company Name</label>
                            <input type="text" name="company" value="{settings.get('company_name', 'General Corp')}">
                        </div>
                        <button type="submit" class="btn">Save Host Info</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Manage Device Types</div>
                    <form action="/admin/add_type" method="GET" style="margin-bottom: 20px;">
                        <div class="form-group">
                            <label>New Device Type</label>
                            <input type="text" name="type" placeholder="e.g. Access Point" required>
                        </div>
                        <button type="submit" class="btn">Add Device Type</button>
                    </form>
                    <div>
                        {types_html}
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

    def render_nginx_status(self):
        hostname_running = socket.gethostname()
        
        # Pull live nginx status
        active, accepts, handled, requests, reading, writing, waiting = 0, 0, 0, 0, 0, 0, 0
        try:
            raw = subprocess.run(["curl", "-s", "http://127.0.0.1/nginx_status_raw"], capture_output=True, text=True).stdout
            m = re.search(r"Active connections:\ (\d+)", raw)
            if m:
                active = int(m.group(1))
            lines = raw.strip().split("\n")
            if len(lines) >= 3:
                parts = lines[2].split()
                if len(parts) >= 3:
                    accepts, handled, requests = parts[0], parts[1], parts[2]
            if len(lines) >= 4:
                parts = lines[3].split()
                if len(parts) >= 6:
                    reading, writing, waiting = parts[1], parts[3], parts[6]
        except Exception:
            pass
            
        sys_uptime = "N/A"
        try:
            sys_uptime = subprocess.run(["uptime", "-p"], capture_output=True, text=True).stdout.strip()
        except Exception:
            pass
            
        load_avg = "N/A"
        try:
            with open("/proc/loadavg", "r") as f:
                load_avg = f.read().strip()
        except Exception:
            pass
            
        mem_info = "N/A"
        try:
            mem_info = subprocess.run(["free", "-h"], capture_output=True, text=True).stdout.split("\n")[1].split()
            mem_info = f"Used: {mem_info[2]} / Total: {mem_info[1]}"
        except Exception:
            pass
            
        nginx_ver = "N/A"
        try:
            res = subprocess.run(["nginx", "-v"], capture_output=True, text=True)
            nginx_ver = (res.stdout or res.stderr).strip()
        except Exception:
            pass

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Nginx Styled Status</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Spline+Sans+Mono:wght@300;400;500;600;700&display=swap');
        :root {{
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
        }}
        * {{ box-sizing: border-box; }}
        body {{
            background-color: #0c0d12;
            color: var(--fg-base);
            font-family: 'Spline Sans Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .terminal-window {{
            width: 100%;
            max-width: 950px;
            background-color: var(--bg-base);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.6);
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .terminal-header {{
            background-color: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
            padding: 10px 15px;
            display: flex;
            align-items: center;
            position: relative;
        }}
        .terminal-buttons {{
            display: flex;
            gap: 8px;
        }}
        .btn-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        .dot-red {{ background-color: var(--red); }}
        .dot-yellow {{ background-color: var(--orange); }}
        .dot-green {{ background-color: var(--green); }}
        .terminal-title {{
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            color: var(--fg-dim);
            font-size: 0.85rem;
            font-weight: 500;
        }}
        .terminal-body {{
            padding: 25px;
        }}
        .prompt-line {{
            margin-bottom: 15px;
            font-size: 0.95rem;
        }}
        .prompt-symbol {{
            color: var(--green);
            font-weight: bold;
        }}
        .prompt-path {{
            color: var(--cyan);
        }}
        .command-text {{
            color: var(--fg-base);
        }}
        .nav-links {{
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            font-size: 1rem;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 15px;
        }}
        .nav-links a {{
            color: var(--cyan);
            text-decoration: none;
        }}
        .nav-links a:hover {{
            text-decoration: underline;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .card {{
            background-color: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(0, 0, 0, 0.45);
        }}
        .card-title {{
            color: var(--purple);
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }}
    </style>
</head>
<body>
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-buttons">
                <span class="btn-dot dot-red"></span>
                <span class="btn-dot dot-yellow"></span>
                <span class="btn-dot dot-green"></span>
            </div>
            <div class="terminal-title">rtroiano@{hostname_running}: ~/terminus (nginx status)</div>
        </div>
        
        <div class="terminal-body">
            <div class="nav-links">
                <a href="/">[ Dashboard ]</a>
                <a href="/admin">[ Admin Settings ]</a>
                <a href="/nginx_status" style="color: var(--green); font-weight: bold;">[ Nginx Status ]</a>
            </div>

            <div class="prompt-line">
                <span class="prompt-symbol">rtroiano@{hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">nginx -s status --visual</span>
            </div>
            
            <div class="grid">
                <div class="card">
                    <div class="card-title">&gt;_ Nginx Metrics</div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Active Connections</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; font-weight: bold; color: var(--green);">{active}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Accepted Connections</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{accepts}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Handled Connections</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{handled}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Total Requests</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; font-weight: bold; color: var(--cyan);">{requests}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Reading</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{reading}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Writing</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{writing}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Waiting (Keep-Alive)</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{waiting}</td>
                        </tr>
                    </table>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ System Specs</div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">System Uptime</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{sys_uptime}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Load Average</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{load_avg}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Memory Usage</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a;">{mem_info}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--fg-dim);">Nginx Version</td>
                            <td style="padding: 8px; border-bottom: 1px dashed #44475a; color: var(--purple);">{nginx_ver}</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

def run_webserver():
    server_address = ('', 8085)
    httpd = HTTPServer(server_address, TerminusHTTPHandler)
    print(f"Web configuration server started on port 8085 (PID: {os.getpid()}).")
    with open(os.path.join(PID_DIR, "web.pid"), "w") as f:
        f.write(str(os.getpid()))
        
    try:
        httpd.serve_forever()
    finally:
        try:
            os.remove(os.path.join(PID_DIR, "web.pid"))
        except OSError:
            pass

# TUI Helper: Truncate helper
def trunc(text, max_len):
    if len(text) > max_len:
        return text[:max_len-3] + "..."
    return f"{text:<{max_len}}"

# Interactive TUI Logic
def redraw_tui(active_tab_idx, selected_row):
    environments = get_environments()
    active_env = environments[active_tab_idx]
    
    # Fetch terminal dimensions
    try:
        rows, cols = os.get_terminal_size()
    except Exception:
        rows, cols = 24, 80
        
    # Headers
    title = f" TERMINUS - STANDALONE NETWORK MONITOR "
    title_line = f"┌{'─' * (cols - 2)}┐"
    print(f"\033[H\033[J", end="") # Clear screen and move cursor to home
    print(f"\033[1;35m{title_line}\033[0m")
    
    # Tabs
    tab_bar = "  "
    for idx, env in enumerate(environments):
        if idx == active_tab_idx:
            tab_bar += f"\033[1;32m[ {env} ]\033[0m   "
        else:
            tab_bar += f"\033[1;30m[ {env} ]\033[0m   "
    print(tab_bar)
    print(f"\033[1;35m├{'─' * (cols - 2)}┤\033[0m")
    
    # Table headers widths
    w_id, w_type, w_name, w_addr, w_stat, w_lat, w_dsince = 6, 12, 18, 18, 10, 10, 10
    total_w = w_id + w_type + w_name + w_addr + w_stat + w_lat + w_dsince + 20
    
    print(f"  \033[1;36m%-*s   %-*s   %-*s   %-*s   %-*s   %-*s   %-*s\033[0m" % (
        w_id, "ID", w_type, "DEVICE", w_name, "NAME", w_addr, "TARGET IP", w_stat, "STATUS", w_lat, "LATENCY", w_dsince, "DOWNTIME"
    ))
    print(f"  {'-' * (total_w)}")
    
    envs_data = config.get("environments", {})
    nodes = envs_data.get(active_env, [])
    statuses = load_statuses(active_env)
    
    for idx, node in enumerate(nodes):
        nid = str(node.get("id"))
        dtype = node.get("dev_type", "Server")
        name = node.get("name")
        addr = node.get("addr")
        
        stat_info = statuses.get(nid, {"status": "PENDING", "latency": "N/A", "down_since": ""})
        stat = stat_info["status"]
        lat = stat_info["latency"]
        dsince = stat_info["down_since"]
        
        if stat == "UP":
            stat_color = "\033[1;32m"
            stat_str = "ONLINE"
        elif stat == "DOWN":
            stat_color = "\033[1;31m"
            stat_str = "ALERT"
        else:
            stat_color = "\033[1;33m"
            stat_str = "PENDING"
            
        r_id = trunc(nid, w_id).strip()
        r_type = trunc(dtype, w_type).strip()
        r_name = trunc(name, w_name).strip()
        r_addr = trunc(addr, w_addr).strip()
        r_stat = trunc(stat_str, w_stat).strip()
        r_lat = trunc(lat, w_lat).strip()
        r_dsince = trunc(dsince, w_dsince).strip()
        
        row_str = "  %-*s   %-*s   %-*s   %-*s   %b%-*s\033[0m   %-*s   %-*s" % (
            w_id, r_id, w_type, r_type, w_name, r_name, w_addr, r_addr, stat_color.encode(), w_stat, r_stat, w_lat, r_lat, w_dsince, r_dsince
        )
        
        if idx == selected_row:
            # Highlight selected row (reverse video)
            print(f"\033[7m{row_str:<{total_w + 10}}\033[0m")
        else:
            print(row_str)
            
    if not nodes:
        print(f"\n  \033[1;30mNo nodes configured. Press 'A' to add one.\033[0m\n")
        
    print(f"\033[1;35m└{'─' * (cols - 2)}┘\033[0m")
    
    # Process Status Bars
    dpid = ""
    daemon_pid = os.path.join(PID_DIR, "daemon.pid")
    if os.path.exists(daemon_pid):
        with open(daemon_pid, "r") as f:
            dpid = f.read().strip()
    d_run = f"\033[1;32mRUNNING (PID: {dpid})\033[0m" if dpid and os.path.exists(f"/proc/{dpid}") else "\033[1;31mOFFLINE\033[0m"
    
    wpid = ""
    web_pid = os.path.join(PID_DIR, "web.pid")
    if os.path.exists(web_pid):
        with open(web_pid, "r") as f:
            wpid = f.read().strip()
    w_run = f"\033[1;32mRUNNING (PID: {wpid})\033[0m" if wpid and os.path.exists(f"/proc/{wpid}") else "\033[1;31mOFFLINE\033[0m"
    
    print(f"  Daemon: {d_run}   |   Web Server: {w_run}")
    
    # Command Bar
    cmd_bar = " [TAB] Switch Env  |  [▲/▼] Select  |  [A] Add Node  |  [D] Delete  |  [R] Sweep  |  [Q] Quit "
    print(f"\033[1;37;48;5;236m{cmd_bar:^{cols-2}}\033[0m")

def get_key_tui():
    import termios
    import tty
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        rlist, _, _ = select.select([sys.stdin], [], [], 0.5)
        if rlist:
            char = sys.stdin.read(1)
            if char == "\x1b": # ESC arrow keys
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    char2 = sys.stdin.read(1)
                    if char2 == "[":
                        char3 = sys.stdin.read(1)
                        if char3 == "A": return "UP"
                        elif char3 == "B": return "DOWN"
            return char
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def tui_add_node(env):
    import termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    # Temporarily restore standard terminal flags for typing prompts
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    try:
        rows, _ = os.get_terminal_size()
    except Exception:
        rows = 24
    
    print(f"\033[{rows-3};0H\033[J")
    print(f"\033[1;33mAdd Node to {env}...\033[0m")
    try:
        name = input("Enter Node Name: ").strip()
        addr = input("Enter IP/Hostname: ").strip()
        dtype = input("Enter Device Type (Server/Router/Switch/Firewall/Gateway/Other) [Server]: ").strip() or "Server"
        if name and addr:
            add_node(env, name, addr, dtype)
    except Exception:
        pass

def tui_delete_node(env, selected_row):
    envs_data = config.get("environments", {})
    nodes = envs_data.get(env, [])
    if selected_row < 0 or selected_row >= len(nodes):
        return
        
    node = nodes[selected_row]
    nid = node.get("id")
    name = node.get("name")
    
    try:
        rows, _ = os.get_terminal_size()
    except Exception:
        rows = 24
        
    print(f"\033[{rows-2};0H\033[J")
    confirm = input(f"\033[1;31mDelete Node '{name}' (ID: {nid})? (y/n): \033[0m").strip().lower()
    if confirm == "y":
        delete_node(env, nid)

def tui_sweep_now(env):
    lower_env = env.lower().replace(" ", "_")
    status_file = os.path.join(STATUS_DIR, f"{lower_env}.status")
    
    try:
        rows, _ = os.get_terminal_size()
    except Exception:
        rows = 24
        
    print(f"\033[{rows-2};0H\033[J")
    print(f"\033[1;32mSweeping nodes in {env}... Please wait...\033[0m", end="", flush=True)
    
    reload_config()
    settings = get_settings()
    envs_data = config.get("environments", {})
    nodes = envs_data.get(env, [])
    
    ping_count = int(settings.get("ping_count", 5))
    ping_interval = float(settings.get("ping_interval", 0.2))
    
    statuses = load_statuses(env)
    
    def ping_node(node):
        nid = str(node.get("id"))
        addr = node.get("addr")
        prev = statuses.get(nid, {"status": "UP", "down_since": "", "history": "." * 24})
        prev_h = prev["history"]
        if len(prev_h) < 24:
            prev_h = "." * (24 - len(prev_h)) + prev_h
            
        cmd = ["ping", "-c", str(ping_count), "-i", str(ping_interval), "-w", str(ping_count + 2), addr]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode == 0:
            new_h = prev_h[1:] + "1"
            avg_rtt = "0.0 ms"
            match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/", res.stdout)
            if match:
                avg_rtt = f"{match.group(1)} ms"
            return f"{nid}|UP|{avg_rtt}||{new_h}\n"
        else:
            new_h = prev_h[1:] + "0"
            since = prev["down_since"]
            if prev["status"] != "DOWN" or not since:
                since = time.strftime('%H:%M:%S')
            return f"{nid}|DOWN|N/A|{since}|{new_h}\n"
            
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(ping_node, nodes))
        
    try:
        with open(status_file, "w") as f:
            f.writelines(results)
    except Exception:
        pass

def run_tui_loop():
    active_tab = 0
    sel_row = 0
    
    # Hide cursor
    print("\033[?25l", end="")
    try:
        while True:
            reload_config()
            environments = get_environments()
            active_env = environments[active_tab]
            
            # Bound check rows
            envs_data = config.get("environments", {})
            nodes = envs_data.get(active_env, [])
            if sel_row >= len(nodes):
                sel_row = max(0, len(nodes) - 1)
                
            redraw_tui(active_tab, sel_row)
            
            key = get_key_tui()
            if key == "\t":
                active_tab = (active_tab + 1) % len(environments)
                sel_row = 0
            elif key == "UP":
                if sel_row > 0:
                    sel_row -= 1
            elif key == "DOWN":
                if sel_row < len(nodes) - 1:
                    sel_row += 1
            elif key in ("a", "A"):
                tui_add_node(active_env)
            elif key in ("d", "D"):
                tui_delete_node(active_env, sel_row)
            elif key in ("r", "R"):
                tui_sweep_now(active_env)
            elif key in ("q", "Q"):
                break
    finally:
        # Show cursor and clean term
        print("\033[?25h\033[H\033[J", end="")

def stop_background_daemons():
    for name in ("daemon.pid", "web.pid"):
        pid_file = os.path.join(PID_DIR, name)
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 15)
                os.remove(pid_file)
                print(f"Stopped {name.replace('.pid', '')} (PID: {pid}).")
            except Exception:
                pass

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--daemon":
            run_sweeper_daemon()
        elif arg == "--web":
            run_webserver()
        elif arg == "--add":
            if len(sys.argv) < 5:
                print("Usage: terminus.py --add <env> <name> <addr> [dev_type]")
                sys.exit(1)
            env = sys.argv[2]
            name = sys.argv[3]
            addr = sys.argv[4]
            dtype = sys.argv[5] if len(sys.argv) > 5 else "Server"
            add_node(env, name, addr, dtype)
            print("Node added.")
        elif arg == "--del":
            if len(sys.argv) < 4:
                print("Usage: terminus.py --del <env> <id>")
                sys.exit(1)
            env = sys.argv[2]
            nid = sys.argv[3]
            delete_node(env, nid)
            print("Node deleted.")
        elif arg == "--stop":
            stop_background_daemons()
        elif arg in ("--help", "-h"):
            print("TERMINUS - Standalone Network Operations Monitor (Pure Python 3)")
            print("Usage:")
            print("  ./terminus.py                  Start interactive TUI console")
            print("  ./terminus.py --daemon         Run sweep daemon in foreground")
            print("  ./terminus.py --web            Run web config server on port 8085")
            print("  ./terminus.py --add <env> <n> <a> [t] Add a node to an environment")
            print("  ./terminus.py --del <env> <id>  Delete a node by ID from an environment")
            print("  ./terminus.py --stop           Stop background services")
            print("  ./terminus.py --help           Show this help menu")
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)
    else:
        # TUI Mode execution: auto-spawn background services if not running
        # Start daemon
        dpid = ""
        daemon_pid_path = os.path.join(PID_DIR, "daemon.pid")
        if os.path.exists(daemon_pid_path):
            with open(daemon_pid_path, "r") as f:
                dpid = f.read().strip()
        if not dpid or not os.path.exists(f"/proc/{dpid}"):
            subprocess.Popen([sys.executable, __file__, "--daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.1)
            
        # Start web server
        wpid = ""
        web_pid_path = os.path.join(PID_DIR, "web.pid")
        if os.path.exists(web_pid_path):
            with open(web_pid_path, "r") as f:
                wpid = f.read().strip()
        if not wpid or not os.path.exists(f"/proc/{wpid}"):
            subprocess.Popen([sys.executable, __file__, "--web"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.1)
            
        run_tui_loop()
