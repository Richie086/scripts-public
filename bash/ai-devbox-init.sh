#!/bin/bash

# ==============================================================================
# Modern AI Development Environment Setup Script
# Powered by 'gum' for a beautiful, colorful CLI experience.
# ==============================================================================

set -e

DRY_RUN=0
RUN_MODE=0

show_help() {
    cat <<'EOF'
Usage: ./ai-devbox-init.sh [OPTION]

Options:
  -h, --help      Show this help message and exit
  -n, --dry-run   Show what would be installed without making changes
  -r, --run       Run the interactive installer

Behavior:
  If no flags are provided, this help is shown by default.
  --run and --dry-run are mutually exclusive.

Examples:
  ./ai-devbox-init.sh --help
  ./ai-devbox-init.sh --dry-run
  ./ai-devbox-init.sh --run
EOF
}

if [ "$#" -eq 0 ]; then
    show_help
    exit 0
fi

for arg in "$@"; do
    case "$arg" in
        --dry-run|-n)
            DRY_RUN=1
            ;;
        --run|-r)
            RUN_MODE=1
            ;;
        --help|-h|help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            show_help
            exit 1
            ;;
    esac
done

if [ "$DRY_RUN" -eq 1 ] && [ "$RUN_MODE" -eq 1 ]; then
    echo "Cannot use --run and --dry-run together."
    show_help
    exit 1
fi

if [ "$DRY_RUN" -eq 0 ] && [ "$RUN_MODE" -eq 0 ]; then
    show_help
    exit 0
fi

# 0. Request Sudo and Keep-Alive
# ------------------------------------------------------------------------------
if [ "$DRY_RUN" -eq 0 ]; then
    echo "🔒 Requesting administrative privileges for installation..."
    sudo -v
    while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
else
    echo "🧪 Dry-run mode enabled. No system changes will be made."
fi

# 1. Bootstrap 'gum' (The UI Engine)
# ------------------------------------------------------------------------------
if ! command -v gum &> /dev/null; then
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "gum is required for interactive dry-run mode. Install gum or run without --dry-run."
        exit 1
    fi
    echo "✨ Bootstrapping 'gum' for a modern UI experience..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://repo.charm.sh/apt/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/charm.gpg --yes
    echo "deb [signed-by=/etc/apt/keyrings/charm.gpg] https://repo.charm.sh/apt/ * *" | sudo tee /etc/apt/sources.list.d/charm.list > /dev/null
    sudo apt-get update -yq && sudo apt-get install -yq gum
fi

clear

# 2. Welcome Banner
# ------------------------------------------------------------------------------
gum style \
    --foreground 212 --border-foreground 212 --border double \
    --align center --width 60 --margin "1 2" --padding "1 2" \
    "🚀 AI Development Environment Installer" "Modern • Colorful • Automated" \
    "$( [ "$DRY_RUN" -eq 1 ] && echo "Mode: DRY RUN" || echo "Mode: LIVE")"

# 3. Interactive Selections
# ------------------------------------------------------------------------------
gum style --foreground 99 "Select your target environment:"
MODE_SELECT=$(gum choose "🖥️  Desktop GUI (Supports IDEs)" "💻 Headless CLI (Server)")

if [[ "$MODE_SELECT" == *"Desktop"* ]]; then
    MODE="gui"
else
    MODE="cli"
fi

gum style --foreground 99 "Space to toggle, Enter to confirm core tools:"
CORE_TOOLS=$(gum choose --no-limit --selected "git","docker","python" "git" "gh_cli" "docker" "python" "nodejs")

gum style --foreground 99 "Space to toggle modern CLI & AI extras:"
EXTRAS=$(gum choose --no-limit --selected "ollama","jq_yq","btop" "ollama (Local AI Runner)" "jq_yq (JSON/YAML Parsers)" "btop (Modern Resource Monitor)" "bat (Modern cat clone)" "fzf (Fuzzy Finder)")

if [ "$MODE" = "cli" ]; then
    gum style --foreground 99 "Space to toggle productivity tools (CLI defaults):"
    PRODUCTIVITY_TOOLS=$(gum choose --no-limit --selected "ripgrep","httpie","sqlite3","postgresql_client","direnv" "ripgrep" "httpie" "sqlite3" "postgresql_client" "direnv")
else
    gum style --foreground 99 "Space to toggle productivity tools (GUI defaults):"
    PRODUCTIVITY_TOOLS=$(gum choose --no-limit --selected "ripgrep","httpie" "ripgrep" "httpie" "sqlite3" "postgresql_client" "direnv")
