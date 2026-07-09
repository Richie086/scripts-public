#!/usr/bin/env python3
"""
suggest_aliases.py
Suggests aliases and shell functions to add to your .bashrc / .bash_aliases based on command history.
Features:
- Service Suite Detection: Proposes complete systemd/journalctl service aliases (e.g. apache-start).
- Recency Weighting: Weighs recent commands higher in calculation.
- Function Generation: Proposes custom bash functions for multi-step sequences (e.g. mkcd).
- Config Sourcing Check: Automatically offers to wire ~/.bash_aliases to ~/.bashrc.
- Dry-run by default.
"""

import argparse
import collections
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

# Base commands that we ignore for general frequency suggestions
IGNORED_COMMANDS = {
    'ls', 'cd', 'pwd', 'exit', 'history', 'clear', 'mv', 'rm', 'cp', 
    'mkdir', 'cat', 'vi', 'vim', 'nano', 'grep', 'ssh', 'sudo', 'man',
    'which', 'alias', 'unalias', 'echo', 'export', 'source', 'exec',
    'bg', 'fg', 'jobs', 'kill', 'ping', 'curl', 'wget', 'git', 'docker', 'kubectl'
}

# Common base command abbreviations
COMMON_ABBREVIATIONS = {
    'git': 'g',
    'kubectl': 'k',
    'docker': 'd',
    'docker-compose': 'dc',
    'terraform': 'tf',
    'python': 'py',
    'python3': 'py3',
    'pip': 'pip',
    'pip3': 'pip3',
    'ansible': 'ans',
    'kubernetes': 'k8s',
    'gcloud': 'gc',
    'systemctl': 'sys',
    'journalctl': 'j',
}

# Subcommand abbreviations for common tools
SUBCOMMAND_ABBREVIATIONS = {
    'checkout': 'co',
    'commit': 'cm',
    'status': 'st',
    'branch': 'br',
    'diff': 'df',
    'pull': 'pl',
    'push': 'ps',
    'clone': 'cl',
    'merge': 'mg',
    'rebase': 'rb',
    'stash': 'sh',
    'add': 'a',
    'log': 'l',
    'get': 'g',
    'describe': 'des',
    'apply': 'ap',
    'delete': 'del',
    'logs': 'lo',
    'exec': 'ex',
    'up': 'up',
    'down': 'dn',
    'build': 'b',
    'run': 'r',
    'ps': 'ps',
    'images': 'img',
}

# Bash builtins to check for conflicts
BASH_BUILTINS = {
    'alias', 'alloc', 'bg', 'bind', 'break', 'builtin', 'case', 'cd', 'chdir',
    'command', 'compgen', 'complete', 'continue', 'declare', 'dirs', 'disown',
    'echo', 'enable', 'eval', 'exec', 'exit', 'export', 'fc', 'fg', 'file',
    'for', 'function', 'getopts', 'hash', 'help', 'history', 'if', 'in', 'jobs',
    'kill', 'let', 'local', 'logout', 'mapfile', 'popd', 'printf', 'pushd',
    'pwd', 'read', 'readonly', 'return', 'set', 'shift', 'shopt', 'source',
    'suspend', 'test', 'time', 'times', 'trap', 'type', 'typeset', 'ulimit',
    'umask', 'unalias', 'unset', 'wait', 'while'
}

# ANSI colors for styling
if sys.stdout.isatty():
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
else:
    GREEN = YELLOW = RED = BLUE = CYAN = BOLD = RESET = ""


def get_recency_weight(idx: int, total: int) -> float:
    """Computes a weighting factor where newer commands carry more weight."""
    if total <= 1:
        return 1.0
    # First third: 1.0 weight
    if idx < total / 3:
        return 1.0
    # Middle third: 1.5 weight
    elif idx < 2 * total / 3:
        return 1.5
    # Last third (most recent): 2.0 weight
    else:
        return 2.0


def find_history_file() -> Path:
    histfile = os.environ.get('HISTFILE')
    if histfile and Path(histfile).exists():
        return Path(histfile)
    for p in [Path.home() / ".bash_history", Path.home() / ".zsh_history"]:
        if p.exists():
            return p
    return Path.home() / ".bash_history"


