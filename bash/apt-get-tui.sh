#!/usr/bin/env bash
#
# apt-get-tui.sh - A Text User Interface (TUI) for apt / apt-get on Ubuntu/Debian.
#
# Every common apt-get / apt-cache / apt-mark function is reachable from a menu.
# Package name fields for install/remove/etc. support TAB auto-completion:
# type the first few letters of a package name and press <TAB> to complete it
# (double-<TAB> lists all matches). Completion is powered by rlwrap.
#
# Usage:  ./apt-get-tui.sh
#
# Notes:
#   * Privileged actions (install, remove, update, ...) are run through sudo.
#   * TAB completion requires the 'rlwrap' package; the script offers to
#     install it automatically on first run if it is missing.

set -o pipefail

# --------------------------------------------------------------------------
# Colours / formatting
# --------------------------------------------------------------------------
# Selected colour theme: "light" (Catppuccin Latte) or "dark" (Ayu Dark).
# Overridable via the APT_TUI_THEME env var or the --dark / --light flags.
THEME="${APT_TUI_THEME:-light}"

# (Re)build all colour variables for the given theme. Colours are emitted as
# 24-bit truecolor escapes; when stdout is not a terminal everything is blank.
apply_theme() {
    THEME="$1"

    if [[ ! -t 1 ]]; then
        BOLD=""; UND=""; RESET=""; DIM=""
        RED=""; GREEN=""; YELLOW=""; CYAN=""
        ACCENT=""; HEADER=""; NUMCLR=""; LABEL=""
        return
    fi

    BOLD=$(tput bold); UND=$(tput smul); RESET=$(tput sgr0)
    tc() { printf '\033[38;2;%d;%d;%dm' "$1" "$2" "$3"; }

    case "$THEME" in
        dark)   # Ayu Dark - https://terminalcolors.com/images/colors/ayu-dark.svg
            LABEL=$(tc  191 189 182)  # #bfbdb6 foreground
            DIM=$(tc    104 104 104)  # #686868 muted
            RED=$(tc    240 113 120)  # #f07178
            GREEN=$(tc  170 217  76)  # #aad94c
            YELLOW=$(tc 255 180  84)  # #ffb454
            CYAN=$(tc   149 230 203)  # #95e6cb
            ACCENT=$(tc 230 180  80)  # #e6b450 signature accent (rules/banner)
            HEADER=$(tc 210 166 255)  # #d2a6ff section titles
            NUMCLR=$(tc  89 194 255)  # #59c2ff option numbers
            ;;
        *)      # Catppuccin Latte (light) - https://catppuccin.com/palette
            THEME="light"
            LABEL=$(tc   76  79 105)  # #4c4f69 text
            DIM=$(tc    108 111 133)  # #6c6f85 subtext
            RED=$(tc    210  15  57)  # #d20f39
            GREEN=$(tc   64 160  43)  # #40a02b
            YELLOW=$(tc 223 142  29)  # #df8e1d
            CYAN=$(tc     4 165 229)  # #04a5e5
            ACCENT=$(tc  30 102 245)  # #1e66f5 blue (rules/banner)
            HEADER=$(tc 136  57 239)  # #8839ef mauve section titles
            NUMCLR=$(tc 254 100  11)  # #fe640b peach option numbers
            ;;
    esac
    unset -f tc
}

apply_theme "$THEME"

# Temp directory for cached package name word-lists (used by TAB completion).
WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/apt-get-tui.XXXXXX")"
ALL_PKGS_WL="$WORKDIR/all_pkgs.wl"
INSTALLED_WL="$WORKDIR/installed.wl"
HELD_WL="$WORKDIR/held.wl"

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
info()  { echo "${CYAN}$*${RESET}"; }
ok()    { echo "${GREEN}$*${RESET}"; }
warn()  { echo "${YELLOW}$*${RESET}"; }
err()   { echo "${RED}$*${RESET}" >&2; }

pause() {
    echo
    read -r -p "Press <Enter> to return to the menu... " _ || true
}

# Ensure rlwrap is available (needed for TAB completion). Offer to install it.
ensure_rlwrap() {
    if command -v rlwrap >/dev/null 2>&1; then
        return 0
    fi
    warn "The 'rlwrap' package is required for TAB auto-completion but is not installed."
    read -r -p "Install it now with 'sudo apt-get install rlwrap'? [Y/n] " ans
    case "$ans" in
        ""|[Yy]*)
            sudo apt-get update && sudo apt-get install -y rlwrap
            ;;
        *)
            warn "Continuing without TAB completion (plain line editing only)."
            ;;
    esac
}

