# User Account Decommissioning Utility (`remove_user.sh`)

A comprehensive, production-grade Bash script designed to safely, securely, and completely remove a user account from an Ubuntu system. 

It handles everything from process termination and service teardown to home directory backups, Samba share cleanups, and sudoers rule management.

---

## Features

- **Robust Safety Constraints**:
  - Requires root (`sudo`) privilege execution.
  - Prevents accidental deletion of the `root` account, the active `sudo` user running the script, and the currently logged-in user session.
  - Interactive validation and warning gate when attempting to delete system accounts (UID < 1000).
- **Session & Process Teardown**:
  - Automatically identifies and terminates systemd user service managers (`user@UID.service`).
  - Sends soft `SIGTERM` and escalates to `SIGKILL` for lingering processes owned by the user.
- **Sudoers Syntax Validation**:
  - Comments out specific privileges in `/etc/sudoers` rather than deleting the lines (allowing easy auditing).
  - Automatically runs `visudo -c` validation to prevent syntax lockouts and restores backup file on failure.
  - Automatically deletes user-specific custom drop-in config files from `/etc/sudoers.d/`.
- **Cron, Spool, & Mail Cleanup**:
  - Deletes all user scheduled `crontabs` and mail spools.
- **Samba share / Windows credential cleanup**:
  - Checks if Samba is present and removes user credentials from the database via `smbpasswd -x`.
- **Primary Group Purge**:
  - Verifies and deletes the user's primary private group (if left empty after deletion).
- **Home Directory Archiving (Optional)**:
  - Supports compressed `.tar.gz` backups of the user's home folder saved to `/var/backups/remove_user_backups/` before directory deletion.
- **Global Filesystem Purge (Optional)**:
  - Offers recursive filesystem-wide search and delete for all files owned by the user's UID (excluding safe system paths like `/proc`, `/sys`, `/dev`, and `/run`).
- **Fully Automated (Non-Interactive) Support**:
  - Provides a `-y` or `--yes` option to auto-confirm prompts, making it suitable for DevOps pipelines.
- **Dry-Run Mode**:
  - Supports a `-d` or `--dry-run` option to simulate operations and view logs without modifying system files.
- **System Logging**:
  - Records script output to `/var/log/remove_user-$username.log` (falling back to `/tmp/` if necessary) for auditing.

---

## Options & Arguments

```text
Usage: sudo ./remove_user.sh [options] <username>
       sudo ./remove_user.sh [options] -u <username>

Options:
  -u, --user <name>      Specify the user account to remove
  -y, --yes              Assume 'yes' to all prompts (non-interactive mode)
  -d, --dry-run          Show what would be done without modifying the system
  -backup true|false     Backup the user's home folder before deletion (default: false)
  -h, -help, --help      Show this help message
```

---

## Execution Walkthrough

The script runs in the following sequence:
1. **Pre-Flight Validation**: Verifies root permissions, validates the username format, checks if the account exists, and performs safety/UID checks.
2. **Setup Logging**: Initializes `/var/log/remove_user-<username>.log` and redirects stdout and stderr (skipped during dry runs).
3. **Backup Phase**: Creates a `.tar.gz` archive of the home directory (if `-backup true` is requested).
4. **Session & Process Teardown**: Terminates active sessions (`loginctl`) and kills running processes.
5. **Sudoers Cleanup**: Clears entries from `/etc/sudoers` (validating with `visudo`) and `/etc/sudoers.d/`.
6. **Samba Cleanup**: Deletes the user entry in the Samba database.
7. **Cron & Mail Cleanup**: Deletes user crontabs and `/var/mail/` files.
8. **Account Deletion**: Invokes `deluser --remove-home` (or `userdel -r` fallback) to delete the account and home folder.
9. **Group Cleanup**: Removes the private group if it remains.
10. **Filesystem Purge (Optional)**: Performs global cleanup of files owned by the UID outside of home.
11. **Verification**: Queries `/etc/passwd` to verify the user has been fully removed.

---

## Usage Examples

### 1. View the Help screen
```bash
sudo ./remove_user.sh --help
```

### 2. Standard Interactive Deletion
Deletes the user, terminates running tasks, but does not backup their home folder. Prompts for verification before critical decisions.
```bash
sudo ./remove_user.sh testuser
```

### 3. Deletion with Home Folder Backup
Backs up `/home/testuser` to `/var/backups/remove_user_backups/testuser_home_backup_<timestamp>.tar.gz` before deleting it:
```bash
sudo ./remove_user.sh -backup true -u testuser
```

### 4. Non-Interactive Automated Mode (e.g., in CI/CD or Cron)
Runs without asking for any prompt confirmations:
```bash
sudo ./remove_user.sh -y -u testuser
```

### 5. Dry-Run Check
Simulate a user decommissioning with a backup to inspect the logs without modifying the server:
```bash
sudo ./remove_user.sh --dry-run -backup true -u testuser
```
