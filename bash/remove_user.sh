#!/usr/bin/env bash
#
# Completely remove a user account from an Ubuntu system.
#
# This script terminates the user's active processes, stops user services,
# removes crontabs, deletes user-specific sudo rules, removes the user
# from the system, deletes the home directory, and optionally removes
# any files owned by the user across the entire system.
#
# Usage:
#   sudo ./remove_user.sh [options] <username>
#   sudo ./remove_user.sh [options] -u <username>
#
# Options:
#   -u, --user <name>      Specify the user account to remove
#   -y, --yes              Assume 'yes' to all prompts (non-interactive mode)
#   -d, --dry-run          Show what would be done without modifying the system
#   -backup true|false     Backup the user's home folder before deletion (default: false)
#   -h, -help, --help      Show this help message

# Exit immediately on uncaught errors
set -euo pipefail

# ANSI color codes for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure the script is run as root
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run as root (sudo).${NC}" >&2
    exit 1
fi

# Print usage information
show_help() {
    echo "Usage: $0 [options] [<username>]"
    echo "       $0 [options] -u <username>"
    echo ""
    echo "Options:"
    echo "  -u, --user <name>      Specify the user account to remove"
    echo "  -y, --yes              Assume 'yes' to all prompts (non-interactive mode)"
    echo "  -d, --dry-run          Show what would be done without modifying the system"
    echo "  -backup true|false     Backup the user's home folder before deletion (default: false)"
    echo "  -h, -help, --help      Show this help message"
    exit 0
}