# Build / refresh the word-list of every known package name (for install etc.).
build_all_pkgs_wl() {
    if [[ ! -s "$ALL_PKGS_WL" ]]; then
        apt-cache pkgnames 2>/dev/null | sort -u > "$ALL_PKGS_WL"
    fi
}

# Build / refresh the word-list of currently installed packages (remove etc.).
build_installed_wl() {
    dpkg-query -W -f='${Package}\n' 2>/dev/null | sort -u > "$INSTALLED_WL"
}

# Build / refresh the word-list of held packages (unhold).
build_held_wl() {
    apt-mark showhold 2>/dev/null | sort -u > "$HELD_WL"
}

# Read a (possibly space-separated) list of package names WITH tab completion.
#   $1 = prompt text
#   $2 = path to the word-list file to complete against
# Result is placed in the global REPLY variable.
read_pkgs() {
    local prompt="$1" wordlist="$2"
    REPLY=""
    if [[ -t 0 ]] && command -v rlwrap >/dev/null 2>&1 && [[ -s "$wordlist" ]]; then
        # rlwrap gives readline editing + TAB completion against the word-list.
        # 'head -n 1' returns a single edited line then exits.
        REPLY=$(rlwrap -C apt-get-tui -f "$wordlist" -S "$prompt" head -n 1)
    else
        # Fallback (e.g. no rlwrap, or piped input): plain readline line edit.
        read -e -r -p "$prompt" REPLY
    fi
}

# Read a single free-text line (no package completion).
read_line() {
    local prompt="$1"
    REPLY=""
    read -r -p "$prompt" REPLY
}

# Run a command, echoing it first so the user sees exactly what happened.
run() {
    echo "${BOLD}\$ $*${RESET}"
    "$@"
}

# --------------------------------------------------------------------------
# apt actions
# --------------------------------------------------------------------------
do_search() {
    read_line "Enter a search term (name / keyword): "
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    run apt-cache search -- "$REPLY"
}

do_show() {
    build_all_pkgs_wl
    read_pkgs "Package to show: " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run apt show $REPLY
}

do_install() {
    ensure_rlwrap
    build_all_pkgs_wl
    read_pkgs "Package(s) to install (TAB to complete): " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-get install $REPLY
}

do_reinstall() {
    ensure_rlwrap
    build_installed_wl
    read_pkgs "Package(s) to reinstall (TAB to complete): " "$INSTALLED_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-get install --reinstall $REPLY
}

do_remove() {
    ensure_rlwrap
    build_installed_wl
    read_pkgs "Package(s) to remove (TAB to complete): " "$INSTALLED_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-get remove $REPLY
}

do_purge() {
    ensure_rlwrap
    build_installed_wl
    read_pkgs "Package(s) to purge (config + files) (TAB to complete): " "$INSTALLED_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-get purge $REPLY
}

do_update()      { run sudo apt-get update; }
do_upgrade()     { run sudo apt-get upgrade; }
do_full_upgrade(){ run sudo apt-get full-upgrade; }
do_autoremove()  { run sudo apt-get autoremove; }

do_clean() {
    echo "1) clean      (remove ALL downloaded .deb files from the cache)"
    echo "2) autoclean  (remove only obsolete .deb files)"
    read_line "Choose [1/2]: "
    case "$REPLY" in
        1) run sudo apt-get clean ;;
        2) run sudo apt-get autoclean ;;
        *) warn "Cancelled." ;;
    esac
}

do_list_installed()  { run apt list --installed; }
do_list_upgradable() { run apt list --upgradable; }

do_depends() {
    build_all_pkgs_wl
    read_pkgs "Package to show dependencies of: " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run apt-cache depends $REPLY
}

do_rdepends() {
    build_all_pkgs_wl
    read_pkgs "Package to show reverse-dependencies of: " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run apt-cache rdepends $REPLY
}

do_policy() {
    build_all_pkgs_wl
    read_pkgs "Package to show versions/policy for: " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run apt-cache policy $REPLY
}

do_download() {
    build_all_pkgs_wl
    read_pkgs "Package(s) to download (.deb only, no install): " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    info "Downloading into: $(pwd)"
    # shellcheck disable=SC2086
    run apt-get download $REPLY
}

do_source() {
    build_all_pkgs_wl
    read_pkgs "Package to fetch source for: " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run apt-get source $REPLY
}

do_build_dep() {
    build_all_pkgs_wl
    read_pkgs "Package to install build dependencies for: " "$ALL_PKGS_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-get build-dep $REPLY
}

do_fix_broken() { run sudo apt-get install --fix-broken; }
do_check()      { run sudo apt-get check; }

do_hold() {
    build_installed_wl
    read_pkgs "Package(s) to HOLD (freeze at current version): " "$INSTALLED_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-mark hold $REPLY
}

