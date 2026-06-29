# Automating My GitHub Scripts Catalog with an AI Agent (And Preventing "Dumb" Commits)

If you're anything like me, you probably have a junk drawer folder of utility scripts—Bash tools, PowerShell modules, Python snippets, and random Apache configuration wizards. Mine lives in a repository called `scripts-public`. 

The problem with these repos is always maintenance. You add a script, forget to update the `README.md`, and three months later you have no idea what `Create-RecoveryPartition3.ps1` actually does compared to `Create-RecoveryPartition2.ps1` without reading the source.

Recently, I sat down with **Google Antigravity** (an AI-first development agent) and decided to automate the management, documentation, and safety of this repository. Here’s how we did it.

---

## The Goal

We wanted to:
* **Analyze Folder Stats**: Create a script that counts files, folders, and sizes, outputting the stats in neat Markdown.
* **Auto-Document Everything**: Build an updater script that scans the repository, reads docstrings/headers of our scripts, and updates the `README.md` tools table automatically.
* **Safety Verification**: Ensure we never accidentally push sensitive files (like `.pem` keys or credentials) and automate the Git staging and committing steps, pausing for confirmation *only* before the final push.

---

## Step 1: The Directory Statistics Script (`dir_stats.sh`)

First, we wrote a Bash script to count all files, top-level directories, recursive subdirectories, and calculate the overall size of any directory. 

Because we developed this on a Windows host using a Cygwin/Git Bash shell, standard Windows commands like `find` (which searches text files on Windows) conflict with UNIX `find` in the system path. To resolve this, we added auto-detection logic to locate `/usr/bin/find` or `/bin/find`.

