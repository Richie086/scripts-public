#!/bin/bash

# ==============================================================================
# Script Name: user_manager.sh
# Description: Advanced Linux user account manager for Ubuntu.
#              Supports interactive and CLI mode, audit logging, and dry-runs.
# ==============================================================================

# --- Colors & Styling ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# --- Globals ---
AUDIT_LOG="/var/log/user_manager_audit.log"
DRY_RUN=0

# Variables from CLI
CLI_USER=""
CLI_PASS=""
CLI_UID=""
CLI_GID=""
CLI_HOME=""
CLI_SHELL=""

# --- Helper Functions ---
log_audit() {
    local msg="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    if [[ $DRY_RUN -eq 0 ]]; then
        echo "$msg" >> "$AUDIT_LOG"
    fi
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log_audit "SUCCESS: $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    log_audit "ERROR: $1"
}

print_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log_audit "WARNING: $1"
}

print_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script requires root privileges."
        exit 1
    fi
}

check_permissions() {
    if [[ $DRY_RUN -eq 0 ]] && [ ! -w "$(dirname "$AUDIT_LOG")" ]; then
        print_error "Cannot write to log directory $(dirname "$AUDIT_LOG")."
        exit 1
    fi
}

# --- Core Operations ---
exec_cmd() {
    local cmd="$1"
    local desc="$2"

    if [[ $DRY_RUN -eq 1 ]]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would execute: ${BOLD}$cmd${NC}"
        return 0
    else
        eval "$cmd"
        local status=$?
        if [ $status -eq 0 ]; then
            print_success "$desc completed successfully."
            return 0
        else
            print_error "$desc failed with exit code $status."
            return $status
        fi
    fi
}

do_create_user() {
    local user="$1"
    local pword="$2"
    local uid="$3"
    local gid="$4"
    local homedir="$5"
    local tshell="$6"

    if id "$user" &>/dev/null; then
        print_error "User '$user' already exists."
        return 1
    fi

    local cmd="useradd -m"
    [[ -n "$tshell" ]] && cmd+=" -s \"$tshell\"" || cmd+=" -s /bin/bash"
    [[ -n "$homedir" ]] && cmd+=" -d \"$homedir\""
    [[ -n "$uid" ]] && cmd+=" -u $uid"
    [[ -n "$gid" ]] && cmd+=" -g $gid"
    cmd+=" \"$user\""

    exec_cmd "$cmd" "Create user '$user'"
    local create_status=$?

    if [[ $create_status -eq 0 && -n "$pword" ]]; then
        if [[ $DRY_RUN -eq 1 ]]; then
            echo -e "${YELLOW}[DRY-RUN]${NC} Would set password for: ${BOLD}$user${NC}"
        else
            echo "$user:$pword" | chpasswd
            if [ $? -eq 0 ]; then
                print_success "Password set for '$user'."
            else
                print_error "Failed to set password for '$user'."
            fi
        fi
    fi
}

do_add_group() {
    local user="$1"
    local group="$2"

    if ! getent group "$group" &>/dev/null; then
        print_error "Group '$group' does not exist."
        return 1
    fi
    exec_cmd "usermod -aG \"$group\" \"$user\"" "Add '$user' to group '$group'"
}

do_config_sudo() {
    local user="$1"
    local opt="$2"
    local custom="$3"
    local sudoers_file="/etc/sudoers.d/$user"

    if [[ $DRY_RUN -eq 1 ]]; then
        echo -e "${YELLOW}[DRY-RUN]${NC} Would create sudoers file $sudoers_file for $user."
        return 0
    fi

    case $opt in
        1) echo "$user ALL=(ALL) NOPASSWD: ALL" > "$sudoers_file" ;;
        2) echo "$user ALL=(ALL:ALL) ALL" > "$sudoers_file" ;;
        3) echo "$user ALL=(ALL) $custom" > "$sudoers_file" ;;
        4) echo "$user ALL=(ALL) NOPASSWD: $custom" > "$sudoers_file" ;;
        *) return 1 ;;
    esac

    if visudo -cf "$sudoers_file" &>/dev/null; then
        chmod 440 "$sudoers_file"
        print_success "Sudo config saved for '$user'."
    else
        print_error "Sudo config invalid. Reverting."
        rm -f "$sudoers_file"
    fi
}

# --- Interactive Menu ---
draw_box() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} ${BOLD}         Linux User Manager Tool (Advanced)         ${NC}${BLUE}║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║${NC}  1. Create a new user                              ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  2. Add an existing user to a group                ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  3. Configure sudo access for a user               ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}  4. Exit                                           ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
}

interactive_mode() {
    while true; do
        clear
        draw_box
        echo -n -e "${CYAN}Please enter your choice (1-4): ${NC}"
        read choice
        
        case $choice in
            1)
                echo -n "Username: "
                read user
                echo -n "Password (leave blank for none): "
                read -s pword; echo
                echo -n "UID (leave blank for default): "
                read uid
                echo -n "GID (leave blank for default): "
                read gid
                echo -n "Home Dir (leave blank for /home/$user): "
                read homedir
                echo -n "Shell (leave blank for /bin/bash): "
                read tshell
                do_create_user "$user" "$pword" "$uid" "$gid" "$homedir" "$tshell"
                read -p "Press [ENTER] to continue..."
                ;;
            2)
                echo -n "Username: "
                read user
                echo -n "Group name: "
                read group
                do_add_group "$user" "$group"
                read -p "Press [ENTER] to continue..."
                ;;
            3)
                echo -n "Username: "
                read user
                echo "1) NOPASSWD: ALL"
                echo "2) ALL (requires password)"
                echo "3) Specific commands"
                echo "4) Specific commands NOPASSWD"
                echo -n "Option: "
                read opt
                custom=""
                if [[ $opt -eq 3 || $opt -eq 4 ]]; then
                    echo -n "Enter commands (e.g. /bin/systemctl restart nginx): "
                    read custom
                fi
                do_config_sudo "$user" "$opt" "$custom"
                read -p "Press [ENTER] to continue..."
                ;;
            4)
                print_info "Exiting."
                exit 0
                ;;
            *)
                print_error "Invalid choice."
                sleep 1
                ;;
        esac
    done
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -username  <name>    Username to create/modify"
    echo "  -password  <pass>    Password for the user"
    echo "  -UID       <uid>     Custom UID"
    echo "  -GID       <gid>     Custom GID"
    echo "  -home      <dir>     Custom home directory"
    echo "  -terminal  <shell>   Custom shell (e.g. /bin/bash)"
    echo "  -d, --dry-run        Do not execute actions, only print"
    echo "  -help, --help        Show this help message"
    echo ""
}

# --- Main Logic ---
check_root

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -username) CLI_USER="$2"; shift 2 ;;
        -password) CLI_PASS="$2"; shift 2 ;;
        -UID) CLI_UID="$2"; shift 2 ;;
        -GID) CLI_GID="$2"; shift 2 ;;
        -home) CLI_HOME="$2"; shift 2 ;;
        -terminal) CLI_SHELL="$2"; shift 2 ;;
        -d|--dry-run) DRY_RUN=1; shift ;;
        -help|--help) show_help; exit 0 ;;
        *) print_error "Unknown parameter passed: $1"; exit 1 ;;
    esac
done

check_permissions

if [[ -n "$CLI_USER" ]]; then
    # CLI Mode executed
    print_info "CLI Mode Triggered for user: $CLI_USER"
    do_create_user "$CLI_USER" "$CLI_PASS" "$CLI_UID" "$CLI_GID" "$CLI_HOME" "$CLI_SHELL"
else
    # Interactive Mode
    interactive_mode
fi