do_unhold() {
    build_held_wl
    read_pkgs "Package(s) to UNHOLD: " "$HELD_WL"
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-mark unhold $REPLY
}

do_showhold()  { run apt-mark showhold; }

do_add_repo() {
    read_line "Repository / PPA to add (e.g. 'ppa:user/ppa'): "
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    run sudo add-apt-repository "$REPLY"
}

# Configure an apt proxy by writing /etc/apt/apt.conf.d/99proxy.
do_proxy() {
    local conf="/etc/apt/apt.conf.d/99proxy"
    info "Configure an apt proxy server (written to $conf)."
    [[ -f "$conf" ]] && warn "Note: $conf already exists and will be overwritten."

    # Default is YES for both protocols (empty answer counts as yes).
    local do_http=true do_https=true
    read_line "Proxy HTTP traffic?  [Y/n]: "
    case "$REPLY" in [Nn]*) do_http=false ;; esac
    read_line "Proxy HTTPS traffic? [Y/n]: "
    case "$REPLY" in [Nn]*) do_https=false ;; esac

    if ! $do_http && ! $do_https; then
        warn "Neither HTTP nor HTTPS selected - nothing to do."
        return
    fi

    read_line "Proxy server address (host or IP, no scheme): "
    local addr="$REPLY"
    [[ -z "$addr" ]] && { warn "No proxy address entered."; return; }
    # Tolerate a pasted scheme / trailing slash.
    addr="${addr#http://}"; addr="${addr#https://}"; addr="${addr%/}"

    read_line "Proxy port: "
    local port="$REPLY"
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        err "Port must be a number."
        return
    fi

    # Both protocols are proxied through the same http:// endpoint.
    local content=""
    $do_http  && content+="Acquire::http::Proxy \"http://${addr}:${port}/\";"$'\n'
    $do_https && content+="Acquire::https::Proxy \"http://${addr}:${port}/\";"$'\n'

    echo
    info "The following will be written to $conf:"
    echo "${BOLD}${content}${RESET}"
    read_line "Write this configuration? [Y/n]: "
    case "$REPLY" in [Nn]*) warn "Cancelled - no changes made."; return ;; esac

    if printf '%s' "$content" | sudo tee "$conf" >/dev/null; then
        ok "Proxy configuration written to $conf"
        info "apt will now use this proxy. (Delete the file to disable it.)"
    else
        err "Failed to write $conf"
    fi
}

do_toggle_theme() {
    if [[ "$THEME" == "dark" ]]; then
        apply_theme light
    else
        apply_theme dark
    fi
    ok "Theme switched to: ${THEME} (Catppuccin Latte / Ayu Dark)"
}

do_raw() {
    warn "Advanced: type any apt-get arguments (they are appended to 'sudo apt-get')."
    read_line "sudo apt-get "
    [[ -z "$REPLY" ]] && { warn "Nothing entered."; return; }
    # shellcheck disable=SC2086
    run sudo apt-get $REPLY
}

# --------------------------------------------------------------------------
# Menu
# --------------------------------------------------------------------------
# Column width (visible characters) for each section column.
MENU_CW=22