fi

gum style --foreground 99 "Space to toggle TUI tools:"
TUI_TOOLS=$(gum choose --no-limit --selected "lazygit","eza","fd","tldr" "lazygit" "eza" "fd" "delta" "tldr" "neovim")

if [ "$MODE" = "gui" ]; then
    gum style --foreground 214 "GUI heavy packages are optional and can be large downloads."
    gum style --foreground 99 "Space to toggle GUI tools:"
    GUI_TOOLS=$(gum choose --no-limit "dbeaver_ce (~400MB)" "remmina" "alacritty" "kitty" "inkscape (~120MB)" "gimp (~150MB)")
fi

if [ "$MODE" = "gui" ]; then
    gum style --foreground 99 "Select your IDEs:"
    IDES=$(gum choose --no-limit --selected "cursor" "vscode" "cursor" "antigravity")
fi

# Confirm
gum confirm "Ready to build your environment?" || exit 0
clear

# Helper function for colorful section headers
print_header() {
    gum style --foreground 212 --bold --margin "1 0" "➔ $1"
}

print_dry_run_cmd() {
    gum style --foreground 214 "[dry-run] $1"
}

ensure_line_in_file() {
    local line="$1"
    local file="$2"

    if [ ! -f "$file" ]; then
        touch "$file"
    fi

    if ! grep -Fqx "$line" "$file"; then
        echo "$line" >> "$file"
    fi
}

prompt_and_add_alias() {
    local line="$1"
    local label="$2"

    if gum confirm "Add alias for $label?"; then
        ensure_line_in_file "$line" "$HOME/.bashrc"
    fi
}

install_apt_or_fallback() {
    local apt_package="$1"
    local fallback_desc="$2"
    local fallback_cmd="$3"

    if ! sudo apt-get install -y "$apt_package"; then
        gum style --foreground 214 "Apt install failed for $apt_package. Trying fallback: $fallback_desc"
        eval "$fallback_cmd"
    fi
}