Here is the script, placed in **[testing/dir_stats.sh](https://github.com/Richie086/scripts-public/blob/main/testing/dir_stats.sh)**:

```bash
#!/bin/bash
# Target directory to analyze (default: current directory)
TARGET_DIR="${1:-.}"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist." >&2
    exit 1
fi

# Clean up path to absolute path
ABS_TARGET_DIR=$(cd "$TARGET_DIR" && pwd)
OUTPUT_FILE="directory_stats.md"

# Detect and use the correct find utility (avoiding Windows find.exe)
if [ -x "/usr/bin/find" ]; then
    FIND="/usr/bin/find"
elif [ -x "/bin/find" ]; then
    FIND="/bin/find"
else
    FIND="find"
fi

# Calculate counts
TOTAL_FILES=$("$FIND" "$ABS_TARGET_DIR" -type f | wc -l)
TOP_LEVEL_FOLDERS=$("$FIND" "$ABS_TARGET_DIR" -maxdepth 1 -type d | grep -v -e "^$ABS_TARGET_DIR$" | wc -l)
TOTAL_SUBFOLDERS=$("$FIND" "$ABS_TARGET_DIR" -type d | grep -v -e "^$ABS_TARGET_DIR$" | wc -l)
TOTAL_SIZE=$(du -sh "$ABS_TARGET_DIR" 2>/dev/null | cut -f1)

# Generate Markdown Content
MARKDOWN_OUTPUT=$(cat <<EOF
# Directory Statistics Report

- **Target Directory:** \`$ABS_TARGET_DIR\`
- **Date/Time:** \$(date)

## Overview

| Metric | Count / Size |
| :--- | :--- |
| **Total Files** | $TOTAL_FILES |
| **Top-Level Folders** | $TOP_LEVEL_FOLDERS |
| **Total Subfolders (Recursive)** | $TOTAL_SUBFOLDERS |
| **Total Folder Size** | $TOTAL_SIZE |
EOF
)

# Output to file and stdout
echo "$MARKDOWN_OUTPUT" > "$OUTPUT_FILE"
echo "$MARKDOWN_OUTPUT"
```

Running it on our `/bash` subdirectory immediately outputs:

```markdown
# Directory Statistics Report
- Target Directory: /c/Users/Richard Troiano/.gemini/antigravity/scratch/scripts-public/bash

| Metric | Count / Size |
| :--- | :--- |
| Total Files | 2 |
| Top-Level Folders | 0 |
| Total Subfolders (Recursive) | 0 |
| Total Folder Size | 20K |
```

---

## Step 2: Automating README Updates (`update_readme.py`)

Next, we needed to make sure any script we add is documented. Writing description changes manually is tedious. 

We built a Python script, **[testing/update_readme.py](https://github.com/Richie086/scripts-public/blob/main/testing/update_readme.py)**, that:
1. Crawls through all script directories (`bash`, `powershell`, `python`, `web`, `testing`).
2. Opens each script (`.sh`, `.ps1`, `.py`) and extracts help descriptions or shebang comments.
3. Automatically replaces the entire `# Catalog of Tools` section inside `README.md` with a clean, linked list.

```python
#!/usr/bin/env python3
"""
README Catalog Auto-Updater Script
Automatically scans the repository for shell, PowerShell, and Python scripts,
extracts description metadata from headers, and updates README.md's Catalog of Tools.
"""
import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
README_PATH = os.path.join(REPO_ROOT, 'README.md')

def get_script_description(filepath):
    ext = os.path.splitext(filepath)[1]
    description = "No description provided."
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if ext == '.sh':
            lines = content.splitlines()
            desc_lines = []
            for line in lines:
                if line.startswith('#!'):
                    continue
                if line.strip().startswith('#'):
                    clean = line.strip().lstrip('#').strip()
                    if clean and not clean.startswith('==='):
                        desc_lines.append(clean)
                elif desc_lines:
                    break
            if desc_lines:
                description = " ".join(desc_lines[:2])
                
        elif ext == '.ps1':
            match = re.search(r'\.DESCRIPTION\s+(.*?)(?=\.\w+|\s*#>|#\s*=)', content, re.DOTALL | re.IGNORECASE)
            if match:
                description = " ".join(match.group(1).strip().splitlines())
            else:
                lines = content.splitlines()
                desc_lines = []
                for line in lines:
                    if line.strip().startswith('#') or line.strip().startswith('<#') or line.strip().startswith('.DESCRIPTION'):
                        clean = line.strip().lstrip('#').lstrip('<#').strip()
                        if clean and not clean.startswith('==='):
                            desc_lines.append(clean)
                    elif desc_lines:
                        break
                if desc_lines:
                    description = " ".join(desc_lines[:2])
                    
        elif ext == '.py':
            match = re.search(r'^"""(.*?)"""', content, re.DOTALL)
            if match:
                description = " ".join(match.group(1).strip().splitlines())
    except Exception as e:
        description = f"Error reading description: {e}"
        
    return description

def main():
    print("Scanning repository directories...")
    categories = {
        'bash': ('🐚 Linux Bash (`/bash`)', '.sh'),
        'powershell': ('🔷 Windows PowerShell (`/powershell`)', '.ps1'),
        'python': ('🐍 Python (`/python`)', '.py'),
        'testing': ('🧪 Testing & Directory Analysis (`/testing`)', '.py'),
        'web': ('🌐 Web / Server Config (`/web`)', '.sh')
    }
    
    catalog_sections = []
    
    for folder, (header, main_ext) in sorted(categories.items()):
        folder_path = os.path.join(REPO_ROOT, folder)
        if not os.path.isdir(folder_path):
            continue
            
        catalog_sections.append(f"### {header}")
        scripts_found = []
        for root, dirs, files in os.walk(folder_path):
            for file in sorted(files):
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                if ext in ['.sh', '.ps1', '.py']:
                    rel_path = os.path.relpath(filepath, REPO_ROOT).replace('\\', '/')
                    if file.startswith('.') or 'venv' in rel_path or '__pycache__' in rel_path:
                        continue
                    desc = get_script_description(filepath)
                    scripts_found.append(f"* [{file}]({rel_path}): {desc}")
                    
        if scripts_found:
            catalog_sections.extend(scripts_found)
        else:
            catalog_sections.append("*No active scripts documented.*")
        catalog_sections.append("")
        
    catalog_text = "\n".join(catalog_sections)
    
    with open(README_PATH, 'r', encoding='utf-8') as f:
        readme_content = f.read()
        
    pattern = r'(## Catalog of Tools\n\n)(.*?)(?=\n---\n|\n## ⚠️ Disclaimer)'
    
    if re.search(pattern, readme_content, re.DOTALL):
        updated_content = re.sub(pattern, rf'\1{catalog_text}', readme_content, flags=re.DOTALL)
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("README.md Catalog of Tools updated successfully!")

if __name__ == '__main__':
    main()
```

---

## Step 3: Safety Nets & Safe Commit Workflows

Automating Git actions is dangerous if you aren't careful. Hardcoding passwords or committing active TLS keys (`key.pem`) is a fast track to getting compromised.

To solve this, we created local agent rules inside a **[.agents/AGENTS.md](https://github.com/Richie086/scripts-public/blob/main/.agents/AGENTS.md)** file. The rules instruct the AI agent to:
1. **Never** include private/public keys, certificates, or usernames in documentation.
2. Run a pre-commit diff scan (`git diff --cached`) for private key patterns, credential variables, and active `.pem` files.
3. If anything looks off, **halt** immediately and display a caution dialog to the user.
4. If everything is clean, automate `git add`, `git diff`, and `git commit`, but **stop and prompt** the user before running the final `git push`.

### Putting It to the Test: A Real-World Security Scan

To make sure our repository was completely secure, we performed a comprehensive scan on all project files for passwords, usernames, and cryptographic keys.

During the audit, we discovered two tracked files:
* `python/stftp/cert.pem`
* `python/stftp/key.pem`

Even though these were self-signed certificates generated for STFTP testing, checking private keys into Git is a security risk. If pushed to a public repository, they trigger GitHub's Secret Scanning alerts.

To fix this, we ran:
```bash
git rm --cached python/stftp/cert.pem python/stftp/key.pem
```
This command successfully untracked the keys from Git (so they are ignored by the local `.gitignore` rules and never pushed to GitHub) while keeping them intact on my local disk for local testing.

Here is the exact automated pre-push workflow in action:

```text
1. Automated stage: git add testing/update_readme.py README.md
2. Automated scan: git diff --cached (Verified no credentials, keys, or certs were staged)
3. Automated commit: git commit -m "Add auto-updater"
4. Halt for confirmation: "Would you like me to push this commit to GitHub now?" -> User types 'yes' -> git push
```

---

## Conclusion

By spending an hour setting up clean automation paths with Google Antigravity, we now have a repository that documents itself cleanly on every commit, keeps directories structured, and provides a warning system to prevent us from committing sensitive API keys. 

If you want to see the catalog in action or download these tools, head over to the repo at **Richie086/scripts-public**. Happy automating!