# Print one right-padded menu cell with a colourised number, e.g. "12) Remove".
# Padding is based on VISIBLE width so ANSI colour codes never break alignment.
#   $1 = "num|Label"  (empty string -> a blank cell)
emit_cell() {
    local token="$1"
    if [[ -z "$token" ]]; then
        printf '%*s' "$MENU_CW" ""
        return
    fi
    local num="${token%%|*}" label="${token#*|}"
    local vis="${num}) ${label}"
    local pad=$(( MENU_CW - ${#vis} ))
    (( pad < 0 )) && pad=0
    printf '%s%s)%s %s%s%s%*s' "${BOLD}${NUMCLR}" "$num" "${RESET}" \
        "${LABEL}" "$label" "${RESET}" "$pad" ""
}

# Print one section-title cell (coloured/underlined), padded to the column width.
emit_title() {
    local title="$1"
    local pad=$(( MENU_CW - ${#title} ))
    (( pad < 0 )) && pad=0
    printf '%s%s%s%*s' "${BOLD}${UND}${HEADER}" "$title" "${RESET}" "$pad" ""
}

# Render the menu as side-by-side VERTICAL columns: each section is its own
# column, with its options listed top-to-bottom underneath the section title.
print_menu() {
    clear 2>/dev/null || true

    local -a titles=( "Find / Inspect" "Install / Remove" "Maintenance" \
                      "Pinning / Sources" "Other" )

    # Section entries as "number|Proper-Case Label", listed vertically.
    local -a c1=( "1|Search Packages" "2|Show Details" "3|Dependencies" \
                  "4|Reverse Deps" "5|Versions / Policy" "6|List Installed" \
                  "7|List Upgradable" )
    local -a c2=( "8|Install" "9|Reinstall" "10|Remove" "11|Purge" \
                  "12|Download .deb" "13|Download Source" "14|Build Deps" )
    local -a c3=( "15|Update Lists" "16|Upgrade" "17|Full Upgrade" \
                  "18|Autoremove" "19|Clean Cache" "20|Fix Broken" \
                  "21|Check Deps" )
    local -a c4=( "22|Hold" "23|Unhold" "24|Show Held" "25|Add Repo / PPA" \
                  "26|Set Proxy" )
    local -a c5=( "80|Toggle Theme" "90|Raw apt-get Command" "0|Exit" )

    # Coloured horizontal rules sized to the full menu width.
    local bar; printf -v bar '%*s' $(( MENU_CW * 5 )) ''; bar=${bar// /─}

    echo
    printf '%s%s%s\n' "${ACCENT}" "$bar" "${RESET}"
    printf '   %s%sapt-get-tui%s  %s— a menu-driven front-end for apt%s   %s[theme: %s]%s\n' \
        "${BOLD}" "${ACCENT}" "${RESET}" "${DIM}" "${RESET}" "${DIM}" "${THEME}" "${RESET}"
    printf '%s%s%s\n' "${ACCENT}" "$bar" "${RESET}"

    # Section-title row.
    emit_title "${titles[0]}"; emit_title "${titles[1]}"; emit_title "${titles[2]}"
    emit_title "${titles[3]}"; emit_title "${titles[4]}"; echo

    # Work out how many rows the tallest column needs.
    local maxrows=0 n
    for n in "${#c1[@]}" "${#c2[@]}" "${#c3[@]}" "${#c4[@]}" "${#c5[@]}"; do
        (( n > maxrows )) && maxrows=$n
    done

    local r
    for (( r = 0; r < maxrows; r++ )); do
        emit_cell "${c1[r]:-}"; emit_cell "${c2[r]:-}"; emit_cell "${c3[r]:-}"
        emit_cell "${c4[r]:-}"; emit_cell "${c5[r]:-}"; echo
    done

    printf '%s%s%s\n' "${ACCENT}${DIM}" "$bar" "${RESET}"
    printf 'Tip: Install / Remove / Show / etc. fields support %s<TAB>%s auto-completion.\n' \
        "${BOLD}${GREEN}" "${RESET}"
    printf '%sCreated by Richard Troiano 2026 with Cursor.  See my blog @ %s%s%s%s\n' \
        "${DIM}" "${RESET}" "${ACCENT}${UND}" "extremesarcasm.org" "${RESET}"
}

main() {
    # Optional CLI flags: choose the colour theme up front.
    local arg
    for arg in "$@"; do
        case "$arg" in
            --dark)  apply_theme dark ;;
            --light) apply_theme light ;;
            -h|--help)
                echo "Usage: apt-get-tui.sh [--dark|--light]"
                echo "  --dark   use the Ayu Dark colour scheme"
                echo "  --light  use the Catppuccin Latte colour scheme (default)"
                echo "  (also honours APT_TUI_THEME=dark|light; toggle live from the menu)"
                exit 0 ;;
        esac
    done

    if ! command -v apt-get >/dev/null 2>&1; then
        err "apt-get not found. This tool is for Debian/Ubuntu systems."
        exit 1
    fi

    while true; do
        print_menu
        read_line "Choose an option: "
        choice="$REPLY"
        echo
        case "$choice" in
            1)  do_search ;;
            2)  do_show ;;
            3)  do_depends ;;
            4)  do_rdepends ;;
            5)  do_policy ;;
            6)  do_list_installed ;;
            7)  do_list_upgradable ;;
            8)  do_install ;;
            9)  do_reinstall ;;
            10) do_remove ;;
            11) do_purge ;;
            12) do_download ;;
            13) do_source ;;
            14) do_build_dep ;;
            15) do_update ;;
            16) do_upgrade ;;
            17) do_full_upgrade ;;
            18) do_autoremove ;;
            19) do_clean ;;
            20) do_fix_broken ;;
            21) do_check ;;
            22) do_hold ;;
            23) do_unhold ;;
            24) do_showhold ;;
            25) do_add_repo ;;
            26) do_proxy ;;
            80) do_toggle_theme ;;
            90) do_raw ;;
            0|q|Q) ok "Bye!"; exit 0 ;;
            "") continue ;;
            *)  warn "Invalid option: '$choice'" ;;
        esac
        pause
    done
}

main "$@"