# Parse options manually to support -help, --help, and other long options
FORCE=false
DRY_RUN=false
BACKUP=false
USERNAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|-help|--help)
            show_help
            ;;
        -y|--yes)
            FORCE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -backup|--backup)
            if [[ $# -lt 2 ]]; then
                echo -e "${RED}Error: Option '$1' requires an argument (true/false).${NC}" >&2
                show_help
            fi
            if [[ "$2" == "true" ]]; then
                BACKUP=true
            elif [[ "$2" == "false" ]]; then
                BACKUP=false
            else
                echo -e "${RED}Error: Invalid argument '$2' for option '$1'. Must be true or false.${NC}" >&2
                show_help
            fi
            shift 2
            ;;
        -u|--user)
            if [[ $# -lt 2 ]]; then
                echo -e "${RED}Error: Option '$1' requires an argument.${NC}" >&2
                show_help
            fi
            if [[ -n "$USERNAME" ]]; then
                echo -e "${RED}Error: Multiple usernames specified.${NC}" >&2
                show_help
            fi
            USERNAME="$2"
            shift 2
            ;;
        -*)
            echo -e "${RED}Error: Unknown option '$1'${NC}" >&2
            show_help
            ;;
        *)
            if [[ -n "$USERNAME" ]]; then
                echo -e "${RED}Error: Multiple usernames specified.${NC}" >&2
                show_help
            fi
            USERNAME="$1"
            shift
            ;;
    esac
done

# Check for required username argument
if [[ -z "$USERNAME" ]]; then
    echo -e "${RED}Error: Username is required.${NC}" >&2
    show_help
fi

# Basic validation of username format
if [[ ! "$USERNAME" =~ ^[a-z_][a-z0-9_-]*\$?$ ]]; then
    echo -e "${RED}Error: Invalid username format '$USERNAME'.${NC}" >&2
    exit 1
fi

# Check if user exists
if ! id "$USERNAME" &>/dev/null; then
    echo -e "${RED}Error: User '$USERNAME' does not exist on this system.${NC}" >&2
    exit 1
fi

# Retrieve UID and Home Directory
USER_UID=$(id -u "$USERNAME")
USER_HOME=$(getent passwd "$USERNAME" | cut -d: -f6)

# Safety Checks
if [[ "$USERNAME" == "root" ]]; then
    echo -e "${RED}Error: Cannot delete the 'root' user!${NC}" >&2
    exit 1
fi

# Avoid deleting currently logged-in user running sudo
if [[ -n "${SUDO_USER:-}" ]] && [[ "$USERNAME" == "$SUDO_USER" ]]; then
    echo -e "${RED}Error: Cannot delete the active sudo user '$USERNAME' running this script!${NC}" >&2
    exit 1
fi

# Avoid deleting current shell user
if [[ "$USERNAME" == "$(whoami)" ]]; then
    echo -e "${RED}Error: Cannot delete the currently logged-in user!${NC}" >&2
    exit 1
fi

# Warn if deleting a system account (UID < 1000)
if [[ $USER_UID -lt 1000 ]]; then
    echo -e "${YELLOW}Warning: '$USERNAME' is a system user (UID: $USER_UID < 1000).${NC}"
    if [[ "$FORCE" != "true" ]]; then
        read -p "Are you sure you want to delete this system user? (y/N): " confirm < /dev/tty
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
fi

# Set up logging to /var/log/remove_user-$username.log if not in dry-run mode
if [[ "$DRY_RUN" == "false" ]]; then
    # Ensure log directory exists
    mkdir -p /var/log
    LOGFILE="/var/log/remove_user-${USERNAME}.log"
    
    # Try touching/writing to the log file to verify permissions
    if ! touch "$LOGFILE" 2>/dev/null; then
        echo -e "${YELLOW}Warning: Cannot write to /var/log. Logging to /tmp/remove_user-${USERNAME}.log instead.${NC}" >&2
        LOGFILE="/tmp/remove_user-${USERNAME}.log"
        touch "$LOGFILE" || {
            echo -e "${RED}Error: Cannot create log file in /tmp either. Aborting.${NC}" >&2
            exit 1
        }
    fi
    
    # Redirect all stdout and stderr of the remaining script to both terminal and the logfile
    exec > >(tee -a "$LOGFILE") 2>&1
    
    echo "Logging script output to: $LOGFILE"
    echo "Log started at $(date)" >> "$LOGFILE"
else
    echo -e "${BLUE}[DRY-RUN] Dry run active. System modifications will be skipped.${NC}"
fi

echo -e "${BLUE}=== Starting Complete Removal of User: $USERNAME ===${NC}"

# 0. Backup user home directory if specified
if [[ "$BACKUP" == "true" ]]; then
    BACKUP_DIR="/var/backups/remove_user_backups"
    BACKUP_FILE="${BACKUP_DIR}/${USERNAME}_home_backup_$(date +%F_%H%M%S).tar.gz"
    echo -e "${YELLOW}[Backup] Preparing backup of home directory: $USER_HOME...${NC}"
    
    if [[ -n "$USER_HOME" ]] && [[ -d "$USER_HOME" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${BLUE}[DRY-RUN] Would create backup: tar -czf $BACKUP_FILE -C $(dirname "$USER_HOME") $(basename "$USER_HOME")${NC}"
        else
            echo "Creating backup of $USER_HOME to $BACKUP_FILE..."
            mkdir -p "$BACKUP_DIR"
            if tar -czf "$BACKUP_FILE" -C "$(dirname "$USER_HOME")" "$(basename "$USER_HOME")"; then
                echo -e "${GREEN}Backup successfully saved to: $BACKUP_FILE${NC}"
            else
                echo -e "${RED}Warning: Failed to create backup of home directory.${NC}" >&2
                if [[ "$FORCE" != "true" ]]; then
                    read -p "Do you want to continue with user deletion without a backup? (y/N): " continue_without_backup < /dev/tty
                    if [[ ! "$continue_without_backup" =~ ^[Yy]$ ]]; then
                        echo "Aborted."
                        exit 1
                    fi
                else
                    echo "Force mode active. Continuing without backup."
                fi
            fi
        fi
    else
        echo -e "${YELLOW}Warning: Home directory '$USER_HOME' does not exist. Skipping backup.${NC}"
    fi
fi

# 1. Terminate running processes and user services
echo -e "${YELLOW}[1/7] Checking for active processes and user sessions...${NC}"
if pgrep -u "$USERNAME" >/dev/null || loginctl list-users | grep -q "$USERNAME"; then
    echo "Found running processes or active sessions for user '$USERNAME'."
    CONFIRM_KILL="y"
    if [[ "$FORCE" != "true" ]]; then
        read -p "Terminate all active user processes and sessions? (y/N): " CONFIRM_KILL < /dev/tty
    fi

    if [[ "$CONFIRM_KILL" =~ ^[Yy]$ ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${BLUE}[DRY-RUN] Would terminate systemd user services for '$USERNAME'${NC}"
            echo -e "${BLUE}[DRY-RUN] Would send SIGTERM and SIGKILL to remaining processes for '$USERNAME'${NC}"
        else
            echo "Terminating systemd user services..."
            systemctl terminate-user "$USERNAME" 2>/dev/null || true
            
            echo "Sending SIGTERM (15) to processes..."
            pkill -15 -u "$USERNAME" 2>/dev/null || true
            sleep 2
            
            if pgrep -u "$USERNAME" >/dev/null; then
                echo "Processes still running. Sending SIGKILL (9)..."
                pkill -9 -u "$USERNAME" 2>/dev/null || true
                sleep 1
            fi
        fi
    else
        echo -e "${RED}Error: Cannot proceed while user processes are running. Aborting.${NC}" >&2
        exit 1
    fi
fi

# 2. Sudoers Cleanup
echo -e "${YELLOW}[2/7] Cleaning up sudo privileges...${NC}"
# Delete user-specific file in /etc/sudoers.d/
if [[ -f "/etc/sudoers.d/$USERNAME" ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would remove /etc/sudoers.d/$USERNAME${NC}"
    else
        echo "Removing /etc/sudoers.d/$USERNAME..."
        rm -f "/etc/sudoers.d/$USERNAME"
    fi
fi

# Comment out user entries in the main /etc/sudoers
if grep -q -E "^[[:space:]]*${USERNAME}[[:space:]]" /etc/sudoers; then
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would comment out explicit entry for '$USERNAME' in /etc/sudoers${NC}"
    else
        echo "Found explicit entry for '$USERNAME' in /etc/sudoers. Commenting it out..."
        BACKUP_SUDOERS="/etc/sudoers.bak.$(date +%F_%H%M%S)"
        cp /etc/sudoers "$BACKUP_SUDOERS"
        
        # Use sed to comment out the line
        sed -i -E "s/^([[:space:]]*${USERNAME}[[:space:]].*)/# Removed by user deletion script: \1/" /etc/sudoers
        
        # Validate sudoers configuration
        if visudo -c; then
            echo "Sudoers file syntax validated successfully."
            rm -f "$BACKUP_SUDOERS"
        else
            echo -e "${RED}Warning: /etc/sudoers syntax verification failed. Restoring backup!${NC}" >&2
            mv "$BACKUP_SUDOERS" /etc/sudoers
        fi
    fi
fi

# 3. Samba Account Cleanup
echo -e "${YELLOW}[3/7] Cleaning up Samba share database...${NC}"
if command -v pdbedit &>/dev/null && command -v smbpasswd &>/dev/null; then
    if pdbedit -u "$USERNAME" &>/dev/null; then
        echo "Found Samba account for '$USERNAME'. Cleaning up..."
        if [[ "$DRY_RUN" == "true" ]]; then
            echo -e "${BLUE}[DRY-RUN] Would run: smbpasswd -x '$USERNAME'${NC}"
        else
            if smbpasswd -x "$USERNAME" &>/dev/null; then
                echo "Successfully removed '$USERNAME' from Samba database."
            else
                echo -e "${RED}Warning: Failed to remove '$USERNAME' from Samba database.${NC}" >&2
            fi
        fi
    else
        echo "No Samba account found for '$USERNAME'."
    fi
else
    echo "Samba utilities (pdbedit/smbpasswd) not installed. Skipping Samba cleanup."
fi

# 4. Clean up cron jobs
echo -e "${YELLOW}[4/7] Removing user crontabs...${NC}"
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${BLUE}[DRY-RUN] Would remove crontab for '$USERNAME'${NC}"
    if [[ -f "/var/spool/cron/crontabs/$USERNAME" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would remove /var/spool/cron/crontabs/$USERNAME${NC}"
    fi
else
    crontab -r -u "$USERNAME" 2>/dev/null || true
    if [[ -f "/var/spool/cron/crontabs/$USERNAME" ]]; then
        rm -f "/var/spool/cron/crontabs/$USERNAME"
    fi
fi

# 5. Remove mail spool
echo -e "${YELLOW}[5/7] Removing mail spool...${NC}"
if [[ "$DRY_RUN" == "true" ]]; then
    if [[ -f "/var/mail/$USERNAME" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would remove /var/mail/$USERNAME${NC}"
    fi
    if [[ -f "/var/spool/mail/$USERNAME" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would remove /var/spool/mail/$USERNAME${NC}"
    fi
else
    rm -f "/var/mail/$USERNAME" 2>/dev/null || true
    rm -f "/var/spool/mail/$USERNAME" 2>/dev/null || true
fi

# 6. Delete account and home directory
echo -e "${YELLOW}[6/7] Deleting user account and home directory...${NC}"
if [[ "$DRY_RUN" == "true" ]]; then
    if command -v deluser &>/dev/null; then
        echo -e "${BLUE}[DRY-RUN] Would run: deluser --remove-home '$USERNAME'${NC}"
    else
        echo -e "${BLUE}[DRY-RUN] Would run: userdel -r '$USERNAME'${NC}"
    fi
    if [[ -n "$USER_HOME" ]] && [[ -d "$USER_HOME" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would manually remove '$USER_HOME' if system utility failed to delete it${NC}"
    fi
    if [[ -f "/var/lib/systemd/linger/$USERNAME" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would remove /var/lib/systemd/linger/$USERNAME${NC}"
    fi
else
    if command -v deluser &>/dev/null; then
        # Use deluser if available (recommended on Debian/Ubuntu)
        deluser --remove-home "$USERNAME"
    else
        # Fallback to userdel
        userdel -r "$USERNAME"
    fi

    # Clean up home directory manually if it still exists
    if [[ -n "$USER_HOME" ]] && [[ -d "$USER_HOME" ]]; then
        echo "Home directory '$USER_HOME' was not deleted. Removing manually..."
        rm -rf "$USER_HOME"
    fi

    # Remove systemd linger and runtime files if they exist
    if [[ -f "/var/lib/systemd/linger/$USERNAME" ]]; then
        rm -f "/var/lib/systemd/linger/$USERNAME"
    fi
fi

# 7. Group Cleanup
echo -e "${YELLOW}[7/7] Checking for remaining private group...${NC}"
if getent group "$USERNAME" &>/dev/null; then
    echo "Group '$USERNAME' still exists. Attempting removal..."
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would run: groupdel '$USERNAME'${NC}"
    else
        if groupdel "$USERNAME" 2>/dev/null; then
            echo "Successfully removed group '$USERNAME'."
        else
            echo -e "${YELLOW}Warning: Could not remove group '$USERNAME'. It may contain other users.${NC}"
        fi
    fi
else
    echo "No private group '$USERNAME' remaining."
fi

# 8. Global filesystem cleanup of files owned by the user (Optional)
echo -e "${YELLOW}Checking for other files owned by '$USERNAME'...${NC}"
CLEAN_ALL_FILES="n"
if [[ "$FORCE" != "true" ]]; then
    read -p "Do you want to search and delete all files owned by '$USERNAME' (UID: $USER_UID) outside of their home directory? WARNING: This scans the whole system and can be slow. (y/N): " CLEAN_ALL_FILES < /dev/tty
fi

if [[ "$CLEAN_ALL_FILES" =~ ^[Yy]$ ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}[DRY-RUN] Would scan and remove files owned by UID $USER_UID (excluding /proc, /sys, /dev, /run)${NC}"
    else
        echo "Scanning and removing files owned by UID $USER_UID..."
        # Exclude system folders to avoid errors and safety issues
        find / -user "$USER_UID" -not \( -path "/proc/*" -o -path "/sys/*" -o -path "/dev/*" -o -path "/run/*" \) -exec rm -rf {} \; 2>/dev/null || true
    fi
else
    echo "Skipping global filesystem search."
fi

# Final Verification
if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${GREEN}[DRY-RUN] Dry run complete. No changes were made to the system.${NC}"
else
    if id "$USERNAME" &>/dev/null; then
        echo -e "${RED}Error: Failed to completely remove user account '$USERNAME'.${NC}" >&2
        exit 1
    else
        echo -e "${GREEN}Success: User '$USERNAME' (UID: $USER_UID) has been completely removed from the system.${NC}"
    fi
fi
