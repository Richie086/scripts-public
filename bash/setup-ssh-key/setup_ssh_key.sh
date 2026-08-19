#!/usr/bin/env bash
#
# Interactive SSH Key Generator & Remote Installer (Modern Theme)
#
# This script guides the user through the process of:
#   1. Prompting for remote server details (username, host, port).
#   2. Configuring and generating a secure Ed25519 SSH keypair.
#   3. Verbosely uploading the public key to the remote server's authorized_keys.
#   4. Verbosely testing the connection using the private and public keys.
#
# DESIGN SYSTEM:
#   Uses a premium dark-themed color palette with 256-color ANSI escape sequences.
#
# ERROR HANDLING:
#   - set -euo pipefail: Exit on error, unset variables, or pipe failures.

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 COLOR PALETTE & UI DESIGN (256-Color Modern Dark Theme)
# ─────────────────────────────────────────────────────────────────────────────
# We use custom 256-color palette to break away from raw ANSI colors and provide
# a sleek, modern UI:
#   - Accent Purple/Indigo (Title & Borders): Color 99
#   - Neon Cyan (Prompts & Highlights): Color 51
#   - Neon Green (Success & Status): Color 84
#   - Pastel Yellow (Warnings): Color 220
#   - Vibrant Red (Errors): Color 197
#   - Muted Charcoal (Command previews & Debug): Color 244
#   - Dark Gray Background (Accent Block): Color 235
# ─────────────────────────────────────────────────────────────────────────────
BG_DARK='\033[48;5;235m'
FG_PURPLE='\033[38;5;99m'
FG_CYAN='\033[38;5;51m'
FG_GREEN='\033[38;5;84m'
FG_YELLOW='\033[38;5;220m'
FG_RED='\033[38;5;197m'
FG_MUTED='\033[38;5;244m'
NC='\033[0m'
BOLD='\033[1m'

# Status indicators
STATUS_RUNNING="${BOLD}${FG_PURPLE}[ RUNNING ]${NC}"
STATUS_SUCCESS="${BOLD}${FG_GREEN}[ SUCCESS ]${NC}"
STATUS_WARNING="${BOLD}${FG_YELLOW}[ WARNING ]${NC}"
STATUS_ERROR="${BOLD}${FG_RED}[  ERROR  ]${NC}"
STATUS_COMMAND="${BOLD}${FG_MUTED}[ COMMAND ]${NC}"

# UI helper functions
print_banner() {
    clear
    echo -e "${FG_PURPLE}┌──────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${FG_PURPLE}│${NC}  ${BOLD}${FG_CYAN}🛡️  SSH KEYGEN & REMOTE DEPLOYER${NC}                                        ${FG_PURPLE}│${NC}"
    echo -e "${FG_PURPLE}│${NC}  ${FG_MUTED}Generates secure Ed25519 keypairs and installs them on remote hosts. ${FG_PURPLE}│${NC}"
    echo -e "${FG_PURPLE}└──────────────────────────────────────────────────────────────────────────┘${NC}"
}

print_step() {
    local step_num="$1"
    local step_title="$2"
    echo -e "\n${BOLD}${FG_PURPLE}Step $step_num: $step_title${NC}"
    echo -e "${FG_PURPLE}────────────────────────────────────────────────────────────────────────────${NC}"
}

log_verbose() {
    echo -e "   ${FG_MUTED}↳ $1${NC}"
}

log_command() {
    echo -e "   ${STATUS_COMMAND} ${FG_MUTED}$1${NC}"
}

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ SYSTEM VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────
# Verify the local SSH directory exists and has standard 700 permissions.
# This prevents OpenSSH from rejecting the local configuration.
ensure_local_ssh_dir() {
    local ssh_dir="${HOME}/.ssh"
    print_step "0" "Verifying Local SSH Environment"
    
    if [[ ! -d "$ssh_dir" ]]; then
        log_verbose "Local directory '$ssh_dir' does not exist."
        log_command "mkdir -p '$ssh_dir' && chmod 700 '$ssh_dir'"
        mkdir -p "$ssh_dir"
        chmod 700 "$ssh_dir"
        echo -e "   ${STATUS_SUCCESS} Created local SSH directory with secure 700 permissions."
    else
        log_verbose "Local SSH directory '$ssh_dir' verified."
        # Ensure permissions are correct
        log_command "chmod 700 '$ssh_dir'"
        chmod 700 "$ssh_dir"
        echo -e "   ${STATUS_SUCCESS} Secured local SSH directory permissions."
    fi
}

