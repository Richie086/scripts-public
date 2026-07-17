#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import datetime
import zipfile
import glob

def run_cmd(args, cwd=None):
    """Runs a system command, returning stdout and stderr."""
    try:
        res = subprocess.run(
            args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return res.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else str(e)

def perform_git_sync(vault_dir):
    """Checks git status, commits, and pushes changes if needed."""
    git_dir = os.path.join(vault_dir, ".git")
    if not os.path.exists(git_dir):
        print(f"Git Sync Warning: '{vault_dir}' is not a git repository. Skipping git sync.", file=sys.stderr)
        return

    print("Checking git status...")
    status_out, err = run_cmd(["git", "status", "--porcelain"], cwd=vault_dir)
    if err:
        print(f"Error checking git status: {err}", file=sys.stderr)
        return

    if not status_out:
        print("No changes to sync in git repository.")
        return

    print("Staging changes...")
    _, err = run_cmd(["git", "add", "."], cwd=vault_dir)
    if err:
        print(f"Error staging changes: {err}", file=sys.stderr)
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"Auto-backup: {timestamp}"
    print(f"Committing changes: '{commit_msg}'...")
    _, err = run_cmd(["git", "commit", "-m", commit_msg], cwd=vault_dir)
    if err:
        print(f"Error committing changes: {err}", file=sys.stderr)
        return

    print("Pushing to remote repository...")
    _, err = run_cmd(["git", "push"], cwd=vault_dir)
    if err:
        print(f"Warning: Git push encountered errors: {err}", file=sys.stderr)
    else:
        print("Git sync complete!")

def create_zip_archive(vault_dir, backup_dir):
    """Creates a compressed zip archive of the vault, excluding .git folders."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"vault_backup_{timestamp}.zip"
    zip_path = os.path.join(backup_dir, zip_filename)

    print(f"Creating ZIP archive at '{zip_path}'...")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(vault_dir):
                # Modify dirs in-place to prevent os.walk from entering .git folder
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, vault_dir)
                    zipf.write(file_path, arcname)
        print("ZIP archive created successfully.")
    except Exception as e:
        print(f"Error creating ZIP archive: {e}", file=sys.stderr)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        sys.exit(1)

def prune_old_backups(backup_dir, retention):
    """Prunes older backups to enforce the retention limit."""
    pattern = os.path.join(backup_dir, "vault_backup_*.zip")
    backups = sorted(glob.glob(pattern))

    if len(backups) <= retention:
        return

    to_delete = backups[:-retention]
    print(f"Pruning {len(to_delete)} old backup(s)...")
    for path in to_delete:
        try:
            os.remove(path)
            print(f"Deleted old backup: {os.path.basename(path)}")
        except Exception as e:
            print(f"Error deleting old backup '{path}': {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Automated Obsidian Vault Backup and Sync")
    parser.add_argument("--vault-dir", "-v", required=True, help="Path to the Obsidian Vault directory")
    parser.add_argument("--backup-dir", "-b", required=True, help="Path to the directory where zip backups will be saved")
    parser.add_argument("--git-sync", "-g", action="store_true", help="Perform git commit and push if the vault is a git repository")
    parser.add_argument("--retention", "-r", type=int, default=7, help="Number of daily backups to keep (default: 7)")
    
    args = parser.parse_args()

    vault_dir = os.path.abspath(args.vault_dir)
    backup_dir = os.path.abspath(args.backup_dir)

    if not os.path.isdir(vault_dir):
        print(f"Error: Vault directory '{vault_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting Obsidian backup for vault: {vault_dir}")
    
    # 1. Perform Git Sync
    if args.git_sync:
        perform_git_sync(vault_dir)

    # 2. Create ZIP Archive
    create_zip_archive(vault_dir, backup_dir)

    # 3. Prune old backups
    prune_old_backups(backup_dir, args.retention)
    
    print("Backup operation complete!")

if __name__ == "__main__":
    main()