def read_history(history_path: Path) -> List[str]:
    if not history_path.exists():
        return []
    commands = []
    try:
        with open(history_path, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or re.match(r"^#\d+$", line):
                    continue
                zsh_match = re.match(r"^:\s*\d+:\d+;(.*)$", line)
                cmd = zsh_match.group(1).strip() if zsh_match else line
                if cmd:
                    commands.append(cmd)
    except Exception as e:
        print(f"{RED}[ERROR] Failed to read history file: {e}{RESET}", file=sys.stderr)
        sys.exit(1)
    return commands


def load_existing_aliases() -> Dict[str, str]:
    aliases = {}
    paths = [Path.home() / ".bashrc", Path.home() / ".bash_aliases", Path.home() / ".bash_profile", Path.home() / ".profile", Path.home() / ".zshrc"]
    shared_bashrc = Path("/opt/shared-scripts/.bashrc")
    if shared_bashrc.exists():
        paths.append(shared_bashrc)
    for path in paths:
        if not path.exists():
            continue
        try:
            with open(path, 'r', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    match = re.match(r"^\s*alias\s+([a-zA-Z0-9_\.-]+)\s*=\s*(['\"]?)(.*?)\2\s*$", line)
                    if match:
                        aliases[match.group(1)] = match.group(3)
        except Exception:
            pass
    return aliases


def load_all_config_contents() -> str:
    paths = [
        Path.home() / ".bashrc",
        Path.home() / ".bash_aliases",
        Path.home() / ".bash_profile",
        Path.home() / ".profile",
        Path.home() / ".zshrc"
    ]
    contents = []
    for path in paths:
        if path.exists():
            try:
                with open(path, 'r', errors='ignore') as f:
                    contents.append(f.read())
            except Exception:
                pass
    return "\n".join(contents)


# --- Service Suite Detection ---

class ServiceInteraction:
    def __init__(self, name: str):
        self.name = name
        self.uses_sudo = False
        self.count = 0.0

def detect_service_interactions(commands: List[str]) -> Dict[str, ServiceInteraction]:
    """Scans history for systemctl and journalctl commands and groups by service."""
    services = {}
    total_cmds = len(commands)
    
    systemctl_actions = {
        'start', 'stop', 'restart', 'status', 'enable', 'disable',
        'reload', 'force-reload', 'mask', 'unmask', 'try-restart', 'condrestart'
    }
    
    # Matches: [sudo] journalctl ... -u [service] ...
    journalctl_pat = re.compile(r"\bjournalctl\b.*?(?:-u\s+|--unit(?:=|\s+))([a-zA-Z0-9_\.\-]+)")
    
    for idx, cmd in enumerate(commands):
        weight = get_recency_weight(idx, total_cmds)
        cmd_clean = re.sub(r'\s+', ' ', cmd).strip()
        has_sudo = "sudo " in cmd_clean or cmd_clean.startswith("sudo")
        
        # 1. Check systemctl
        if "systemctl" in cmd_clean:
            words = cmd_clean.split(' ')
            try:
                sys_idx = words.index("systemctl")
            except ValueError:
                continue
            
            action = None
            service = None
            for i in range(sys_idx + 1, len(words)):
                word = words[i]
                if word in systemctl_actions:
                    action = word
                    # Find the service name (first non-flag word after action)
                    for j in range(i + 1, len(words)):
                        if not words[j].startswith("-"):
                            service = words[j]
                            break
                    break
            
            if service:
                service_clean = service.replace(".service", "")
                if service_clean not in services:
                    services[service_clean] = ServiceInteraction(service_clean)
                services[service_clean].count += weight
                if has_sudo:
                    services[service_clean].uses_sudo = True
            continue
            
        # 2. Check journalctl
        if "journalctl" in cmd_clean:
            jour_m = journalctl_pat.search(cmd_clean)
            if jour_m:
                service = jour_m.group(1)
                service_clean = service.replace(".service", "")
                if service_clean not in services:
                    services[service_clean] = ServiceInteraction(service_clean)
                services[service_clean].count += weight
                if has_sudo:
                    services[service_clean].uses_sudo = True
                
    return services


def generate_service_suite(service: ServiceInteraction) -> List[Tuple[str, str, str]]:
    """Generates the full suite of service control aliases."""
    sudo_pref = "sudo " if service.uses_sudo else ""
    name = service.name
    
    suite = [
        (f"{name}-status", f"{sudo_pref}systemctl status {name}", "Status check"),
        (f"{name}-start", f"{sudo_pref}systemctl start {name}", "Start service"),
        (f"{name}-stop", f"{sudo_pref}systemctl stop {name}", "Stop service"),
        (f"{name}-restart", f"{sudo_pref}systemctl restart {name}", "Restart service"),
        (f"{name}-journalctl", f"{sudo_pref}journalctl -u {name} -f", "View live logs"),
    ]
    return suite


# --- Function Sequence Detection ---

def detect_function_suggestions(commands: List[str], existing_aliases: Dict[str, str], existing_content: str) -> List[Tuple[str, str, str, str]]:
    """Scans history for common multi-step sequences to propose bash shell functions."""
    suggestions = []
    
    # 1. Detect mkdir + cd sequence
    mkdir_cd_count = 0
    same_line_pat = re.compile(r"^\s*mkdir\s+(?:-p\s+)?([a-zA-Z0-9_\.-]+)\s*(&&|;)\s*cd\s+\1\s*$")
    mkdir_pat = re.compile(r"^\s*mkdir\s+(?:-p\s+)?([a-zA-Z0-9_\.-]+)\s*$")
    cd_pat = re.compile(r"^\s*cd\s+([a-zA-Z0-9_\.-]+)\s*$")
    
    i = 0
    total_cmds = len(commands)
    while i < total_cmds:
        cmd = re.sub(r'\s+', ' ', commands[i]).strip()
        weight = get_recency_weight(i, total_cmds)
        
        # Check same line
        if same_line_pat.match(cmd):
            mkdir_cd_count += weight
            i += 1
            continue
            
        # Check consecutive lines
        if i < total_cmds - 1:
            next_cmd = re.sub(r'\s+', ' ', commands[i+1]).strip()
            m1 = mkdir_pat.match(cmd)
            m2 = cd_pat.match(next_cmd)
            if m1 and m2 and m1.group(1) == m2.group(1):
                mkdir_cd_count += weight
                i += 2
                continue
        i += 1
        
    rounded_mkdir_cd = int(round(mkdir_cd_count))
    has_mkcd = 'mkcd' in existing_aliases or re.search(r"\bmkcd\s*\(\)", existing_content)
    if rounded_mkdir_cd >= 2 and not has_mkcd:
        func_body = "mkcd() {\n    mkdir -p \"$1\" && cd \"$1\"\n}"
        suggestions.append((
            "mkcd",
            func_body,
            f"Creates directory & enters it (weighted score: {rounded_mkdir_cd})",
            "mkcd"
        ))
        
    return suggestions


# --- General Alias Logic ---

def generate_alias_name(cmd: str) -> str:
    words = cmd.split(' ')
    if not words:
        return ""
    prefix_abbr = ""
    consumed_words = 0
    if len(words) >= 2 and (words[0], words[1]) == ("docker", "compose"):
        prefix_abbr = "dc"
        consumed_words = 2
    elif words[0] in COMMON_ABBREVIATIONS:
        prefix_abbr = COMMON_ABBREVIATIONS[words[0]]
        consumed_words = 1
    remaining_words = words[consumed_words:]
    if not remaining_words:
        return prefix_abbr
    parts = [prefix_abbr] if prefix_abbr else []
    for i, word in enumerate(remaining_words):
        clean_word = word.lstrip('-')
        if not clean_word:
            continue
        if i == 0 and clean_word in SUBCOMMAND_ABBREVIATIONS:
            parts.append(SUBCOMMAND_ABBREVIATIONS[clean_word])
        else:
            parts.append(clean_word[0])
    alias_name = "".join(parts)
    alias_name = re.sub(r'[^a-z0-9]', '', alias_name.lower())
    if not alias_name:
        alias_name = re.sub(r'[^a-z0-9]', '', cmd.lower())[:3]
    return alias_name


def resolve_conflict(alias_name: str, cmd: str, existing_aliases: Dict[str, str], system_commands: Set[str]) -> Tuple[str, str]:
    if alias_name in existing_aliases:
        target = existing_aliases[alias_name]
        if re.sub(r'\s+', ' ', target).strip() == re.sub(r'\s+', ' ', cmd).strip():
            return alias_name, "Duplicate (already defined)"
        for suffix in ['a', 'b', 'c', '1', '2']:
            candidate = alias_name + suffix
            if candidate not in existing_aliases and candidate not in system_commands:
                return candidate, f"Conflict: existing alias '{alias_name}' (maps to '{target}'). Suggesting '{candidate}'."
        return alias_name + "_custom", f"Conflict: existing alias '{alias_name}'."
    if alias_name in system_commands or shutil.which(alias_name):
        for suffix in ['x', 'c', '1', '2', 't']:
            candidate = alias_name + suffix
            if candidate not in existing_aliases and candidate not in system_commands and not shutil.which(candidate):
                return candidate, f"Conflict: system command '{alias_name}'. Suggesting '{candidate}'."
        return alias_name + "_custom", f"Conflict: system command '{alias_name}'."
    return alias_name, "Available"


def is_service_command(cmd: str) -> bool:
    cmd_clean = re.sub(r'\s+', ' ', cmd).strip()
    return bool(re.match(r"^\s*(sudo\s+)?(systemctl|journalctl)\b", cmd_clean))


def extract_candidates(commands: List[str], min_uses: int) -> List[Tuple[str, int]]:
    counts = collections.Counter()
    total_cmds = len(commands)
    
    for idx, cmd in enumerate(commands):
        weight = get_recency_weight(idx, total_cmds)
        cmd = cmd.strip()
        cmd = re.sub(r'\s+', ' ', cmd)
        if not cmd or is_service_command(cmd):
            continue
        words = cmd.split(' ')
        counts[cmd] += weight
        for i in range(1, min(len(words), 5)):
            prefix = " ".join(words[:i])
            if not is_service_command(prefix):
                counts[prefix] += weight
            
    filtered = []
    for candidate, count in counts.items():
        display_count = int(round(count))
        if display_count < min_uses:
            continue
        words = candidate.split(' ')
        if candidate in IGNORED_COMMANDS:
            continue
        if len(words) == 1:
            if len(candidate) <= 3 or candidate.startswith('-') or candidate in IGNORED_COMMANDS:
                continue
        is_safe = True
        for word in words:
            if '/' in word or '\\' in word or ('.' in word and not word.startswith('-')):
                is_safe = False
                break
            if word.isdigit() and len(word) > 1:
                is_safe = False
                break
            if any(char in word for char in ['=', '>', '<', '|', ';', '&', '*', '?']):
                is_safe = False
                break
        if is_safe:
            filtered.append((candidate, display_count))
            
    filtered.sort(key=lambda x: len(x[0]), reverse=True)
    deduped = []
    seen_prefixes = {}
    for cand, count in filtered:
        is_redundant = False
        for seen_cand, seen_count in seen_prefixes.items():
            if seen_cand.startswith(cand) and count == seen_count:
                is_redundant = True
                break
        if not is_redundant:
            deduped.append((cand, count))
            seen_prefixes[cand] = count
    deduped.sort(key=lambda x: x[1], reverse=True)
    return deduped


def get_default_dest_file() -> Path:
    bash_aliases = Path.home() / ".bash_aliases"
    return bash_aliases if bash_aliases.exists() else Path.home() / ".bashrc"


def write_aliases(selections_to_write: List[Tuple[str, str, str]], dest_file: Path, dry_run: bool):
    if not selections_to_write:
        print("No items selected to be written.")
        return
        
    block_start = "# >>> BASHRC ALIAS SUGGESTER >>>\n"
    block_end = "# <<< BASHRC ALIAS SUGGESTER <<<\n"
    
    new_lines = []
    for name, value, item_type in selections_to_write:
        if item_type == "alias":
            if "'" in value:
                new_lines.append(f"alias {name}=\"{value}\"\n")
            else:
                new_lines.append(f"alias {name}='{value}'\n")
        elif item_type == "function":
            new_lines.append(f"{value}\n\n")
            
    block_content = block_start + "".join(new_lines).strip() + "\n" + block_end
    
    if dry_run:
        print(f"\n{YELLOW}[DRY RUN] Would write the following block to {dest_file}:{RESET}")
        print("-" * 50)
        print(block_content.strip())
        print("-" * 50)
        return
        
    import subprocess
    use_sudo = False
    
    # 1. Try to create backup
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = dest_file.with_suffix(f".bak.{timestamp}")
    
    if dest_file.exists():
        print(f"[+] Creating backup of {dest_file} at {backup}...")
        try:
            shutil.copy(dest_file, backup)
        except PermissionError:
            print(f"{YELLOW}[!] Permission denied backing up to {backup}.{RESET}")
            try:
                confirm = input("Would you like to try backing up and writing using sudo? [y/N]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                confirm = 'n'
            if confirm == 'y':
                use_sudo = True
                try:
                    subprocess.run(['sudo', 'cp', str(dest_file), str(backup)], check=True)
                except Exception as e:
                    print(f"{RED}[ERROR] Failed to backup with sudo: {e}{RESET}", file=sys.stderr)
                    sys.exit(1)
            else:
                sys.exit(1)
        except Exception as e:
            print(f"{RED}[ERROR] Failed to back up configuration: {e}{RESET}", file=sys.stderr)
            sys.exit(1)
            
    # 2. Read existing content
    content = ""
    if dest_file.exists():
        try:
            with open(dest_file, 'r', errors='ignore') as f:
                content = f.read()
        except PermissionError:
            if not use_sudo:
                print(f"{YELLOW}[!] Permission denied reading {dest_file}.{RESET}")
                try:
                    confirm = input("Would you like to try reading and writing using sudo? [y/N]: ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    confirm = 'n'
                if confirm == 'y':
                    use_sudo = True
                else:
                    sys.exit(1)
            
            if use_sudo:
                try:
                    proc = subprocess.run(['sudo', 'cat', str(dest_file)], capture_output=True, text=True, check=True)
                    content = proc.stdout
                except Exception as e:
                    print(f"{RED}[ERROR] Failed to read with sudo: {e}{RESET}", file=sys.stderr)
                    sys.exit(1)
        except Exception as e:
            print(f"{RED}[ERROR] Failed to read {dest_file}: {e}{RESET}", file=sys.stderr)
            sys.exit(1)
            
    # 3. Calculate updated content
    pattern = r"# >>> BASHRC ALIAS SUGGESTER >>>.*# <<< BASHRC ALIAS SUGGESTER <<<\n?"
    if re.search(pattern, content, re.DOTALL):
        updated_content = re.sub(pattern, block_content, content, flags=re.DOTALL)
        print(f"[+] Updating existing ALIAS SUGGESTER block in {dest_file}...")
    else:
        if content and not content.endswith('\n'):
            block_content = "\n" + block_content
        updated_content = content + block_content
        print(f"[+] Appending ALIAS SUGGESTER block to {dest_file}...")
        
    # 4. Write content
    try:
        if use_sudo:
            proc = subprocess.Popen(['sudo', 'tee', str(dest_file)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = proc.communicate(input=updated_content)
            if proc.returncode != 0:
                raise Exception(stderr.strip())
        else:
            with open(dest_file, 'w') as f:
                f.write(updated_content)
        print(f"{GREEN}[SUCCESS] Successfully wrote {len(selections_to_write)} items to {dest_file}!{RESET}")
    except PermissionError:
        print(f"{YELLOW}[!] Permission denied writing to {dest_file}.{RESET}")
        try:
            confirm = input("Would you like to try writing using sudo? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            confirm = 'n'
        if confirm == 'y':
            try:
                proc = subprocess.Popen(['sudo', 'tee', str(dest_file)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = proc.communicate(input=updated_content)
                if proc.returncode != 0:
                    raise Exception(stderr.strip())
                print(f"{GREEN}[SUCCESS] Successfully wrote {len(selections_to_write)} items to {dest_file} using sudo!{RESET}")
            except Exception as sudo_err:
                print(f"{RED}[ERROR] Failed to write using sudo: {sudo_err}{RESET}", file=sys.stderr)
                sys.exit(1)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"{RED}[ERROR] Failed to write to {dest_file}: {e}{RESET}", file=sys.stderr)
        sys.exit(1)

    # 5. Verify sourcing if written to ~/.bash_aliases
    if dest_file.name == ".bash_aliases":
        bashrc_path = Path.home() / ".bashrc"
        if bashrc_path.exists():
            try:
                with open(bashrc_path, 'r', errors='ignore') as f:
                    bashrc_content = f.read()
            except Exception:
                bashrc_content = ""
            if ".bash_aliases" not in bashrc_content:
                print(f"\n{YELLOW}[NOTE] ~/.bash_aliases is not sourced in your ~/.bashrc.{RESET}")
                try:
                    confirm = input(f"Would you like to automatically add the sourcing block to {bashrc_path}? [y/N]: ").strip().lower()
                except (KeyboardInterrupt, EOFError):
                    confirm = 'n'
                if confirm == 'y':
                    bashrc_backup = bashrc_path.with_suffix(f".bak.{timestamp}")
                    print(f"[+] Creating backup of {bashrc_path} at {bashrc_backup}...")
                    try:
                        shutil.copy(bashrc_path, bashrc_backup)
                        source_snippet = "\n# Source custom aliases\nif [ -f ~/.bash_aliases ]; then\n    . ~/.bash_aliases\nfi\n"
                        with open(bashrc_path, 'a') as f_br:
                            f_br.write(source_snippet)
                        print(f"{GREEN}[SUCCESS] Sourcing block appended to {bashrc_path}!{RESET}")
                    except Exception as e:
                        print(f"{RED}[ERROR] Failed to source ~/.bash_aliases: {e}{RESET}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Suggests shell aliases and functions based on command history.")
    parser.add_argument('-f', '--history-file', help="Path to command history file")
    parser.add_argument('-n', '--limit', type=int, default=15, help="Max frequency suggestions")
    parser.add_argument('-m', '--min-uses', type=int, default=3, help="Min command frequency")
    parser.add_argument('-a', '--apply', action='store_true', help="Apply directly without confirmation")
    parser.add_argument('-d', '--dest', help="Destination config file")
    parser.add_argument('-i', '--interactive', action='store_true', help="Interactively accept suggestions")
    
    args = parser.parse_args()
    
    history_file_path = Path(args.history_file) if args.history_file else find_history_file()
    print(f"[+] Using history file: {BLUE}{history_file_path}{RESET}")
    
    if not history_file_path.exists() or history_file_path.stat().st_size == 0:
        print(f"{YELLOW}[WARNING] History file '{history_file_path}' is empty or does not exist.{RESET}")
        print("To flush in-memory history, run: history -a")
        sys.exit(0)
        
    commands = read_history(history_file_path)
    print(f"[+] Loaded {len(commands)} commands from history.")
    
    existing_aliases = load_existing_aliases()
    print(f"[+] Loaded {len(existing_aliases)} existing aliases from shell configs.")
    
    existing_content = load_all_config_contents()
    
    # 1. Service Suite Detection (utilizes weight)
    service_interactions = detect_service_interactions(commands)
    active_services = [s for s in service_interactions.values() if int(round(s.count)) >= max(2, args.min_uses - 1)]
    
    suggested_service_aliases = []
    if active_services:
        print(f"\n{BOLD}{CYAN}=== SERVICE SUITE RECOMMENDATIONS ==={RESET}")
        for s in active_services:
            rounded_weight = int(round(s.count))
            print(f"Service: {BOLD}{s.name}{RESET} (weighted score: {rounded_weight})")
            suite = generate_service_suite(s)
            for alias_name, cmd, desc in suite:
                final_name, status = resolve_conflict(alias_name, cmd, existing_aliases, BASH_BUILTINS)
                print(f"  - {BOLD}{final_name:<20}{RESET} -> {cmd:<35} ({status})")
                if status != "Duplicate (already defined)":
                    suggested_service_aliases.append((final_name, cmd, s.name))
            print()
            
    # 2. General Frequency Suggestions (utilizes weight)
    candidates = extract_candidates(commands, args.min_uses)
    suggested_general_aliases = []
    limit = min(args.limit, len(candidates))
    
    for i in range(limit):
        cmd, count = candidates[i]
        suggested_name = generate_alias_name(cmd)
        if not suggested_name:
            continue
        final_name, status = resolve_conflict(suggested_name, cmd, existing_aliases, BASH_BUILTINS)
        if status != "Duplicate (already defined)":
            suggested_general_aliases.append((final_name, cmd, count, status))
            
    if suggested_general_aliases:
        print(f"{BOLD}{CYAN}=== GENERAL ALIAS RECOMMENDATIONS ==={RESET}")
        print(f"{'Idx':<4} | {'Count':<5} | {'Command':<40} | {'Alias':<12} | {'Status':<30}")
        print("-" * 105)
        for idx, (name, cmd, count, status) in enumerate(suggested_general_aliases, 1):
            cmd_disp = cmd[:37] + "..." if len(cmd) > 37 else cmd
            status_color = GREEN if status == "Available" else YELLOW
            print(f"{idx:<4} | {count:<5} | {cmd_disp:<40} | {BOLD}{name:<12}{RESET} | {status_color}{status}{RESET}")
        print("-" * 105)
        
    # 3. Shell Function Recommendations
    suggested_functions = detect_function_suggestions(commands, existing_aliases, existing_content)
    if suggested_functions:
        print(f"\n{BOLD}{CYAN}=== SHELL FUNCTION RECOMMENDATIONS ==={RESET}")
        for name, body, desc, key in suggested_functions:
            print(f"Function: {BOLD}{name}(){RESET} - {desc}")
            print(f"Definition:\n{body}\n")
            
    if not suggested_service_aliases and not suggested_general_aliases and not suggested_functions:
        print("No new alias or function recommendations generated.")
        sys.exit(0)
        
    # Dry-Run Check / Selection Phase
    if not args.apply and not args.interactive:
        print(f"\n{YELLOW}[DRY RUN MODE] To select and save aliases, run the script with:{RESET}")
        print(f"  {BOLD}python3 {sys.argv[0]} --apply{RESET}        (to select from index list)")
        print(f"  {BOLD}python3 {sys.argv[0]} --interactive{RESET}  (to customize and save one-by-one)")
        sys.exit(0)
        
    dest_path = Path(args.dest) if args.dest else get_default_dest_file()
    selected_items = []
    
    # 4. Interactive/Selection Phase
    if args.interactive:
        # Prompt for service suites first
        if suggested_service_aliases:
            by_service = collections.defaultdict(list)
            for name, cmd, s_name in suggested_service_aliases:
                by_service[s_name].append((name, cmd))
            
            for s_name, aliases in by_service.items():
                print(f"\nWould you like to add the management suite for service '{BOLD}{s_name}{RESET}'?")
                for name, cmd in aliases:
                    print(f"  alias {name}='{cmd}'")
                choice = input("Add this suite? [Y/n/individual]: ").strip().lower()
                if choice in ['', 'y', 'yes']:
                    for name, cmd in aliases:
                        selected_items.append((name, cmd, "alias"))
                elif choice == 'individual':
                    for name, cmd in aliases:
                        sub_choice = input(f"  Add alias '{BOLD}{name}{RESET}'? [Y/n/custom]: ").strip()
                        if sub_choice.lower() == 'n':
                            continue
                        elif sub_choice == '' or sub_choice.lower() == 'y':
                            selected_items.append((name, cmd, "alias"))
                        else:
                            custom = re.sub(r'[^a-zA-Z0-9_-]', '', sub_choice.lower())
                            if custom:
                                selected_items.append((custom, cmd, "alias"))
                                
        # Prompt for general frequency aliases
        if suggested_general_aliases:
            print(f"\n{BOLD}Interactive General Alias Selection:{RESET}")
            for idx, (name, cmd, count, status) in enumerate(suggested_general_aliases, 1):
                choice = input(f"[{idx}] Suggest alias '{BOLD}{name}{RESET}' for '{CYAN}{cmd}{RESET}' (weighted: {count})? [Y/n/custom]: ").strip()
                if choice.lower() == 'n':
                    continue
                elif choice == '' or choice.lower() == 'y':
                    selected_items.append((name, cmd, "alias"))
                else:
                    custom = re.sub(r'[^a-zA-Z0-9_-]', '', choice.lower())
                    if custom:
                        selected_items.append((custom, cmd, "alias"))
                        
        # Prompt for shell functions
        if suggested_functions:
            print(f"\n{BOLD}Interactive Shell Function Selection:{RESET}")
            for name, body, desc, key in suggested_functions:
                choice = input(f"Add function '{BOLD}{name}(){RESET}' ({desc})? [Y/n]: ").strip().lower()
                if choice in ['', 'y', 'yes']:
                    selected_items.append((name, body, "function"))
    else:
        # Non-interactive / index selection
        p_idx = 1
        print("\nSelection Menu:")
        idx_map = {}
        
        if suggested_service_aliases:
            print(f"{BOLD}Service Aliases:{RESET}")
            for name, cmd, s_name in suggested_service_aliases:
                print(f"  [{p_idx}] alias {name}='{cmd}'")
                idx_map[p_idx] = (name, cmd, "alias")
                p_idx += 1
                
        if suggested_general_aliases:
            print(f"{BOLD}General Aliases:{RESET}")
            for name, cmd, count, status in suggested_general_aliases:
                print(f"  [{p_idx}] alias {name}='{cmd}' (score: {count})")
                idx_map[p_idx] = (name, cmd, "alias")
                p_idx += 1
                
        if suggested_functions:
            print(f"{BOLD}Shell Functions:{RESET}")
            for name, body, desc, key in suggested_functions:
                print(f"  [{p_idx}] function {name}() - {desc}")
                idx_map[p_idx] = (name, body, "function")
                p_idx += 1
                
        try:
            choice = input(f"\nSelect indices to save (comma-separated, e.g. 1,3,5), 'all' to select all, or 'q' to quit: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)
            
        if choice.lower() == 'q' or not choice:
            print("[+] No selections made. Exiting.")
            sys.exit(0)
            
        if choice.lower() == 'all':
            selected_items = list(idx_map.values())
        else:
            try:
                indices = [int(i.strip()) for i in choice.split(',') if i.strip()]
                for idx in indices:
                    if idx in idx_map:
                        selected_items.append(idx_map[idx])
                    else:
                        print(f"[!] Warning: Index {idx} out of range.")
            except ValueError:
                print(f"{RED}[ERROR] Invalid selection format.{RESET}")
                sys.exit(1)
                
    if not selected_items:
        print("[+] No items selected.")
        sys.exit(0)
        
    dry_run = not args.apply
    if dry_run:
        print("\nSelected Items:")
        for name, value, item_type in selected_items:
            if item_type == "alias":
                print(f"  alias {name}='{value}'")
            elif item_type == "function":
                print(f"  function {name}() [Definition size: {len(value.splitlines())} lines]")
        try:
            confirm = input(f"\nWrite these to {dest_path}? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print()
            sys.exit(0)
        if confirm == 'y':
            dry_run = False
            
    write_aliases(selected_items, dest_path, dry_run=dry_run)


if __name__ == "__main__":
    main()