main() {
    print_banner
    ensure_local_ssh_dir

    # ─────────────────────────────────────────────────────────────────────────
    # 1. USER INPUTS (Interactive setup)
    # ─────────────────────────────────────────────────────────────────────────
    print_step "1" "Gathering Remote Server Details"

    # Prompt for remote hostname/IP
    while true; do
        echo -e -n "   ${FG_CYAN}Enter remote hostname or IP address:${NC} "
        read -r hostname
        if [[ -n "$hostname" ]]; then
            break
        fi
        echo -e "   ${STATUS_ERROR} Hostname cannot be empty."
    done

    # Prompt for remote username (defaulting to current local user)
    default_user=$(whoami)
    echo -e -n "   ${FG_CYAN}Enter remote username${NC} [default: $default_user]: "
    read -r username
    if [[ -z "$username" ]]; then
        username="$default_user"
    fi
    log_verbose "Selected remote user: $username"

    # Prompt for remote port (defaulting to 22)
    default_port="22"
    echo -e -n "   ${FG_CYAN}Enter remote SSH port${NC} [default: $default_port]: "
    read -r port
    if [[ -z "$port" ]]; then
        port="$default_port"
    fi
    log_verbose "Selected port: $port"

    # ─────────────────────────────────────────────────────────────────────────
    # 2. KEYPAIR CONFIGURATION & GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    print_step "2" "Configuring SSH Key Generation"

    # Suggest a descriptive name based on hostname to keep keys organized
    clean_host="${hostname//./_}"
    default_key_name="id_ed25519_${clean_host}"
    echo -e -n "   ${FG_CYAN}Enter key name${NC} [default: $default_key_name]: "
    read -r key_name
    if [[ -z "$key_name" ]]; then
        key_name="$default_key_name"
    fi

    key_path="${HOME}/.ssh/${key_name}"
    pub_key_path="${key_path}.pub"
    log_verbose "Target private key: $key_path"
    log_verbose "Target public key:  $pub_key_path"

    generate_new=true
    if [[ -f "$key_path" ]]; then
        echo -e "   ${STATUS_WARNING} Key already exists at: $key_path"
        echo -e -n "   ${FG_YELLOW}Do you want to overwrite it? (y/n)${NC} [default: n]: "
        read -r overwrite
        if [[ "$overwrite" =~ ^[Yy]$ ]]; then
            log_verbose "User selected to overwrite existing key."
        else
            generate_new=false
            echo -e "   ${STATUS_SUCCESS} Re-using existing SSH keypair."
        fi
    fi

    if [[ "$generate_new" = true ]]; then
        # ed25519 is the modern standard (most secure, smallest footprint)
        log_verbose "Prompting for passphrase (optional security layer)..."
        echo -e -n "   ${FG_CYAN}Enter optional passphrase (press Enter for none):${NC} "
        read -r -s passphrase
        echo
        echo -e -n "   ${FG_CYAN}Confirm passphrase:${NC} "
        read -r -s passphrase_confirm
        echo
        
        if [[ "$passphrase" != "$passphrase_confirm" ]]; then
            echo -e "   ${STATUS_ERROR} Passphrases do not match!"
            exit 1
        fi

        log_verbose "Executing ssh-keygen for Ed25519..."
        log_command "ssh-keygen -t ed25519 -C \"${username}@${hostname}\" -f \"$key_path\" -N \"<hidden>\""
        ssh-keygen -t ed25519 -C "${username}@${hostname}" -f "$key_path" -N "$passphrase"
        echo -e "   ${STATUS_SUCCESS} Ed25519 keypair successfully generated."
    fi

    # ─────────────────────────────────────────────────────────────────────────
    # 3. REMOTE DEPLOYMENT (authorized_keys addition)
    # ─────────────────────────────────────────────────────────────────────────
    print_step "3" "Deploying Public Key to Remote Host"
    echo -e "   ${FG_YELLOW}Please prepare to enter the remote password for $username@$hostname.${NC}"
    
    # We will try ssh-copy-id first. If unavailable, fall back to shell piping.
    if command -v ssh-copy-id &> /dev/null; then
        log_verbose "ssh-copy-id utility found. Attempting structured installation..."
        log_command "ssh-copy-id -i \"$pub_key_path\" -p \"$port\" \"$username@$hostname\""
        
        if ssh-copy-id -i "$pub_key_path" -p "$port" "$username@$hostname"; then
            echo -e "   ${STATUS_SUCCESS} public key successfully added to remote server using ssh-copy-id."
        else
            echo -e "   ${STATUS_WARNING} ssh-copy-id failed. Trying fallback manual method..."
            fallback_install "$pub_key_path" "$port" "$username" "$hostname"
        fi
    else
        log_verbose "ssh-copy-id utility NOT found. Using manual pipe fallback..."
        fallback_install "$pub_key_path" "$port" "$username" "$hostname"
    fi

    # ─────────────────────────────────────────────────────────────────────────
    # 4. VERIFYING KEY-BASED AUTHENTICATION
    # ─────────────────────────────────────────────────────────────────────────
    print_step "4" "Verifying Remote Connections"
    
    # Test 4.1: Connect using the private key file
    log_verbose "Test 4.1: Initiating connection test using PRIVATE key."
    log_command "ssh -i \"$key_path\" -p \"$port\" -o BatchMode=yes -o ConnectTimeout=5 \"$username@$hostname\""
    
    # BatchMode=yes ensures ssh fails fast without prompting for passwords if key auth fails.
    if ssh -i "$key_path" -p "$port" -o BatchMode=yes -o ConnectTimeout=5 "$username@$hostname" "echo 'Handshake successful'" &>/dev/null; then
        echo -e "   ${STATUS_SUCCESS} Private key authentication successful!"
        private_key_success=true
    else
        echo -e "   ${STATUS_ERROR} Private key authentication failed."
        private_key_success=false
    fi

    # Test 4.2: Connect passing the public key file to -i (user requested check)
    log_verbose "Test 4.2: Initiating connection test using PUBLIC key path."
    log_verbose "This tests if your local SSH agent can locate the corresponding private key."
    log_command "ssh -i \"$pub_key_path\" -p \"$port\" -o BatchMode=yes -o ConnectTimeout=5 \"$username@$hostname\""
    
    if ssh -i "$pub_key_path" -p "$port" -o BatchMode=yes -o ConnectTimeout=5 "$username@$hostname" "echo 'Handshake successful'" &>/dev/null; then
        echo -e "   ${STATUS_SUCCESS} Public key path authentication successful!"
        public_key_success=true
    else
        echo -e "   ${STATUS_WARNING} Public key path authentication failed."
        log_verbose "This is typical behavior if the local SSH client requires the private key file directly."
        public_key_success=false
    fi

    # ─────────────────────────────────────────────────────────────────────────
    # 5. FINAL SUMMARY & REPORTING
    # ─────────────────────────────────────────────────────────────────────────
    print_step "5" "Setup Summary Report"
    
    echo -e "   ${BG_DARK}                                                                          ${NC}"
    echo -e "   ${BG_DARK}  ${BOLD}${FG_PURPLE}SUMMARY DETAIL:${NC}                                                         ${BG_DARK}  ${NC}"
    echo -e "   ${BG_DARK}  • Target Host:      ${FG_CYAN}$hostname${NC}${BG_DARK}                                            ${BG_DARK}  ${NC}"
    echo -e "   ${BG_DARK}  • Target User:      ${FG_CYAN}$username${NC}${BG_DARK}                                            ${BG_DARK}  ${NC}"
    echo -e "   ${BG_DARK}  • Port:             ${FG_CYAN}$port${NC}${BG_DARK}                                                ${BG_DARK}  ${NC}"
    echo -e "   ${BG_DARK}  • Generated Key:    ${FG_CYAN}$key_path${NC}${BG_DARK}                                    ${BG_DARK}  ${NC}"
    
    if [[ "$private_key_success" = true ]]; then
        echo -e "   ${BG_DARK}  • Private Auth:     ${FG_GREEN}PASSED${NC}${BG_DARK}                                              ${BG_DARK}  ${NC}"
    else
        echo -e "   ${BG_DARK}  • Private Auth:     ${FG_RED}FAILED${NC}${BG_DARK}                                              ${BG_DARK}  ${NC}"
    fi

    if [[ "$public_key_success" = true ]]; then
        echo -e "   ${BG_DARK}  • Public Auth:      ${FG_GREEN}PASSED${NC}${BG_DARK}                                              ${BG_DARK}  ${NC}"
    else
        echo -e "   ${BG_DARK}  • Public Auth:      ${FG_YELLOW}SKIPPED/UNSUPPORTED (Requires Private Key)${NC}${BG_DARK}              ${BG_DARK}  ${NC}"
    fi
    echo -e "   ${BG_DARK}                                                                          ${NC}"
    echo

    if [[ "$private_key_success" = true ]]; then
        echo -e "   ${BOLD}${FG_GREEN}🎉 All setup tasks completed successfully!${NC}"
        echo -e "   To log in to the host without password prompts, execute:"
        echo -e "     ${BOLD}${FG_CYAN}ssh -i \"$key_path\" -p \"$port\" \"$username@$hostname\"${NC}\n"
    else
        echo -e "   ${BOLD}${FG_RED}⚠️ Warning: Setup completed but validation failed.${NC}"
        echo -e "   Possible causes:"
        echo -e "     1. Remote server's SSH service config has 'PubkeyAuthentication no'."
        echo -e "     2. Remote user's home folder or ~/.ssh permissions are loose."
        echo -e "   Verify configuration in remote /etc/ssh/sshd_config."
    fi
}

# Helper to deploy SSH public key using basic shell pipes
fallback_install() {
    local pub_path="$1"
    local p_port="$2"
    local r_user="$3"
    local r_host="$4"

    log_verbose "Copying public key content..."
    # The pipeline does the following:
    # 1. Reads the local public key file.
    # 2. Connects via SSH (requiring password authentication).
    # 3. Creates the ~/.ssh directory if not existing.
    # 4. Sets remote directory permissions to 700 (owner access only).
    # 5. Appends the public key to authorized_keys.
    # 6. Sets authorized_keys file permissions to 600 (owner read/write only).
    # 7. Exits.
    log_command "cat \"$pub_path\" | ssh -p \"$p_port\" \"$r_user@$r_host\" \"mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\""
    
    if cat "$pub_path" | ssh -p "$p_port" "$r_user@$r_host" "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"; then
        echo -e "   ${STATUS_SUCCESS} public key successfully added to remote authorized_keys."
    else
        echo -e "   ${STATUS_ERROR} Fallback deployment failed. Please verify credentials."
        exit 1
    fi
}

# Run the script main entry
main "$@"
