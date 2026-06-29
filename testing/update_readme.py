#!/usr/bin/env python3
"""
README Catalog Auto-Updater Script
Automatically scans the repository for shell, PowerShell, and Python scripts,
extracts description metadata from headers, and updates README.md's Catalog of Tools.
"""
import os
import re

# Base directory is the repository root (parent of testing/)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
README_PATH = os.path.join(REPO_ROOT, 'README.md')

def get_script_description(filepath):
    """Extracts description from shebang comments or help blocks."""
    ext = os.path.splitext(filepath)[1]
    description = "No description provided."
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if ext == '.sh':
            # Extract first block of comments after shebang
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
            # Extract .DESCRIPTION from Comment Help Block or initial comments
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
            # Extract module docstring
            match = re.search(r'^"""(.*?)"""', content, re.DOTALL)
            if match:
                description = " ".join(match.group(1).strip().splitlines())
            else:
                lines = content.splitlines()
                desc_lines = []
                for line in lines:
                    if line.strip().startswith('#'):
                        clean = line.strip().lstrip('#').strip()
                        if clean and not clean.startswith('==='):
                            desc_lines.append(clean)
                    elif desc_lines:
                        break
                if desc_lines:
                    description = " ".join(desc_lines[:2])
    except Exception as e:
        description = f"Error reading description: {e}"
        
    return description

def main():
    print("Scanning repository directories...")
    categories = {
        'bash': ('🐚 Linux Bash (`/bash`)', '.sh'),
        'powershell': ('🔷 Windows PowerShell (`/powershell`)', '.ps1'),
        'python': ('🐍 Python (`/python`)', '.py'),
        'testing': ('🧪 Testing & Directory Analysis (`/testing`)', '.py'), # Handles python/sh under testing
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
            # Sort files to ensure stable output order
            for file in sorted(files):
                filepath = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                # Check for relevant extensions
                if ext in ['.sh', '.ps1', '.py']:
                    rel_path = os.path.relpath(filepath, REPO_ROOT).replace('\\', '/')
                    
                    # Ignore git hooks and special files
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
    
    if not os.path.exists(README_PATH):
        print(f"Error: {README_PATH} not found.")
        return
        
    with open(README_PATH, 'r', encoding='utf-8') as f:
        readme_content = f.read()
        
    # Regex pattern matching from ## Catalog of Tools to the next horizontal rule or disclaimer section
    pattern = r'(## Catalog of Tools\n\n)(.*?)(?=\n---\n|\n## ⚠️ Disclaimer)'
    
    if re.search(pattern, readme_content, re.DOTALL):
        updated_content = re.sub(pattern, rf'\1{catalog_text}', readme_content, flags=re.DOTALL)
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("README.md Catalog of Tools updated successfully!")
    else:
        print("Could not find Catalog of Tools section in README.md to update.")

if __name__ == '__main__':
    main()
