#!/usr/bin/env python3
import subprocess
import re
from pathlib import Path

def get_git_log() -> str:
    # Get last 5 commits: hash, date (local time), subject
    # %h: abbreviated commit hash
    # %cd: commit date (respects --date option)
    # %s: subject (commit message)
    cmd = ["git", "log", "-n", "5", "--invert-grep", "--grep=auto-doc", "--pretty=format:- **%h** - %cd - %s", "--date=format:%Y-%m-%d %H:%M:%S"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()

def main():
    repo_root = Path(__file__).resolve().parent.parent
    readme_path = repo_root / "README.md"
    
    if not readme_path.exists():
        return
        
    # Get the latest 5 commits
    commits_text = get_git_log()
    
    # Read README
    with open(readme_path, 'r', errors='ignore') as f:
        content = f.read()
        
    start_tag = "<!-- AUTO-GENERATED COMMITS START -->"
    end_tag = "<!-- AUTO-GENERATED COMMITS END -->"
    
    block_content = f"{start_tag}\n## Recent Commits\n\n{commits_text}\n{end_tag}"
    
    pattern = rf"{start_tag}.*?{end_tag}"
    if re.search(pattern, content, re.DOTALL):
        # Replace existing block
        new_content = re.sub(pattern, block_content, content, flags=re.DOTALL)
    else:
        # Append to the end of the file
        new_content = content.rstrip() + "\n\n" + block_content + "\n"
        
    with open(readme_path, 'w') as f:
        f.write(new_content)
        
    print("[+] README.md commit log updated.")

if __name__ == "__main__":
    main()