if [ "$DRY_RUN" -eq 1 ]; then
    print_header "Dry Run Plan"
    print_dry_run_cmd "sudo apt-get update && sudo apt-get upgrade -y"
    print_dry_run_cmd "sudo apt-get install -y build-essential curl wget software-properties-common apt-transport-https ca-certificates gnupg lsb-release tmux${MODE:+$( [ "$MODE" = "gui" ] && echo " libfuse2 libx11-xcb1 libxss1 libasound2 libgbm1" )}"

    if [[ $CORE_TOOLS == *"git"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y git"
    fi
    if [[ $CORE_TOOLS == *"gh_cli"* ]]; then
        print_dry_run_cmd "Add GitHub CLI apt repo and install gh"
    fi
    if [[ $CORE_TOOLS == *"docker"* ]]; then
        print_dry_run_cmd "Add Docker apt repo, install docker-ce stack, and add $USER to docker group"
    fi
    if [[ $CORE_TOOLS == *"nodejs"* ]]; then
        print_dry_run_cmd "Run NodeSource setup_20.x and install nodejs"
    fi
    if [[ $CORE_TOOLS == *"python"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y python3 python3-pip python3-venv python3-dev"
    fi

    if [[ $EXTRAS == *"ollama"* ]]; then
        print_dry_run_cmd "curl -fsSL https://ollama.com/install.sh | sh"
    fi
    if [[ $EXTRAS == *"jq_yq"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y jq && download yq to /usr/local/bin/yq"
    fi
    if [[ $EXTRAS == *"btop"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y btop"
    fi
    if [[ $EXTRAS == *"bat"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y bat && link ~/.local/bin/bat -> /usr/bin/batcat"
    fi
    if [[ $EXTRAS == *"fzf"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y fzf"
    fi

    if [[ $PRODUCTIVITY_TOOLS == *"ripgrep"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y ripgrep"
    fi
    if [[ $PRODUCTIVITY_TOOLS == *"httpie"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y httpie"
    fi
    if [[ $PRODUCTIVITY_TOOLS == *"sqlite3"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y sqlite3"
    fi
    if [[ $PRODUCTIVITY_TOOLS == *"postgresql_client"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y postgresql-client"
    fi
    if [[ $PRODUCTIVITY_TOOLS == *"direnv"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y direnv and add direnv hook to ~/.bashrc"
    fi

    if [[ $TUI_TOOLS == *"lazygit"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y lazygit (fallback to upstream binary if apt unavailable)"
    fi
    if [[ $TUI_TOOLS == *"eza"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y eza (fallback to upstream binary if apt unavailable)"
        print_dry_run_cmd "Prompt for alias: ls='eza --group-directories-first --icons=auto'"
    fi
    if [[ $TUI_TOOLS == *"fd"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y fd-find"
        print_dry_run_cmd "Prompt for alias: fd=fdfind"
    fi
    if [[ $TUI_TOOLS == *"delta"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y git-delta"
    fi
    if [[ $TUI_TOOLS == *"tldr"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y tldr (fallback to tealdeer)"
    fi
    if [[ $TUI_TOOLS == *"neovim"* ]]; then
        print_dry_run_cmd "sudo apt-get install -y neovim"
    fi

    if [ "$MODE" = "gui" ]; then
        if [[ $GUI_TOOLS == *"dbeaver_ce"* ]]; then
            print_dry_run_cmd "Install dbeaver-ce (~400MB)"
        fi
        if [[ $GUI_TOOLS == *"remmina"* ]]; then
            print_dry_run_cmd "Install remmina and RDP/VNC plugins"
        fi
        if [[ $GUI_TOOLS == *"alacritty"* ]]; then
            print_dry_run_cmd "Install alacritty"
        fi
        if [[ $GUI_TOOLS == *"kitty"* ]]; then
            print_dry_run_cmd "Install kitty"
        fi
        if [[ $GUI_TOOLS == *"inkscape"* ]]; then
            print_dry_run_cmd "Install inkscape (~120MB)"
        fi
        if [[ $GUI_TOOLS == *"gimp"* ]]; then
            print_dry_run_cmd "Install gimp (~150MB)"
        fi
    fi

    if [ "$MODE" = "gui" ]; then
        if [[ $IDES == *"vscode"* ]]; then
            print_dry_run_cmd "Add Microsoft apt repo and install code"
        fi
        if [[ $IDES == *"cursor"* ]]; then
            print_dry_run_cmd "Download Cursor AppImage, chmod +x, symlink /usr/local/bin/cursor, create desktop entry"
        fi
        if [[ $IDES == *"antigravity"* ]]; then
            print_dry_run_cmd "Download and extract Antigravity IDE tarball from edgedl.me.gvt1.com, symlink /usr/local/bin/antigravity-ide, create desktop entry"
        fi
    fi

    if [[ $CORE_TOOLS == *"python"* ]]; then
        print_dry_run_cmd "Create ~/ai_dev_env venv and pip install AI/data packages$( [ "$MODE" = "gui" ] && echo ", including jupyterlab" )"
    fi

    print_header "Dry Run Complete"
    gum style --foreground 82 "No commands were executed."
    exit 0
fi

# 4. Execution Engine
# ------------------------------------------------------------------------------
print_header "Updating System & Installing Base Utilities..."
sudo apt-get update && sudo apt-get upgrade -y
BASE_PKGS="build-essential curl wget software-properties-common apt-transport-https ca-certificates gnupg lsb-release tmux"

if [ "$MODE" = "gui" ]; then
    BASE_PKGS="$BASE_PKGS libfuse2 libx11-xcb1 libxss1 libasound2 libgbm1"
fi
sudo apt-get install -y $BASE_PKGS

# Core Tools
# ------------------------------------------------------------------------------
if [[ $CORE_TOOLS == *"git"* ]]; then
    print_header "Installing Git..."
    sudo apt-get install -y git
fi

if [[ $CORE_TOOLS == *"gh_cli"* ]]; then
    print_header "Installing GitHub CLI..."
    sudo mkdir -p -m 755 /etc/apt/keyrings
    wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
    sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update && sudo apt-get install -y gh
fi

if [[ $CORE_TOOLS == *"docker"* ]]; then
    print_header "Installing Docker CE..."
    sudo mkdir -m 0755 -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    if ! getent group docker | grep -qw "$USER"; then
        sudo usermod -aG docker "$USER"
    fi
fi

if [[ $CORE_TOOLS == *"nodejs"* ]]; then
    print_header "Installing Node.js & npm..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

if [[ $CORE_TOOLS == *"python"* ]]; then
    print_header "Installing Python 3 & venv..."
    sudo apt-get install -y python3 python3-pip python3-venv python3-dev
fi

# Modern Extras
# ------------------------------------------------------------------------------
if [[ $EXTRAS == *"ollama"* ]]; then
    print_header "Installing Ollama (Local AI Runner)..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

if [[ $EXTRAS == *"jq_yq"* ]]; then
    print_header "Installing jq..."
    sudo apt-get install -y jq
    # yq is best installed via wget for the latest release
    sudo wget -qO /usr/local/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
    sudo chmod a+x /usr/local/bin/yq
fi

if [[ $EXTRAS == *"btop"* ]]; then
    print_header "Installing btop..."
    sudo apt-get install -y btop
fi

if [[ $EXTRAS == *"bat"* ]]; then
    print_header "Installing bat..."
    sudo apt-get install -y bat
    # Ubuntu installs bat as 'batcat' due to name conflicts, so we alias it
    mkdir -p ~/.local/bin
    ln -sf /usr/bin/batcat ~/.local/bin/bat
fi

if [[ $EXTRAS == *"fzf"* ]]; then
    print_header "Installing fzf..."
    sudo apt-get install -y fzf
fi

# Productivity Tools
# ------------------------------------------------------------------------------
if [[ $PRODUCTIVITY_TOOLS == *"ripgrep"* ]]; then
    print_header "Installing ripgrep..."
    sudo apt-get install -y ripgrep
fi

if [[ $PRODUCTIVITY_TOOLS == *"httpie"* ]]; then
    print_header "Installing httpie..."
    sudo apt-get install -y httpie
fi

if [[ $PRODUCTIVITY_TOOLS == *"sqlite3"* ]]; then
    print_header "Installing sqlite3..."
    sudo apt-get install -y sqlite3
fi

if [[ $PRODUCTIVITY_TOOLS == *"postgresql_client"* ]]; then
    print_header "Installing PostgreSQL client..."
    sudo apt-get install -y postgresql-client
fi

if [[ $PRODUCTIVITY_TOOLS == *"direnv"* ]]; then
    print_header "Installing direnv..."
    sudo apt-get install -y direnv
    ensure_line_in_file 'eval "$(direnv hook bash)"' "$HOME/.bashrc"
fi

# TUI Tools
# ------------------------------------------------------------------------------
if [[ $TUI_TOOLS == *"lazygit"* ]]; then
    print_header "Installing lazygit..."
    install_apt_or_fallback "lazygit" "GitHub release binary" "set -e; LG_URL=$(curl -fsSL https://api.github.com/repos/jesseduffield/lazygit/releases/latest | grep -Po 'https://[^\" ]*Linux_x86_64\.tar\.gz' | head -n 1); tmpd=$(mktemp -d); curl -fL \"$LG_URL\" -o \"$tmpd/lazygit.tar.gz\"; tar -xzf \"$tmpd/lazygit.tar.gz\" -C \"$tmpd\" lazygit; sudo install \"$tmpd/lazygit\" /usr/local/bin/lazygit; rm -rf \"$tmpd\""
fi

if [[ $TUI_TOOLS == *"eza"* ]]; then
    print_header "Installing eza..."
    install_apt_or_fallback "eza" "GitHub release binary" "set -e; EZA_URL=$(curl -fsSL https://api.github.com/repos/eza-community/eza/releases/latest | grep -Po 'https://[^\" ]*x86_64-unknown-linux-gnu\.tar\.gz' | head -n 1); tmpd=$(mktemp -d); curl -fL \"$EZA_URL\" -o \"$tmpd/eza.tar.gz\"; tar -xzf \"$tmpd/eza.tar.gz\" -C \"$tmpd\"; sudo install \"$tmpd/eza\" /usr/local/bin/eza; rm -rf \"$tmpd\""
    prompt_and_add_alias "alias ls='eza --group-directories-first --icons=auto'" "ls -> eza"
fi

if [[ $TUI_TOOLS == *"fd"* ]]; then
    print_header "Installing fd-find..."
    sudo apt-get install -y fd-find
    prompt_and_add_alias "alias fd='fdfind'" "fd -> fdfind"
fi

if [[ $TUI_TOOLS == *"delta"* ]]; then
    print_header "Installing git-delta..."
    sudo apt-get install -y git-delta
fi

if [[ $TUI_TOOLS == *"tldr"* ]]; then
    print_header "Installing tldr pages..."
    install_apt_or_fallback "tldr" "tealdeer package" "sudo apt-get install -y tealdeer"
fi

if [[ $TUI_TOOLS == *"neovim"* ]]; then
    print_header "Installing Neovim..."
    sudo apt-get install -y neovim
fi

# GUI Tools
# ------------------------------------------------------------------------------
if [ "$MODE" = "gui" ]; then
    if [[ $GUI_TOOLS == *"dbeaver_ce"* ]]; then
        gum style --foreground 214 "Installing dbeaver-ce (~400MB)."
        print_header "Installing DBeaver Community..."
        sudo apt-get install -y dbeaver-ce
    fi

    if [[ $GUI_TOOLS == *"remmina"* ]]; then
        print_header "Installing Remmina..."
        sudo apt-get install -y remmina remmina-plugin-rdp remmina-plugin-vnc
    fi

    if [[ $GUI_TOOLS == *"alacritty"* ]]; then
        print_header "Installing Alacritty..."
        sudo apt-get install -y alacritty
    fi

    if [[ $GUI_TOOLS == *"kitty"* ]]; then
        print_header "Installing Kitty..."
        sudo apt-get install -y kitty
    fi

    if [[ $GUI_TOOLS == *"inkscape"* ]]; then
        gum style --foreground 214 "Installing inkscape (~120MB)."
        print_header "Installing Inkscape..."
        sudo apt-get install -y inkscape
    fi

    if [[ $GUI_TOOLS == *"gimp"* ]]; then
        gum style --foreground 214 "Installing gimp (~150MB)."
        print_header "Installing GIMP..."
        sudo apt-get install -y gimp
    fi
fi

# IDEs
# ------------------------------------------------------------------------------
if [ "$MODE" = "gui" ]; then
    if [[ $IDES == *"vscode"* ]]; then
        print_header "Installing Visual Studio Code..."
        wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
        sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
        echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
        rm -f packages.microsoft.gpg
        sudo apt-get update && sudo apt-get install -y code
    fi

    if [[ $IDES == *"cursor"* ]]; then
        print_header "Installing Cursor..."
        mkdir -p "$HOME/Applications" "$HOME/.local/share/applications"
        CURSOR_APPIMAGE="$HOME/Applications/cursor.AppImage"
        curl -fL "https://downloader.cursor.sh/linux/appImage/x64" -o "$CURSOR_APPIMAGE"
        chmod +x "$CURSOR_APPIMAGE"
        sudo ln -sf "$CURSOR_APPIMAGE" /usr/local/bin/cursor
        cat <<EOF > "$HOME/.local/share/applications/cursor.desktop"
[Desktop Entry]
Name=Cursor
Exec=$CURSOR_APPIMAGE --no-sandbox
Icon=code
Type=Application
Categories=Development;IDE;
EOF
    fi

    if [[ $IDES == *"antigravity"* ]]; then
        print_header "Installing Antigravity IDE..."
        ANTIGRAVITY_IDE_URL="https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/2.1.1-6123990880747520/linux-x64/Antigravity%2520IDE.tar.gz"
        ANTIGRAVITY_TAR="$(mktemp /tmp/antigravity-ide.XXXXXX.tar.gz)"
        ANTIGRAVITY_TMP_DIR="$(mktemp -d /tmp/antigravity-ide.XXXXXX)"
        ANTIGRAVITY_INSTALL_DIR="$HOME/Applications/antigravity-ide"

        mkdir -p "$HOME/Applications" "$HOME/.local/share/applications"
        curl -fL "$ANTIGRAVITY_IDE_URL" -o "$ANTIGRAVITY_TAR"
        tar -xzf "$ANTIGRAVITY_TAR" -C "$ANTIGRAVITY_TMP_DIR"

        rm -rf "$ANTIGRAVITY_INSTALL_DIR"
        mkdir -p "$ANTIGRAVITY_INSTALL_DIR"
        mv "$ANTIGRAVITY_TMP_DIR"/* "$ANTIGRAVITY_INSTALL_DIR"/

        ANTIGRAVITY_BIN=$(find "$ANTIGRAVITY_INSTALL_DIR" -maxdepth 3 -type f -perm -u+x \( -iname "*antigravity*" -o -iname "*ide*" \) | head -n 1)
        if [ -z "$ANTIGRAVITY_BIN" ]; then
            ANTIGRAVITY_BIN=$(find "$ANTIGRAVITY_INSTALL_DIR" -maxdepth 3 -type f -perm -u+x | head -n 1)
        fi

        if [ -n "$ANTIGRAVITY_BIN" ]; then
            sudo ln -sf "$ANTIGRAVITY_BIN" /usr/local/bin/antigravity-ide
            cat <<EOF > "$HOME/.local/share/applications/antigravity-ide.desktop"
[Desktop Entry]
Name=Antigravity IDE
Exec=$ANTIGRAVITY_BIN
Icon=applications-development
Type=Application
Categories=Development;IDE;
EOF
        else
            gum style --foreground 196 "Antigravity IDE downloaded but no executable was found."
        fi

        rm -f "$ANTIGRAVITY_TAR"
        rm -rf "$ANTIGRAVITY_TMP_DIR"
    fi
fi

# AI Python Environment Configuration
# ------------------------------------------------------------------------------
if [[ $CORE_TOOLS == *"python"* ]]; then
    print_header "Configuring Python AI Environment..."
    AI_ENV_DIR="$HOME/ai_dev_env"
    
    if [ ! -d "$AI_ENV_DIR" ]; then
        python3 -m venv "$AI_ENV_DIR"
    fi

    bash -c "
        source $AI_ENV_DIR/bin/activate
        pip install --upgrade pip
        pip install openai anthropic google-generativeai langchain huggingface_hub requests python-dotenv pandas numpy
        if [ '$MODE' = 'gui' ]; then
            pip install jupyterlab
        fi
    "
fi

print_header "Installed Tool Check"
if [[ $PRODUCTIVITY_TOOLS == *"ripgrep"* ]]; then
    command -v rg >/dev/null 2>&1 && gum style --foreground 82 "$(rg --version | head -n 1)" || gum style --foreground 214 "ripgrep not found in PATH"
fi
if [[ $PRODUCTIVITY_TOOLS == *"httpie"* ]]; then
    command -v http >/dev/null 2>&1 && gum style --foreground 82 "$(http --version | head -n 1)" || gum style --foreground 214 "httpie not found in PATH"
fi
if [[ $PRODUCTIVITY_TOOLS == *"sqlite3"* ]]; then
    command -v sqlite3 >/dev/null 2>&1 && gum style --foreground 82 "$(sqlite3 --version | awk '{print "sqlite3 " $1}')" || gum style --foreground 214 "sqlite3 not found in PATH"
fi
if [[ $PRODUCTIVITY_TOOLS == *"postgresql_client"* ]]; then
    command -v psql >/dev/null 2>&1 && gum style --foreground 82 "$(psql --version)" || gum style --foreground 214 "psql not found in PATH"
fi
if [[ $PRODUCTIVITY_TOOLS == *"direnv"* ]]; then
    command -v direnv >/dev/null 2>&1 && gum style --foreground 82 "$(direnv version)" || gum style --foreground 214 "direnv not found in PATH"
fi
if [[ $TUI_TOOLS == *"lazygit"* ]]; then
    command -v lazygit >/dev/null 2>&1 && gum style --foreground 82 "lazygit $(lazygit --version | awk '{print $2}')" || gum style --foreground 214 "lazygit not found in PATH"
fi
if [[ $TUI_TOOLS == *"eza"* ]]; then
    command -v eza >/dev/null 2>&1 && gum style --foreground 82 "$(eza --version | head -n 1)" || gum style --foreground 214 "eza not found in PATH"
fi
if [[ $TUI_TOOLS == *"fd"* ]]; then
    command -v fdfind >/dev/null 2>&1 && gum style --foreground 82 "$(fdfind --version)" || gum style --foreground 214 "fdfind not found in PATH"
fi
if [[ $TUI_TOOLS == *"delta"* ]]; then
    command -v delta >/dev/null 2>&1 && gum style --foreground 82 "$(delta --version)" || gum style --foreground 214 "delta not found in PATH"
fi
if [[ $TUI_TOOLS == *"tldr"* ]]; then
    command -v tldr >/dev/null 2>&1 && gum style --foreground 82 "tldr available" || gum style --foreground 214 "tldr not found in PATH"
fi
if [[ $TUI_TOOLS == *"neovim"* ]]; then
    command -v nvim >/dev/null 2>&1 && gum style --foreground 82 "$(nvim --version | head -n 1)" || gum style --foreground 214 "nvim not found in PATH"
fi

# 5. Success Summary
# ------------------------------------------------------------------------------
clear
gum style \
    --foreground 82 --border-foreground 82 --border rounded \
    --align left --width 60 --margin "1 2" --padding "1 2" \
    "✅ Installation Complete!" "" \
    "Important Next Steps:" \
    "1. Close and reopen your terminal (or log out/in) to apply group permissions." \
    "2. Source your env: source ~/ai_dev_env/bin/activate" \
    "3. Try out your new tools: btop, fzf, or bat" \
    "4. If you installed Ollama, start with: ollama run llama3"
