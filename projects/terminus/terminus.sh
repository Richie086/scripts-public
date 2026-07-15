#!/bin/bash
# TERMINUS - Standalone Network Operations Monitor
# Strict shell options for safety and reliability
set -euo pipefail

# Directory paths
CONFIG_DIR="${HOME}/.config/terminus"
STATUS_DIR="${CONFIG_DIR}/status"
PID_DIR="${CONFIG_DIR}/pids"
FIFO_PATH="${CONFIG_DIR}/web_fifo"

# Configuration variables
PORT="${TERMINUS_PORT:-8080}"
SETTINGS_FILE="${CONFIG_DIR}/settings.conf"
DEVICE_TYPES_FILE="${CONFIG_DIR}/device_types.conf"

load_settings() {
    # Default settings
    PING_COUNT=5
    PING_INTERVAL=0.2
    SWEEP_FREQUENCY=60
    ENV_1="Tenant A"
    ENV_2="Tenant B"
    ENV_3="Tenant C"
    ROOM_NAME="Server Room B"
    PHYSICAL_ADDRESS="456 Enterprise Way"
    COMPANY_NAME="General Corp"
    
    if [[ -f "${SETTINGS_FILE}" ]]; then
        while IFS='=' read -r key val || [[ -n "$key" ]]; do
            [[ -z "$key" || "$key" =~ ^# ]] && continue
            key=$(echo "$key" | xargs)
            val=$(echo "$val" | xargs)
            case "$key" in
                PING_COUNT) PING_COUNT="$val" ;;
                PING_INTERVAL) PING_INTERVAL="$val" ;;
                SWEEP_FREQUENCY) SWEEP_FREQUENCY="$val" ;;
                ENV_1) ENV_1="$val" ;;
                ENV_2) ENV_2="$val" ;;
                ENV_3) ENV_3="$val" ;;
                ROOM_NAME) ROOM_NAME="$val" ;;
                PHYSICAL_ADDRESS) PHYSICAL_ADDRESS="$val" ;;
                COMPANY_NAME) COMPANY_NAME="$val" ;;
            esac
        done < "${SETTINGS_FILE}"
    else
        mkdir -p "${CONFIG_DIR}"
        cat <<EOF > "${SETTINGS_FILE}"
PING_COUNT=5
PING_INTERVAL=0.2
SWEEP_FREQUENCY=60
ENV_1=Tenant A
ENV_2=Tenant B
ENV_3=Tenant C
ROOM_NAME=Server Room B
PHYSICAL_ADDRESS=456 Enterprise Way
COMPANY_NAME=General Corp
EOF
    fi
    
    ENVIRONMENTS=("${ENV_1}" "${ENV_2}" "${ENV_3}")
}

load_device_types() {
    DEVICE_TYPES=()
    if [[ -f "${DEVICE_TYPES_FILE}" ]]; then
        while read -r line || [[ -n "$line" ]]; do
            [[ -z "$line" || "$line" =~ ^# ]] && continue
            DEVICE_TYPES+=("$line")
        done < "${DEVICE_TYPES_FILE}"
    else
        # Seed default device types
        DEVICE_TYPES=("Server" "Router" "Switch" "Firewall" "Gateway" "Other")
        mkdir -p "${CONFIG_DIR}"
        for t in "${DEVICE_TYPES[@]}"; do
            echo "$t" >> "${DEVICE_TYPES_FILE}"
        done
    fi
}

load_settings
load_device_types

# Initialize config paths and seed initial nodes if files do not exist
init_dirs_and_configs() {
    mkdir -p "${CONFIG_DIR}" "${STATUS_DIR}" "${PID_DIR}"
    
    for env in "${ENVIRONMENTS[@]}"; do
        local lower_env="${env,,}"
        local file_name="${lower_env// /_}.conf"
        local file_path="${CONFIG_DIR}/${file_name}"
        if [[ ! -f "${file_path}" ]]; then
            touch "${file_path}"
        fi
    done
}

# DNS Lookup Engine
# If IP is supplied without name, runs reverse PTR lookup.
# If Hostname is supplied without IP, runs forward A lookup.
resolve_dns() {
    local input="$1"
    local mode="$2"
    
    if [[ "$mode" == "forward" ]]; then
        local ip
        ip=$(dig +short "$input" 2>/dev/null | grep -E '^[0-9.]+$' | head -n 1) || true
        if [[ -z "$ip" ]]; then
            ip=$(host "$input" 2>/dev/null | grep -oE 'has address [0-9.]+' | awk '{print $3}' | head -n 1) || true
        fi
        echo "${ip:-N/A}"
    else
        local host_name
        host_name=$(dig +short -x "$input" 2>/dev/null | head -n 1) || true
        if [[ -z "$host_name" ]]; then
            host_name=$(host "$input" 2>/dev/null | grep -oE 'pointer [a-zA-Z0-9.-]+' | awk '{print $NF}' | head -n 1) || true
        fi
        echo "${host_name%.}"
    fi
}

# Get next unique ID for an environment config file
get_next_id() {
    local file="$1"
    if [[ ! -f "$file" ]]; then
        echo 1
        return
    fi
    local max_id=0
    while IFS='|' read -r nid name addr dev_type fqdn || [[ -n "$nid" ]]; do
        [[ -z "$nid" ]] && continue
        # strip non-digits to verify numeric ID
        local clean_id
        clean_id=$(echo "$nid" | tr -cd '0-9')
        if [[ -n "$clean_id" && "$clean_id" -gt "$max_id" ]]; then
            max_id="$clean_id"
        fi
    done < "$file"
    echo $((max_id + 1))
}

# Add a node to an environment
add_node() {
    local env="$1"
    local name="$2"
    local addr="$3"
    local dev_type="${4:-Server}"
    
    local lower_env="${env,,}"
    local file_name="${lower_env// /_}.conf"
    local file_path="${CONFIG_DIR}/${file_name}"
    
    # Resolve fallback DNS if fields are blank
    if [[ -z "$name" && -n "$addr" ]]; then
        name=$(resolve_dns "$addr" "reverse")
        if [[ -z "$name" || "$name" == "N/A" ]]; then
            name="$addr"
        fi
    elif [[ -n "$name" && -z "$addr" ]]; then
        if [[ "$name" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            addr="$name"
        else
            addr=$(resolve_dns "$name" "forward")
            if [[ -z "$addr" || "$addr" == "N/A" ]]; then
                addr="$name"
            fi
        fi
    fi
    
    if [[ -z "$name" || -z "$addr" ]]; then
        return 1
    fi
    
    # Resolve FQDN if possible
    local fqdn=""
    if [[ "$addr" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        # addr is IP, resolve PTR
        fqdn=$(resolve_dns "$addr" "reverse")
        if [[ -z "$fqdn" || "$fqdn" == "$addr" || "$fqdn" == "N/A" ]]; then
            fqdn=""
        fi
    else
        # addr is Hostname
        fqdn="$addr"
        local resolved_ip
        resolved_ip=$(resolve_dns "$addr" "forward")
        if [[ -n "$resolved_ip" && "$resolved_ip" != "N/A" ]]; then
            addr="$resolved_ip"
        fi
    fi
    
    local nid
    nid=$(get_next_id "$file_path")
    echo "${nid}|${name}|${addr}|${dev_type}|${fqdn}" >> "$file_path"
    
    # Quick initial status sweep
    update_status_for_node "$env" "$nid" "$name" "$addr" &
}

# Quick status updater for a single node (runs backgrounded on addition)
update_status_for_node() {
    local env="$1"
    local nid="$2"
    local name="$3"
    local addr="$4"
    
    local lower_env="${env,,}"
    local file_name="${lower_env// /_}"
    local status_file="${STATUS_DIR}/${file_name}.status"
    
    local ping_out
    if ping_out=$(ping -c 1 -w 1 "$addr" 2>&1); then
        local avg_rtt
        avg_rtt=$(echo "$ping_out" | grep '^rtt' | cut -d'=' -f2 | cut -d'/' -f2 | tr -d ' ' || echo "0.0")
        echo "${nid}|UP|${avg_rtt} ms||.......................1" >> "$status_file"
    else
        echo "${nid}|DOWN|N/A|$(date +%H:%M:%S)|.......................0" >> "$status_file"
    fi
}

# Delete a node from an environment config and status file
delete_node() {
    local env="$1"
    local nid="$2"
    
    local lower_env="${env,,}"
    local file_name="${lower_env// /_}"
    local conf_path="${CONFIG_DIR}/${file_name}.conf"
    local status_path="${STATUS_DIR}/${file_name}.status"
    
    [[ ! -f "$conf_path" ]] && return
    
    local tmp_conf="${conf_path}.tmp"
    grep -v "^${nid}|" "$conf_path" > "$tmp_conf" || true
    mv "$tmp_conf" "$conf_path"
    
    if [[ -f "$status_path" ]]; then
        local tmp_status="${status_path}.tmp"
        grep -v "^${nid}|" "$status_path" > "$tmp_status" || true
        mv "$tmp_status" "$status_path"
    fi
}

# Asynchronous Sweep Daemon Process
run_daemon() {
    init_dirs_and_configs
    if [[ -f "${PID_DIR}/daemon.pid" ]]; then
        local old_pid
        old_pid=$(cat "${PID_DIR}/daemon.pid" 2>/dev/null || true)
        if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
            echo "Sweep daemon already running (PID: $old_pid)."
            return
        fi
    fi
    echo $$ > "${PID_DIR}/daemon.pid"
    
    # Daemon signal trap for PID cleanup
    trap 'rm -f "${PID_DIR}/daemon.pid"' EXIT SIGINT SIGTERM
    
    while true; do
        load_settings
        for env in "${ENVIRONMENTS[@]}"; do
            local lower_env="${env,,}"
            local file_name="${lower_env// /_}"
            local conf_file="${CONFIG_DIR}/${file_name}.conf"
            local status_file="${STATUS_DIR}/${file_name}.status"
            local tmp_status_file="${status_file}.tmp"
            
            [[ ! -f "${conf_file}" ]] && continue
            
            # Read previous statuses and histories into memory
            declare -A prev_status=()
            declare -A prev_down_since=()
            declare -A prev_history=()
            if [[ -f "${status_file}" ]]; then
                while IFS='|' read -r nid stat lat dsince hist || [[ -n "$nid" ]]; do
                    [[ -z "$nid" ]] && continue
                    prev_status["$nid"]="$stat"
                    prev_down_since["$nid"]="$dsince"
                    prev_history["$nid"]="$hist"
                done < "${status_file}"
            fi
            
            declare -A pids=()
            
            # Ping each node in parallel to speed up execution
            while IFS='|' read -r nid name addr dev_type fqdn || [[ -n "$nid" ]]; do
                [[ -z "$nid" ]] && continue
                (
                    local ping_out
                    local prev_h="${prev_history[$nid]:-........................}"
                    if [[ ${#prev_h} -lt 24 ]]; then
                        local pad_len=$(( 24 - ${#prev_h} ))
                        local padding
                        padding=$(printf '%*s' "$pad_len" "" | tr ' ' '.')
                        prev_h="${padding}${prev_h}"
                    fi
                    local new_h
                    
                    # Dynamic sweeps based on config settings
                    if ping_out=$(ping -c "${PING_COUNT:-5}" -i "${PING_INTERVAL:-0.2}" -w $(( PING_COUNT + 2 )) "$addr" 2>&1); then
                        local avg_rtt
                        avg_rtt=$(echo "$ping_out" | grep '^rtt' | cut -d'=' -f2 | cut -d'/' -f2 | tr -d ' ' || echo "")
                        new_h="${prev_h:1}1"
                        if [[ -n "$avg_rtt" ]]; then
                            echo "${nid}|UP|${avg_rtt} ms||${new_h}"
                        else
                            echo "${nid}|UP|0.0 ms||${new_h}"
                        fi
                    else
                        new_h="${prev_h:1}0"
                        local since
                        local prev_s="${prev_status[$nid]:-UP}"
                        if [[ "$prev_s" == "DOWN" ]]; then
                            since="${prev_down_since[$nid]:-$(date +%H:%M:%S)}"
                        else
                            since="$(date +%H:%M:%S)"
                        fi
                        echo "${nid}|DOWN|N/A|${since}|${new_h}"
                    fi
                ) > "/tmp/terminus_ping_${file_name}_${nid}.res" 2>&1 &
                pids["$nid"]=$!
            done < "${conf_file}"
            
            # Wait for parallel sweeps to complete
            for nid in "${!pids[@]}"; do
                wait "${pids[$nid]}" 2>/dev/null || true
            done
            
            # Write final status updates atomically
            : > "${tmp_status_file}"
            while IFS='|' read -r nid name addr dev_type fqdn || [[ -n "$nid" ]]; do
                [[ -z "$nid" ]] && continue
                local res_file="/tmp/terminus_ping_${file_name}_${nid}.res"
                if [[ -f "${res_file}" ]]; then
                    cat "${res_file}" >> "${tmp_status_file}"
                    rm -f "${res_file}"
                else
                    local prev_h="${prev_history[$nid]:-........................}"
                    if [[ ${#prev_h} -lt 24 ]]; then
                        local pad_len=$(( 24 - ${#prev_h} ))
                        local padding
                        padding=$(printf '%*s' "$pad_len" "" | tr ' ' '.')
                        prev_h="${padding}${prev_h}"
                    fi
                    local new_h="${prev_h:1}0"
                    echo "${nid}|DOWN|N/A|$(date +%H:%M:%S)|${new_h}" >> "${tmp_status_file}"
                fi
            done < "${conf_file}"
            
            mv "${tmp_status_file}" "${status_file}"
        done
        sleep "${SWEEP_FREQUENCY:-60}"
    done
}

# URL Value Decoder helper (converts percent encoding and '+' to space)
decode_val() {
    local val="${1//+/ }"
    printf '%b' "${val//%/\\x}"
}
# Output Webserver HTML Response
send_html_response() {
    local active_env="$1"
    
    local lower_env="${active_env,,}"
    local file_name="${lower_env// /_}"
    local conf_file="${CONFIG_DIR}/${file_name}.conf"
    local status_file="${STATUS_DIR}/${file_name}.status"
    
    local table_rows=""
    
    declare -A statuses=()
    declare -A latencies=()
    declare -A down_sinces=()
    declare -A histories=()
    if [[ -f "${status_file}" ]]; then
        while IFS='|' read -r nid stat lat dsince hist || [[ -n "$nid" ]]; do
            [[ -z "$nid" ]] && continue
            statuses["$nid"]="$stat"
            latencies["$nid"]="$lat"
            down_sinces["$nid"]="$dsince"
            histories["$nid"]="$hist"
        done < "${status_file}"
    fi
    
    if [[ -f "${conf_file}" ]]; then
        while IFS='|' read -r nid name addr dev_type fqdn || [[ -n "$nid" ]]; do
            [[ -z "$nid" ]] && continue
            local stat="${statuses[$nid]:-PENDING}"
            local lat="${latencies[$nid]:-N/A}"
            local dsince="${down_sinces[$nid]:-}"
            
            local status_badge=""
            if [[ "$stat" == "UP" ]]; then
                status_badge="<span class=\"status-badge status-online\">ONLINE</span>"
            elif [[ "$stat" == "DOWN" ]]; then
                status_badge="<span class=\"status-badge status-alert\">ALERT</span>"
            else
                status_badge="<span class=\"status-badge status-pending\">PENDING</span>"
            fi
            
            local detail_str=""
            if [[ "$stat" == "DOWN" ]]; then
                detail_str="Since: ${dsince}"
            else
                detail_str="${lat}"
            fi
            
            local fqdn_val="${fqdn:-}"
            local addr_html
            if [[ -n "$fqdn_val" ]]; then
                addr_html="<code>${addr}</code><br><span style=\"font-size: 0.75rem; color: var(--fg-dim); font-family: inherit;\">${fqdn_val}</span>"
            else
                addr_html="<code>${addr}</code>"
            fi
            
            local hist="${histories[$nid]:-........................}"
            if [[ ${#hist} -lt 24 ]]; then
                local pad_len=$(( 24 - ${#hist} ))
                local padding
                padding=$(printf '%*s' "$pad_len" "" | tr ' ' '.')
                hist="${padding}${hist}"
            fi
            
            local spark_html=""
            for (( i=0; i<24; i++ )); do
                local char="${hist:$i:1}"
                if [[ "$char" == "1" ]]; then
                    spark_html="${spark_html}<span style=\"color: var(--green); font-size: 1.15rem; line-height: 1; letter-spacing: -2px; margin-right: 1px;\" title=\"Sweep $((i+1)): UP\">■</span>"
                elif [[ "$char" == "0" ]]; then
                    spark_html="${spark_html}<span style=\"color: var(--red); font-size: 1.15rem; line-height: 1; letter-spacing: -2px; margin-right: 1px;\" title=\"Sweep $((i+1)): DOWN\">■</span>"
                else
                    spark_html="${spark_html}<span style=\"color: var(--fg-dim); font-size: 1.15rem; line-height: 1; letter-spacing: -2px; margin-right: 1px;\" title=\"Sweep $((i+1)): PENDING\">·</span>"
                fi
            done
            
            table_rows="${table_rows}
            <tr>
                <td>${nid}</td>
                <td>${dev_type:-Server}</td>
                <td><strong>${name}</strong></td>
                <td>${addr_html}</td>
                <td>${status_badge}</td>
                <td>${detail_str}</td>
                <td style=\"white-space: nowrap;\">${spark_html}</td>
                <td>
                    <a href=\"/delete?env=${active_env// /+}&id=${nid}\" class=\"btn btn-danger\">[Delete]</a>
                </td>
            </tr>"
        done < "${conf_file}"
    fi
    
    if [[ -z "$table_rows" ]]; then
        table_rows="<tr><td colspan=\"8\" style=\"text-align: center; color: var(--fg-dim); padding: 40px;\">No nodes configured in this environment.</td></tr>"
    fi
    
    local tabs_html=""
    for e in "${ENVIRONMENTS[@]}"; do
        if [[ "$e" == "$active_env" ]]; then
            tabs_html="${tabs_html}<a href=\"/?env=${e// /+}\" class=\"tab-btn active\">[ ${e} ]</a>"
        else
            tabs_html="${tabs_html}<a href=\"/?env=${e// /+}\" class=\"tab-btn\">[ ${e} ]</a>"
        fi
    done
    
    local device_options=""
    for t in "${DEVICE_TYPES[@]}"; do
        device_options="${device_options}<option value=\"${t}\">${t}</option>"
    done
    
    # Dynamic Host System Specifications
    local hostname_running; hostname_running=$(hostname 2>/dev/null || echo "Unknown")
    local time_utc; time_utc=$(date -u "+%Y-%m-%d %H:%M:%S UTC")
    local time_local; time_local=$(date "+%Y-%m-%d %H:%M:%S %Z")
    local os_running="Linux"
    if [[ -f /etc/os-release ]]; then
        os_running=$(grep '^PRETTY_NAME=' /etc/os-release | cut -d= -f2 | tr -d '"')
    fi
    local ram_total; ram_total=$(free -h 2>/dev/null | grep Mem | awk '{print $2}' || echo "N/A")
    local cpu_model="N/A"
    if [[ -f /proc/cpuinfo ]]; then
        cpu_model=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs || true)
    fi
    [[ -z "$cpu_model" ]] && cpu_model="Unknown CPU"
    local ip_addresses; ip_addresses=$(hostname -I 2>/dev/null | xargs || echo "N/A")
    
    echo -e "HTTP/1.1 200 OK\r"
    echo -e "Content-Type: text/html\r"
    echo -e "Connection: close\r"
    echo -e "\r"
    
    cat <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TERMINUS | Operations Terminal</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Spline+Sans+Mono:wght@300;400;500;600;700&display=swap');
        :root {
            --bg-base: #1e1f29;
            --bg-elevated: #282a36;
            --border: #44475a;
            --fg-base: #f8f8f2;
            --fg-dim: #6272a4;
            --green: #50fa7b;
            --red: #ff5555;
            --orange: #ffb86c;
            --purple: #bd93f9;
            --cyan: #8be9fd;
        }
        * { box-sizing: border-box; }
        body {
            background-color: #0c0d12;
            color: var(--fg-base);
            font-family: 'Spline Sans Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .terminal-window {
            width: 100%;
            max-width: 950px;
            background-color: var(--bg-base);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.6);
            overflow: hidden;
            margin-bottom: 20px;
        }
        .terminal-header {
            background-color: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
            padding: 10px 15px;
            display: flex;
            align-items: center;
            position: relative;
        }
        .terminal-buttons {
            display: flex;
            gap: 8px;
        }
        .btn-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .dot-red { background-color: var(--red); }
        .dot-yellow { background-color: var(--orange); }
        .dot-green { background-color: var(--green); }
        .terminal-title {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            color: var(--fg-dim);
            font-size: 0.85rem;
            font-weight: 500;
        }
        .terminal-body {
            padding: 25px;
        }
        .prompt-line {
            margin-bottom: 15px;
            font-size: 0.95rem;
        }
        .prompt-symbol {
            color: var(--green);
            font-weight: bold;
        }
        .prompt-path {
            color: var(--cyan);
        }
        .command-text {
            color: var(--fg-base);
        }
        .nav-links {
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            font-size: 1rem;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 15px;
        }
        .nav-links a {
            color: var(--cyan);
            text-decoration: none;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }
        .tab-btn {
            color: var(--fg-dim);
            padding: 6px 12px;
            text-decoration: none;
            font-weight: 500;
        }
        .tab-btn:hover {
            color: var(--fg-base);
        }
        .tab-btn.active {
            color: var(--green);
            font-weight: bold;
        }
        .card {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 25px;
        }
        .section-title {
            font-size: 1.1rem;
            color: var(--purple);
            margin: 0 0 15px 0;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 10px;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        th {
            color: var(--cyan);
            border-bottom: 2px solid var(--border);
            font-weight: bold;
        }
        td {
            border-bottom: none;
        }
        .status-badge {
            font-weight: bold;
        }
        .status-online { color: var(--green); }
        .status-alert { color: var(--red); }
        .status-pending { color: var(--orange); }
        code {
            background-color: rgba(0, 0, 0, 0.25);
            padding: 2px 6px;
            border-radius: 4px;
            color: var(--cyan);
        }
        .btn {
            background-color: var(--green);
            color: #0c0d12;
            border: none;
            padding: 6px 12px;
            font-family: inherit;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
            text-decoration: none;
            display: inline-block;
        }
        .btn-danger {
            background-color: transparent;
            color: var(--red);
            border: 1px solid var(--red);
            padding: 2px 8px;
        }
        .btn-danger:hover {
            background-color: var(--red);
            color: var(--fg-base);
        }
        .form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr auto;
            gap: 16px;
            align-items: end;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        label {
            color: var(--fg-dim);
            margin-bottom: 6px;
        }
        input, select {
            background-color: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--fg-base);
            padding: 8px 12px;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
        }
        input:focus, select:focus {
            border-color: var(--purple);
        }
    </style>
    <meta http-equiv="refresh" content="10">
</head>
<body>
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-buttons">
                <span class="btn-dot dot-red"></span>
                <span class="btn-dot dot-yellow"></span>
                <span class="btn-dot dot-green"></span>
            </div>
            <div class="terminal-title">rtroiano@${hostname_running}: ~/terminus</div>
        </div>
        
        <div class="terminal-body">
            <div class="nav-links">
                <a href="/" style="color: var(--green); font-weight: bold;">[ Dashboard ]</a>
                <a href="/admin">[ Admin Settings ]</a>
                <a href="/nginx_status">[ Nginx Status ]</a>
            </div>

            <div class="prompt-line">
                <span class="prompt-symbol">rtroiano@${hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">terminus --show-nodes --env "${active_env}"</span>
            </div>

            <div class="tabs">
                ${tabs_html}
            </div>

            <div class="card">
                <div class="section-title">&gt;_ Environment Nodes Grid</div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 50px;">ID</th>
                            <th>Device Type</th>
                            <th>Node Name</th>
                            <th>Target Host/IP</th>
                            <th>Status</th>
                            <th>Performance Details</th>
                            <th>Uptime History (Last 24 Sweeps)</th>
                            <th style="width: 80px;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${table_rows}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <div class="section-title">&gt;_ Add Node Configuration</div>
                <form action="/add" method="GET">
                    <input type="hidden" name="env" value="${active_env}">
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="name">Node Name</label>
                            <input type="text" id="name" name="name" placeholder="e.g. Gateway" required>
                        </div>
                        <div class="form-group">
                            <label for="addr">IP / Hostname</label>
                            <input type="text" id="addr" name="addr" placeholder="e.g. 192.168.1.1" required>
                        </div>
                        <div class="form-group">
                            <label for="dev_type">Device Type</label>
                            <select id="dev_type" name="dev_type">
                                ${device_options}
                            </select>
                        </div>
                        <button type="submit" class="btn">Add Node</button>
                    </div>
                </form>
            </div>

            <div class="prompt-line" style="margin-top: 30px;">
                <span class="prompt-symbol">rtroiano@${hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">terminus --show-host-info</span>
            </div>

            <div class="card">
                <div class="section-title">&gt;_ Host System Specs</div>
                <table>
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Configured / Dynamic System Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>System Hostname</td>
                            <td><code>${hostname_running}</code></td>
                        </tr>
                        <tr>
                            <td>Physical Room Location</td>
                            <td><code>${ROOM_NAME:-Server Room B}</code></td>
                        </tr>
                        <tr>
                            <td>Physical Address</td>
                            <td><code>${PHYSICAL_ADDRESS:-456 Enterprise Way}</code></td>
                        </tr>
                        <tr>
                            <td>Company Name</td>
                            <td><code>${COMPANY_NAME:-General Corp}</code></td>
                        </tr>
                        <tr>
                            <td>Time (UTC)</td>
                            <td><code>${time_utc}</code></td>
                        </tr>
                        <tr>
                            <td>Time (Local Zone)</td>
                            <td><code>${time_local}</code></td>
                        </tr>
                        <tr>
                            <td>Operating System (OS)</td>
                            <td><code>${os_running}</code></td>
                        </tr>
                        <tr>
                            <td>Total Memory (RAM)</td>
                            <td><code>${ram_total}</code></td>
                        </tr>
                        <tr>
                            <td>Processor (CPU)</td>
                            <td><code>${cpu_model}</code></td>
                        </tr>
                        <tr>
                            <td>Active Network IP(s)</td>
                            <td><code>${ip_addresses}</code></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
EOF
}

# Helper to rename physical environment config/status files
rename_env_files() {
    local old_name="$1"
    local new_name="$2"
    [[ "$old_name" == "$new_name" ]] && return
    
    local old_lower="${old_name,,}"
    local old_file="${old_lower// /_}"
    local new_lower="${new_name,,}"
    local new_file="${new_lower// /_}"
    
    if [[ -f "${CONFIG_DIR}/${old_file}.conf" ]]; then
        mv "${CONFIG_DIR}/${old_file}.conf" "${CONFIG_DIR}/${new_file}.conf"
    fi
    if [[ -f "${STATUS_DIR}/${old_file}.status" ]]; then
        mv "${STATUS_DIR}/${old_file}.status" "${STATUS_DIR}/${new_file}.status"
    fi
}

# Admin settings dashboard response
send_admin_response() {
    local query="${1:-}"
    
    local success_param
    success_param=$(echo "$query" | grep -oE 'success=[^&]*' | cut -d= -f2 || true)
    
    local success_msg=""
    if [[ "$success_param" == "1" ]]; then
        success_msg="<div class=\"alert alert-success\">Tabs updated successfully!</div>"
    elif [[ "$success_param" == "2" ]]; then
        success_msg="<div class=\"alert alert-success\">Sweep &amp; Ping config updated successfully!</div>"
    elif [[ "$success_param" == "3" ]]; then
        success_msg="<div class=\"alert alert-success\">Device type added!</div>"
    elif [[ "$success_param" == "4" ]]; then
        success_msg="<div class=\"alert alert-success\">Device type deleted!</div>"
    elif [[ "$success_param" == "5" ]]; then
        success_msg="<div class=\"alert alert-success\">Host system settings updated successfully!</div>"
    fi
    
    local error_msg=""
    
    local types_html=""
    for t in "${DEVICE_TYPES[@]}"; do
        types_html="${types_html}
        <div style=\"display: flex; justify-content: space-between; padding: 6px 10px; border-bottom: 1px dashed #44475a;\">
            <span>${t}</span>
            <a href=\"/admin/del_type?type=${t// /+}\" style=\"color: #ff5555; text-decoration: none;\">[Delete]</a>
        </div>"
    done
    
    local hostname_running; hostname_running=$(hostname 2>/dev/null || echo "Unknown")
    
    echo -e "HTTP/1.1 200 OK\r"
    echo -e "Content-Type: text/html\r"
    echo -e "Connection: close\r"
    echo -e "\r"
    
    cat <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Terminus Admin Dashboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Spline+Sans+Mono:wght@300;400;500;600;700&display=swap');
        :root {
            --bg-base: #1e1f29;
            --bg-elevated: #282a36;
            --border: #44475a;
            --fg-base: #f8f8f2;
            --fg-dim: #6272a4;
            --green: #50fa7b;
            --red: #ff5555;
            --orange: #ffb86c;
            --purple: #bd93f9;
            --cyan: #8be9fd;
        }
        * { box-sizing: border-box; }
        body {
            background-color: #0c0d12;
            color: var(--fg-base);
            font-family: 'Spline Sans Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .terminal-window {
            width: 100%;
            max-width: 950px;
            background-color: var(--bg-base);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.6);
            overflow: hidden;
            margin-bottom: 20px;
        }
        .terminal-header {
            background-color: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
            padding: 10px 15px;
            display: flex;
            align-items: center;
            position: relative;
        }
        .terminal-buttons {
            display: flex;
            gap: 8px;
        }
        .btn-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .dot-red { background-color: var(--red); }
        .dot-yellow { background-color: var(--orange); }
        .dot-green { background-color: var(--green); }
        .terminal-title {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            color: var(--fg-dim);
            font-size: 0.85rem;
            font-weight: 500;
        }
        .terminal-body {
            padding: 25px;
        }
        .prompt-line {
            margin-bottom: 15px;
            font-size: 0.95rem;
        }
        .prompt-symbol {
            color: var(--green);
            font-weight: bold;
        }
        .prompt-path {
            color: var(--cyan);
        }
        .command-text {
            color: var(--fg-base);
        }
        .nav-links {
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            font-size: 1rem;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 15px;
        }
        .nav-links a {
            color: var(--cyan);
            text-decoration: none;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .card {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 10px;
        }
        .card-title {
            color: var(--purple);
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.1rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            margin-bottom: 15px;
        }
        label {
            color: var(--fg-dim);
            margin-bottom: 5px;
            font-size: 0.9rem;
        }
        input {
            background-color: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--fg-base);
            padding: 8px 12px;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
        }
        input:focus {
            border-color: var(--purple);
        }
        .btn {
            background-color: var(--green);
            color: #0c0d12;
            border: none;
            padding: 10px 15px;
            font-family: inherit;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px;
            display: inline-block;
        }
        .btn:hover {
            box-shadow: 0 2px 8px rgba(80,250,123,0.4);
        }
        .alert {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .alert-success {
            background-color: rgba(80,250,123,0.15);
            color: var(--green);
            border: 1px solid var(--green);
        }
        .alert-error {
            background-color: rgba(255,85,85,0.15);
            color: var(--red);
            border: 1px solid var(--red);
        }
    </style>
</head>
<body>
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-buttons">
                <span class="btn-dot dot-red"></span>
                <span class="btn-dot dot-yellow"></span>
                <span class="btn-dot dot-green"></span>
            </div>
            <div class="terminal-title">rtroiano@${hostname_running}: ~/terminus (admin)</div>
        </div>
        
        <div class="terminal-body">
            <div class="nav-links">
                <a href="/">[ Dashboard ]</a>
                <a href="/admin" style="color: var(--green); font-weight: bold;">[ Admin Settings ]</a>
                <a href="/nginx_status">[ Nginx Status ]</a>
            </div>

            <div class="prompt-line">
                <span class="prompt-symbol">rtroiano@${hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">terminus --admin-settings</span>
            </div>
            
            ${success_msg}
            ${error_msg}
            
            <div class="grid">
                <div class="card">
                    <div class="card-title">&gt;_ Tab Name Editor</div>
                    <form action="/admin/save_tabs" method="GET">
                        <div class="form-group">
                            <label>Tab 1 Name</label>
                            <input type="text" name="env1" value="${ENVIRONMENTS[0]}">
                        </div>
                        <div class="form-group">
                            <label>Tab 2 Name</label>
                            <input type="text" name="env2" value="${ENVIRONMENTS[1]}">
                        </div>
                        <div class="form-group">
                            <label>Tab 3 Name</label>
                            <input type="text" name="env3" value="${ENVIRONMENTS[2]}">
                        </div>
                        <button type="submit" class="btn">Save Tabs</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Sweep &amp; Ping Config</div>
                    <form action="/admin/save_ping" method="GET">
                        <div class="form-group">
                            <label>Sweep Frequency (seconds)</label>
                            <input type="number" name="frequency" value="${SWEEP_FREQUENCY}">
                        </div>
                        <div class="form-group">
                            <label>Ping Count per Sweep</label>
                            <input type="number" name="pcount" value="${PING_COUNT}">
                        </div>
                        <div class="form-group">
                            <label>Ping Interval (seconds)</label>
                            <input type="text" name="pinterval" value="${PING_INTERVAL}">
                        </div>
                        <button type="submit" class="btn">Save Configuration</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Host System Configurations</div>
                    <form action="/admin/save_host" method="GET">
                        <div class="form-group">
                            <label>Physical Room Location</label>
                            <input type="text" name="room" value="${ROOM_NAME}">
                        </div>
                        <div class="form-group">
                            <label>Physical Address</label>
                            <input type="text" name="address" value="${PHYSICAL_ADDRESS}">
                        </div>
                        <div class="form-group">
                            <label>Company Name</label>
                            <input type="text" name="company" value="${COMPANY_NAME}">
                        </div>
                        <button type="submit" class="btn">Save Host Info</button>
                    </form>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Manage Device Types</div>
                    <form action="/admin/add_type" method="GET" style="margin-bottom: 20px;">
                        <div class="form-group">
                            <label>New Device Type</label>
                            <input type="text" name="type" placeholder="e.g. Access Point" required>
                        </div>
                        <button type="submit" class="btn">Add Device Type</button>
                    </form>
                    <div>
                        ${types_html}
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
EOF
}

# Styled Nginx stub_status live dashboard response
send_nginx_status_response() {
    # 1. Fetch raw nginx status from local Nginx stub module
    local raw_status
    raw_status=$(curl -s http://127.0.0.1/nginx_status_raw || echo "Error: Nginx stub_status unreachable on http://127.0.0.1/nginx_status_raw")
    
    # 2. Parse connections metrics
    local active=0 accepts=0 handled=0 requests=0 reading=0 writing=0 waiting=0
    if [[ "$raw_status" =~ Active\ connections:\ ([0-9]+) ]]; then
        active="${BASH_REMATCH[1]}"
    fi
    local line3
    line3=$(echo "$raw_status" | sed -n '3p' || echo "")
    if [[ -n "$line3" ]]; then
        accepts=$(echo "$line3" | awk '{print $1}')
        handled=$(echo "$line3" | awk '{print $2}')
        requests=$(echo "$line3" | awk '{print $3}')
    fi
    local line4
    line4=$(echo "$raw_status" | sed -n '4p' || echo "")
    if [[ -n "$line4" ]]; then
        reading=$(echo "$line4" | awk '{print $2}')
        writing=$(echo "$line4" | awk '{print $4}')
        waiting=$(echo "$line4" | awk '{print $6}')
    fi
    
    # 3. Pull additional system stats to show as much detail as possible
    local sys_uptime
    sys_uptime=$(uptime -p 2>/dev/null || echo "N/A")
    local load_avg
    load_avg=$(cat /proc/loadavg 2>/dev/null || echo "N/A")
    local mem_info
    mem_info=$(free -h 2>/dev/null | grep Mem | awk '{printf "Used: %s / Total: %s", $3, $2}' || echo "N/A")
    local nginx_ver
    nginx_ver=$(nginx -v 2>&1 || echo "N/A")
    
    local hostname_running; hostname_running=$(hostname 2>/dev/null || echo "Unknown")
    
    # 4. Generate HTML response
    echo -e "HTTP/1.1 200 OK\r"
    echo -e "Content-Type: text/html\r"
    echo -e "Connection: close\r"
    echo -e "\r"
    
    cat <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Nginx Styled Status</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Spline+Sans+Mono:wght@300;400;500;600;700&display=swap');
        :root {
            --bg-base: #1e1f29;
            --bg-elevated: #282a36;
            --border: #44475a;
            --fg-base: #f8f8f2;
            --fg-dim: #6272a4;
            --green: #50fa7b;
            --red: #ff5555;
            --orange: #ffb86c;
            --purple: #bd93f9;
            --cyan: #8be9fd;
        }
        * { box-sizing: border-box; }
        body {
            background-color: #0c0d12;
            color: var(--fg-base);
            font-family: 'Spline Sans Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .terminal-window {
            width: 100%;
            max-width: 950px;
            background-color: var(--bg-base);
            border: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.6);
            overflow: hidden;
            margin-bottom: 20px;
        }
        .terminal-header {
            background-color: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
            padding: 10px 15px;
            display: flex;
            align-items: center;
            position: relative;
        }
        .terminal-buttons {
            display: flex;
            gap: 8px;
        }
        .btn-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        .dot-red { background-color: var(--red); }
        .dot-yellow { background-color: var(--orange); }
        .dot-green { background-color: var(--green); }
        .terminal-title {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            color: var(--fg-dim);
            font-size: 0.85rem;
            font-weight: 500;
        }
        .terminal-body {
            padding: 25px;
        }
        .prompt-line {
            margin-bottom: 15px;
            font-size: 0.95rem;
        }
        .prompt-symbol {
            color: var(--green);
            font-weight: bold;
        }
        .prompt-path {
            color: var(--cyan);
        }
        .command-text {
            color: var(--fg-base);
        }
        .nav-links {
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            font-size: 1rem;
            border-bottom: 1px dashed var(--border);
            padding-bottom: 15px;
        }
        .nav-links a {
            color: var(--cyan);
            text-decoration: none;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background-color: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 20px;
        }
        .card-title {
            font-size: 1.1rem;
            color: var(--purple);
            margin-bottom: 15px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 5px;
        }
        .metric {
            font-size: 1.3rem;
            color: var(--orange);
            margin-bottom: 10px;
        }
        .detail-line {
            margin-bottom: 8px;
        }
        .label {
            color: var(--fg-dim);
        }
        pre {
            background-color: rgba(0, 0, 0, 0.25);
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            color: var(--fg-base);
            margin: 0;
        }
    </style>
</head>
<body>
    <div class="terminal-window">
        <div class="terminal-header">
            <div class="terminal-buttons">
                <span class="btn-dot dot-red"></span>
                <span class="btn-dot dot-yellow"></span>
                <span class="btn-dot dot-green"></span>
            </div>
            <div class="terminal-title">rtroiano@${hostname_running}: ~/terminus (nginx-status)</div>
        </div>
        
        <div class="terminal-body">
            <div class="nav-links">
                <a href="/">[ Dashboard ]</a>
                <a href="/admin">[ Admin Settings ]</a>
                <a href="/nginx_status" style="color: var(--green); font-weight: bold;">[ Nginx Status ]</a>
            </div>

            <div class="prompt-line">
                <span class="prompt-symbol">rtroiano@${hostname_running}</span>:<span class="prompt-path">~/terminus</span>$ <span class="command-text">terminus --show-nginx-status</span>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-title">&gt;_ Connection State</div>
                    <div class="metric">${active} Active Connections</div>
                    <div class="detail-line"><span class="label">Reading:</span> ${reading}</div>
                    <div class="detail-line"><span class="label">Writing:</span> ${writing}</div>
                    <div class="detail-line"><span class="label">Waiting:</span> ${waiting}</div>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Request Performance</div>
                    <div class="detail-line"><span class="label">Accepts:</span> ${accepts}</div>
                    <div class="detail-line"><span class="label">Handled:</span> ${handled}</div>
                    <div class="detail-line"><span class="label">Total Requests:</span> ${requests}</div>
                    <div class="detail-line"><span class="label">Nginx Version:</span> ${nginx_ver}</div>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ System Resources</div>
                    <div class="detail-line"><span class="label">Uptime:</span> ${sys_uptime}</div>
                    <div class="detail-line"><span class="label">Memory:</span> ${mem_info}</div>
                    <div class="detail-line"><span class="label">Load Avg:</span> ${load_avg}</div>
                </div>
                
                <div class="card">
                    <div class="card-title">&gt;_ Raw Stub Output</div>
                    <pre>${raw_status}</pre>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
EOF
}

# Request Handler for Web Server
handle_http_request() {
    load_settings
    load_device_types
    local request_line=""
    read -r request_line || true
    
    [[ -z "$request_line" ]] && return
    
    # Read rest of HTTP headers
    local line=""
    while read -r line; do
        line=$(echo "$line" | tr -d '\r')
        [[ -z "$line" ]] && break
    done
    
    local method
    method=$(echo "$request_line" | awk '{print $1}') || true
    local full_path
    full_path=$(echo "$request_line" | awk '{print $2}') || true
    
    if [[ "$full_path" == "/favicon.ico" ]]; then
        echo -e "HTTP/1.1 204 No Content\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    fi
    
    local path="${full_path%%\?*}"
    local query=""
    if [[ "$full_path" == *\?* ]]; then
        query="${full_path#*\?}"
    fi
    
    if [[ "$path" == "/add" ]]; then
        local env
        env=$(echo "$query" | grep -oE 'env=[^&]*' | cut -d= -f2 || true)
        env=$(decode_val "$env")
        local name
        name=$(echo "$query" | grep -oE 'name=[^&]*' | cut -d= -f2 || true)
        name=$(decode_val "$name")
        local addr
        addr=$(echo "$query" | grep -oE 'addr=[^&]*' | cut -d= -f2 || true)
        addr=$(decode_val "$addr")
        local dev_type
        dev_type=$(echo "$query" | grep -oE 'dev_type=[^&]*' | cut -d= -f2 || true)
        dev_type=$(decode_val "$dev_type")
        
        # Default dev_type to Server if empty
        if [[ -z "$dev_type" ]]; then
            dev_type="Server"
        fi
        
        add_node "$env" "$name" "$addr" "$dev_type"
        
        echo -e "HTTP/1.1 302 Found\r"
        echo -e "Location: /?env=${env// /+}\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    elif [[ "$path" == "/delete" ]]; then
        local env
        env=$(echo "$query" | grep -oE 'env=[^&]*' | cut -d= -f2 || true)
        env=$(decode_val "$env")
        local id
        id=$(echo "$query" | grep -oE 'id=[^&]*' | cut -d= -f2 || true)
        id=$(decode_val "$id")
        
        delete_node "$env" "$id"
        
        echo -e "HTTP/1.1 302 Found\r"
        echo -e "Location: /?env=${env// /+}\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    elif [[ "$path" == "/nginx_status" ]]; then
        send_nginx_status_response
        return
    elif [[ "$path" == "/admin" ]]; then
        send_admin_response "$query"
        return
    elif [[ "$path" == "/admin/save_tabs" ]]; then
        local env1 env2 env3
        env1=$(decode_val "$(echo "$query" | grep -oE 'env1=[^&]*' | cut -d= -f2 || true)")
        env2=$(decode_val "$(echo "$query" | grep -oE 'env2=[^&]*' | cut -d= -f2 || true)")
        env3=$(decode_val "$(echo "$query" | grep -oE 'env3=[^&]*' | cut -d= -f2 || true)")
        
        [[ -z "$env1" ]] && env1="Tenant A"
        [[ -z "$env2" ]] && env2="Tenant B"
        [[ -z "$env3" ]] && env3="Tenant C"
        
        rename_env_files "${ENVIRONMENTS[0]}" "$env1"
        rename_env_files "${ENVIRONMENTS[1]}" "$env2"
        rename_env_files "${ENVIRONMENTS[2]}" "$env3"
        
        cat <<EOF > "${SETTINGS_FILE}"
PING_COUNT=${PING_COUNT}
PING_INTERVAL=${PING_INTERVAL}
SWEEP_FREQUENCY=${SWEEP_FREQUENCY}
ENV_1=${env1}
ENV_2=${env2}
ENV_3=${env3}
ROOM_NAME=${ROOM_NAME}
PHYSICAL_ADDRESS=${PHYSICAL_ADDRESS}
COMPANY_NAME=${COMPANY_NAME}
EOF
        
        echo -e "HTTP/1.1 302 Found\r"
        echo -e "Location: /admin?success=1\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    elif [[ "$path" == "/admin/save_ping" ]]; then
        local pcount pinterval pfrequency
        pcount=$(decode_val "$(echo "$query" | grep -oE 'pcount=[^&]*' | cut -d= -f2 || true)")
        pinterval=$(decode_val "$(echo "$query" | grep -oE 'pinterval=[^&]*' | cut -d= -f2 || true)")
        pfrequency=$(decode_val "$(echo "$query" | grep -oE 'frequency=[^&]*' | cut -d= -f2 || true)")
        
        [[ -z "$pcount" ]] && pcount=5
        [[ -z "$pinterval" ]] && pinterval=0.2
        [[ -z "$pfrequency" ]] && pfrequency=60
        
        cat <<EOF > "${SETTINGS_FILE}"
PING_COUNT=${pcount}
PING_INTERVAL=${pinterval}
SWEEP_FREQUENCY=${pfrequency}
ENV_1=${ENVIRONMENTS[0]}
ENV_2=${ENVIRONMENTS[1]}
ENV_3=${ENVIRONMENTS[2]}
ROOM_NAME=${ROOM_NAME}
PHYSICAL_ADDRESS=${PHYSICAL_ADDRESS}
COMPANY_NAME=${COMPANY_NAME}
EOF
        
        echo -e "HTTP/1.1 302 Found\r"
        echo -e "Location: /admin?success=2\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    elif [[ "$path" == "/admin/save_host" ]]; then
        local room address company
        room=$(decode_val "$(echo "$query" | grep -oE 'room=[^&]*' | cut -d= -f2 || true)")
        address=$(decode_val "$(echo "$query" | grep -oE 'address=[^&]*' | cut -d= -f2 || true)")
        company=$(decode_val "$(echo "$query" | grep -oE 'company=[^&]*' | cut -d= -f2 || true)")
        
        [[ -z "$room" ]] && room="Server Room B"
        [[ -z "$address" ]] && address="456 Enterprise Way"
        [[ -z "$company" ]] && company="General Corp"
        
        cat <<EOF > "${SETTINGS_FILE}"
PING_COUNT=${PING_COUNT}
PING_INTERVAL=${PING_INTERVAL}
SWEEP_FREQUENCY=${SWEEP_FREQUENCY}
ENV_1=${ENVIRONMENTS[0]}
ENV_2=${ENVIRONMENTS[1]}
ENV_3=${ENVIRONMENTS[2]}
ROOM_NAME=${room}
PHYSICAL_ADDRESS=${address}
COMPANY_NAME=${company}
EOF
        
        echo -e "HTTP/1.1 302 Found\r"
        echo -e "Location: /admin?success=5\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    elif [[ "$path" == "/admin/add_type" ]]; then
        local new_type
        new_type=$(decode_val "$(echo "$query" | grep -oE 'type=[^&]*' | cut -d= -f2 || true)")
        if [[ -n "$new_type" ]]; then
            local found=0
            for t in "${DEVICE_TYPES[@]}"; do
                if [[ "$t" == "$new_type" ]]; then
                    found=1
                    break
                fi
            done
            if [[ $found -eq 0 ]]; then
                echo "$new_type" >> "${DEVICE_TYPES_FILE}"
                load_device_types
            fi
        fi
        
        echo -e "HTTP/1.1 302 Found\r"
        echo -e "Location: /admin?success=3\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    elif [[ "$path" == "/admin/del_type" ]]; then
        local del_type
        del_type=$(decode_val "$(echo "$query" | grep -oE 'type=[^&]*' | cut -d= -f2 || true)")
        if [[ -n "$del_type" ]]; then
            local escaped_type
            escaped_type=$(echo "$del_type" | sed 's/[^^$*.[\]\\]/\\&/g')
            sed -i "/^${escaped_type}$/d" "${DEVICE_TYPES_FILE}"
            load_device_types
        fi
        
        echo -e "HTTP/1.1 302 Found\r"
        echo -e "Location: /admin?success=4\r"
        echo -e "Connection: close\r"
        echo -e "\r"
        return
    fi
    
    local active_env="${ENVIRONMENTS[0]}"
    if [[ -n "$query" ]]; then
        local target_env
        target_env=$(echo "$query" | grep -oE 'env=[^&]*' | cut -d= -f2 || true)
        target_env=$(decode_val "$target_env")
        for e in "${ENVIRONMENTS[@]}"; do
            if [[ "$e" == "$target_env" ]]; then
                active_env="$e"
            fi
        done
    fi
    
    send_html_response "$active_env"
}

# Run Webserver Loop using nc & named pipe FIFO
run_webserver() {
    init_dirs_and_configs
    if [[ -f "${PID_DIR}/web.pid" ]]; then
        local old_pid
        old_pid=$(cat "${PID_DIR}/web.pid" 2>/dev/null || true)
        if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
            echo "Web configuration daemon already running (PID: $old_pid)."
            return
        fi
    fi
    echo $$ > "${PID_DIR}/web.pid"
    
    rm -f "${FIFO_PATH}"
    mkfifo "${FIFO_PATH}"
    
    trap 'rm -f "${FIFO_PATH}" "${PID_DIR}/web.pid"' EXIT SIGINT SIGTERM
    
    while true; do
        # Accept sequentially via nc and pipe responses back
        if ! cat "${FIFO_PATH}" | nc -l -p "${PORT}" 2>/dev/null | handle_http_request > "${FIFO_PATH}"; then
            sleep 0.2
        fi
    done
}

# Get node count for a configuration file
get_node_count() {
    local env="$1"
    local lower_env="${env,,}"
    local file_name="${lower_env// /_}.conf"
    local file_path="${CONFIG_DIR}/${file_name}"
    [[ ! -f "${file_path}" ]] && echo 0 && return
    grep -c '^' "${file_path}" || echo 0
}

# Truncate strings to fit columns
trunc() {
    local str="$1"
    local max_w="$2"
    if [[ ${#str} -gt $max_w ]]; then
        echo "${str:0:$((max_w-3))}..."
    else
        printf "%-${max_w}s" "$str"
    fi
}

# Render terminal TUI grid
redraw_tui() {
    local active_idx="$1"
    local sel_row="$2"
    
    tput cup 0 0
    local cols
    cols=$(tput cols)
    
    # Title Banner
    local title=" TERMINUS - OPERATIONS CONTROL "
    local pad_len=$(( (cols - ${#title}) / 2 ))
    [[ $pad_len -lt 0 ]] && pad_len=0
    printf '%*s' "$pad_len" ""
    echo -e "\e[1;35;48;5;236m${title}\e[0m"
    echo ""
    
    # Tabs layout
    local tabs_str=""
    for i in "${!ENVIRONMENTS[@]}"; do
        local env_name="${ENVIRONMENTS[$i]}"
        if [[ $i -eq $active_idx ]]; then
            tabs_str="${tabs_str} \e[1;32;7m  ${env_name}  \e[0m  "
        else
            tabs_str="${tabs_str} \e[36m[ ${env_name} ]\e[0m  "
        fi
    done
    
    local plain_tabs_len=0
    for env_name in "${ENVIRONMENTS[@]}"; do
        plain_tabs_len=$((plain_tabs_len + ${#env_name} + 6))
    done
    local tab_pad=$(( (cols - plain_tabs_len) / 2 ))
    [[ $tab_pad -lt 0 ]] && tab_pad=0
    printf '%*s' "$tab_pad" ""
    echo -e "${tabs_str}"
    echo ""
    
    # Setup responsive column widths
    local w_id=4
    local w_type=12
    local w_name=18
    local w_addr=22
    local w_stat=10
    local w_lat=12
    local w_dsince=16
    
    if [[ $cols -lt 100 ]]; then
        w_type=10
        w_name=14
        w_addr=16
        w_stat=8
        w_lat=10
        w_dsince=12
    fi
    local total_table_width=$(( w_id + w_type + w_name + w_addr + w_stat + w_lat + w_dsince + 8 ))
    local t_pad=$(( (cols - total_table_width) / 2 ))
    [[ $t_pad -lt 0 ]] && t_pad=0
    local t_pad_str=""
    if [[ $t_pad -gt 0 ]]; then
        t_pad_str=$(printf '%*s' "$t_pad" "")
    fi
    
    # Print Top Border
    echo -n "$t_pad_str"
    printf '┌'
    printf '─%.0s' $(seq 1 $w_id)
    printf '┬'
    printf '─%.0s' $(seq 1 $w_type)
    printf '┬'
    printf '─%.0s' $(seq 1 $w_name)
    printf '┬'
    printf '─%.0s' $(seq 1 $w_addr)
    printf '┬'
    printf '─%.0s' $(seq 1 $w_stat)
    printf '┬'
    printf '─%.0s' $(seq 1 $w_lat)
    printf '┬'
    printf '─%.0s' $(seq 1 $w_dsince)
    printf '┐\n'
    
    # Header Row
    echo -n "$t_pad_str"
    printf '│ %-*s │ %-*s │ %-*s │ %-*s │ %-*s │ %-*s │ %-*s │\n' \
        $((w_id-1)) "ID" $((w_type-1)) "Device Type" $((w_name-1)) "Node Name" $((w_addr-1)) "Target/IP" \
        $((w_stat-1)) "Status" $((w_lat-1)) "Latency" $((w_dsince-1)) "Down Since"
    
    # Header Separator (bottom border of header only)
    echo -n "$t_pad_str"
    printf '└'
    printf '─%.0s' $(seq 1 $w_id)
    printf '┴'
    printf '─%.0s' $(seq 1 $w_type)
    printf '┴'
    printf '─%.0s' $(seq 1 $w_name)
    printf '┴'
    printf '─%.0s' $(seq 1 $w_addr)
    printf '┴'
    printf '─%.0s' $(seq 1 $w_stat)
    printf '┴'
    printf '─%.0s' $(seq 1 $w_lat)
    printf '┴'
    printf '─%.0s' $(seq 1 $w_dsince)
    printf '┘\n'
    
    # Populate Rows from configurations and statuses
    local env_name="${ENVIRONMENTS[$active_idx]}"
    local lower_env_name="${env_name,,}"
    local file_name="${lower_env_name// /_}"
    local conf_file="${CONFIG_DIR}/${file_name}.conf"
    local status_file="${STATUS_DIR}/${file_name}.status"
    
    declare -A statuses=()
    declare -A latencies=()
    declare -A down_sinces=()
    if [[ -f "${status_file}" ]]; then
        while IFS='|' read -r nid stat lat dsince hist || [[ -n "$nid" ]]; do
            [[ -z "$nid" ]] && continue
            statuses["$nid"]="$stat"
            latencies["$nid"]="$lat"
            down_sinces["$nid"]="$dsince"
        done < "${status_file}"
    fi
    
    local idx=0
    local has_rows=0
    
    if [[ -f "${conf_file}" ]]; then
        while IFS='|' read -r nid name addr dev_type fqdn || [[ -n "$nid" ]]; do
            [[ -z "$nid" ]] && continue
            has_rows=1
            local stat="${statuses[$nid]:-PENDING}"
            local lat="${latencies[$nid]:-N/A}"
            local dsince="${down_sinces[$nid]:-}"
            
            local status_color=""
            local status_str=""
            if [[ "$stat" == "UP" ]]; then
                status_color="\e[1;32m"
                status_str="ONLINE"
            elif [[ "$stat" == "DOWN" ]]; then
                status_color="\e[1;31m"
                status_str="ALERT"
            else
                status_color="\e[1;33m"
                status_str="PENDING"
            fi
            
            local r_id
            r_id=$(trunc "$nid" $w_id)
            local r_type
            r_type=$(trunc "${dev_type:-Server}" $w_type)
            local r_name
            r_name=$(trunc "$name" $w_name)
            local r_addr
            r_addr=$(trunc "$addr" $w_addr)
            local r_stat
            r_stat=$(trunc "$status_str" $w_stat)
            local r_lat
            r_lat=$(trunc "$lat" $w_lat)
            local r_dsince
            r_dsince=$(trunc "$dsince" $w_dsince)
            
            # Print row with overlay highlight if selected (no vertical borders)
            if [[ $idx -eq $sel_row ]]; then
                local ptr_pad_str="$t_pad_str"
                if [[ ${#t_pad_str} -gt 2 ]]; then
                    ptr_pad_str="${t_pad_str:0:-2}▶ "
                fi
                echo -n "$ptr_pad_str"
                printf '\e[7m  %-*s   %-*s   %-*s   %-*s   \e[0m%b\e[7m%-*s\e[0m\e[7m   %-*s   %-*s  \e[0m\n' \
                    $((w_id-1)) "$r_id" $((w_type-1)) "$r_type" $((w_name-1)) "$r_name" $((w_addr-1)) "$r_addr" \
                    "$status_color" $((w_stat-1)) "$r_stat" $((w_lat-1)) "$r_lat" $((w_dsince-1)) "$r_dsince"
            else
                echo -n "$t_pad_str"
                printf '  %-*s   %-*s   %-*s   %-*s   %b%-*s\e[0m   %-*s   %-*s  \n' \
                    $((w_id-1)) "$r_id" $((w_type-1)) "$r_type" $((w_name-1)) "$r_name" $((w_addr-1)) "$r_addr" \
                    "$status_color" $((w_stat-1)) "$r_stat" $((w_lat-1)) "$r_lat" $((w_dsince-1)) "$r_dsince"
            fi
            idx=$((idx + 1))
        done < "${conf_file}"
    fi
    
    if [[ $has_rows -eq 0 ]]; then
        echo -n "$t_pad_str"
        local empty_msg="No nodes configured. Press 'A' to add one."
        printf '  %-*s  \n' $((total_table_width - 4)) "$empty_msg"
    fi
    
    echo ""
    
    echo ""
    
    # System Status Bar
    local daemon_status="OFFLINE"
    local web_status="OFFLINE"
    
    local dpid
    dpid=$(cat "${PID_DIR}/daemon.pid" 2>/dev/null || true)
    if [[ -n "$dpid" ]] && kill -0 "$dpid" 2>/dev/null; then
        daemon_status="RUNNING (PID: $dpid)"
    fi
    local wpid
    wpid=$(cat "${PID_DIR}/web.pid" 2>/dev/null || true)
    if [[ -n "$wpid" ]] && kill -0 "$wpid" 2>/dev/null; then
        web_status="RUNNING (PID: $wpid, Port: $PORT)"
    fi
    
    local status_line="Daemon: ${daemon_status}  |  Web Configuration Server: ${web_status}"
    local s_pad=$(( (cols - ${#status_line}) / 2 ))
    [[ $s_pad -lt 0 ]] && s_pad=0
    printf '%*s' "$s_pad" ""
    echo -e "\e[36m${status_line}\e[0m"
    echo ""
    
    # Command Footer Bar
    local footer="[TAB] Switch Env   [▲/▼] Select   [A] Add Node   [D] Delete Node   [R] Sweep Now   [Q] Quit"
    local f_pad=$(( (cols - ${#footer}) / 2 ))
    [[ $f_pad -lt 0 ]] && f_pad=0
    printf '%*s' "$f_pad" ""
    echo -e "\e[1;37;48;5;236m ${footer} \e[0m"
}

# TUI Prompts: Add node
tui_add_node() {
    local env="$1"
    local lines
    lines=$(tput lines)
    
    tput cup   $((lines - 4)) 0
    tput el
    echo -n -e "\e[1;33mAdd Node to ${env}...\e[0m"
    echo ""
    tput el
    echo -n "Enter Node Name: "
    tput cnorm
    local name=""
    read -r name
    
    tput el
    echo -n "Enter IP or Hostname: "
    local addr=""
    read -r addr
    
    tput el
    echo -n "Enter Device Type [Server]: "
    local dev_type=""
    read -r dev_type
    [[ -z "$dev_type" ]] && dev_type="Server"
    tput civis
    
    if [[ -n "$name" || -n "$addr" ]]; then
        add_node "$env" "$name" "$addr" "$dev_type"
    fi
}

# TUI Prompts: Delete selected node
tui_delete_node() {
    local env="$1"
    local sel_row="$2"
    
    local lower_env="${env,,}"
    local file_name="${lower_env// /_}"
    local conf_file="${CONFIG_DIR}/${file_name}.conf"
    
    [[ ! -f "${conf_file}" ]] && return
    
    local target_id=""
    local target_name=""
    local idx=0
    while IFS='|' read -r nid name addr dev_type || [[ -n "$nid" ]]; do
        [[ -z "$nid" ]] && continue
        if [[ $idx -eq $sel_row ]]; then
            target_id="$nid"
            target_name="$name"
            break
        fi
        idx=$((idx + 1))
    done < "${conf_file}"
    
    [[ -z "$target_id" ]] && return
    
    local lines
    lines=$(tput lines)
    tput cup $((lines - 2)) 0
    tput el
    echo -n -e "\e[1;31mDelete Node '${target_name}' (ID: ${target_id})? (y/n): \e[0m"
    tput cnorm
    
    local confirm=""
    read -s -n 1 confirm || true
    tput civis
    
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        delete_node "$env" "$target_id"
    fi
}

# Run instant foreground sweep
tui_sweep_now() {
    local active_idx="$1"
    local env="${ENVIRONMENTS[$active_idx]}"
    
    local lines
    lines=$(tput lines)
    tput cup $((lines - 2)) 0
    tput el
    echo -ne "\e[1;32mSweeping nodes in ${env}... Please wait...\e[0m"
    
    local lower_env="${env,,}"
    local file_name="${lower_env// /_}"
    local conf_file="${CONFIG_DIR}/${file_name}.conf"
    local status_file="${STATUS_DIR}/${file_name}.status"
    local tmp_status_file="${status_file}.tmp"
    
    [[ ! -f "${conf_file}" ]] && return
    
    declare -A prev_status=()
    declare -A prev_down_since=()
    declare -A prev_history=()
    if [[ -f "${status_file}" ]]; then
        while IFS='|' read -r nid stat lat dsince hist || [[ -n "$nid" ]]; do
            [[ -z "$nid" ]] && continue
            prev_status["$nid"]="$stat"
            prev_down_since["$nid"]="$dsince"
            prev_history["$nid"]="$hist"
        done < "${status_file}"
    fi
    
    declare -A pids=()
    while IFS='|' read -r nid name addr dev_type fqdn || [[ -n "$nid" ]]; do
        [[ -z "$nid" ]] && continue
        (
            local ping_out
            local prev_h="${prev_history[$nid]:-........................}"
            if [[ ${#prev_h} -lt 24 ]]; then
                local pad_len=$(( 24 - ${#prev_h} ))
                local padding
                padding=$(printf '%*s' "$pad_len" "" | tr ' ' '.')
                prev_h="${padding}${prev_h}"
            fi
            local new_h
            
            if ping_out=$(ping -c "${PING_COUNT:-5}" -i "${PING_INTERVAL:-0.2}" -w $(( PING_COUNT + 2 )) "$addr" 2>&1); then
                local avg_rtt
                avg_rtt=$(echo "$ping_out" | grep '^rtt' | cut -d'=' -f2 | cut -d'/' -f2 | tr -d ' ' || echo "")
                new_h="${prev_h:1}1"
                if [[ -n "$avg_rtt" ]]; then
                    echo "${nid}|UP|${avg_rtt} ms||${new_h}"
                else
                    echo "${nid}|UP|0.0 ms||${new_h}"
                fi
            else
                new_h="${prev_h:1}0"
                local since
                local prev_s="${prev_status[$nid]:-UP}"
                if [[ "$prev_s" == "DOWN" ]]; then
                    since="${prev_down_since[$nid]:-$(date +%H:%M:%S)}"
                else
                    since="$(date +%H:%M:%S)"
                fi
                echo "${nid}|DOWN|N/A|${since}|${new_h}"
            fi
        ) > "/tmp/terminus_ping_${file_name}_${nid}.res" 2>&1 &
        pids["$nid"]=$!
    done < "${conf_file}"
    
    for nid in "${!pids[@]}"; do
        wait "${pids[$nid]}" 2>/dev/null || true
    done
    
    : > "${tmp_status_file}"
    while IFS='|' read -r nid name addr dev_type fqdn || [[ -n "$nid" ]]; do
        [[ -z "$nid" ]] && continue
        local res_file="/tmp/terminus_ping_${file_name}_${nid}.res"
        if [[ -f "${res_file}" ]]; then
            cat "${res_file}" >> "${tmp_status_file}"
            rm -f "${res_file}"
        else
            local prev_h="${prev_history[$nid]:-........................}"
            if [[ ${#prev_h} -lt 24 ]]; then
                local pad_len=$(( 24 - ${#prev_h} ))
                local padding
                padding=$(printf '%*s' "$pad_len" "" | tr ' ' '.')
                prev_h="${padding}${prev_h}"
            fi
            local new_h="${prev_h:1}0"
            echo "${nid}|DOWN|N/A|$(date +%H:%M:%S)|${new_h}" >> "${tmp_status_file}"
        fi
    done < "${conf_file}"
    
    mv "${tmp_status_file}" "${status_file}"
}

# Start TUI Mode loop
run_tui() {
    tput smcup
    tput civis
    clear
    
    local active_tab_idx=0
    local selected_row=0
    
    trap 'clear; redraw_tui "$active_tab_idx" "$selected_row"' SIGWINCH
    
    while true; do
        redraw_tui "$active_tab_idx" "$selected_row"
        
        local key=""
        IFS= read -s -n 1 -t 0.5 key || true
        if [[ "$key" == $'\e' ]]; then
            local next=""
            read -s -n 2 -t 0.1 next || true
            key="$key$next"
        fi
        
        case "$key" in
            $'\t') # Tab key
                active_tab_idx=$(( (active_tab_idx + 1) % ${#ENVIRONMENTS[@]} ))
                selected_row=0
                clear
                ;;
            $'\e[A') # Up Arrow
                if [[ $selected_row -gt 0 ]]; then
                    selected_row=$((selected_row - 1))
                fi
                ;;
            $'\e[B') # Down Arrow
                local max_rows
                max_rows=$(get_node_count "${ENVIRONMENTS[$active_tab_idx]}")
                if [[ $selected_row -lt $((max_rows - 1)) ]]; then
                    selected_row=$((selected_row + 1))
                fi
                ;;
            "a"|"A")
                tui_add_node "${ENVIRONMENTS[$active_tab_idx]}"
                clear
                ;;
            "d"|"D")
                tui_delete_node "${ENVIRONMENTS[$active_tab_idx]}" "$selected_row"
                clear
                ;;
            "r"|"R")
                tui_sweep_now "$active_tab_idx"
                clear
                ;;
            "q"|"Q")
                break
                ;;
        esac
    done
    
    tput rmcup
    tput cnorm
}

# Stop background daemons
stop_background_daemons() {
    local dpid
    dpid=$(cat "${PID_DIR}/daemon.pid" 2>/dev/null || true)
    if [[ -n "$dpid" ]]; then
        kill "$dpid" 2>/dev/null || true
        rm -f "${PID_DIR}/daemon.pid"
        echo "Stopped sweep daemon (PID: $dpid)."
    fi
    local wpid
    wpid=$(cat "${PID_DIR}/web.pid" 2>/dev/null || true)
    if [[ -n "$wpid" ]]; then
        kill "$wpid" 2>/dev/null || true
        rm -f "${PID_DIR}/web.pid"
        echo "Stopped web config server (PID: $wpid)."
    fi
}

# Main CLI parser
if [[ $# -gt 0 ]]; then
    case "$1" in
        --daemon)
            run_daemon
            ;;
        --web)
            run_webserver
            ;;
        --add)
            if [[ $# -lt 4 ]]; then
                echo "Usage: $0 --add <env> <name> <addr>"
                exit 1
            fi
            init_dirs_and_configs
            add_node "$2" "$3" "$4" "${5:-Server}"
            echo "Node added."
            ;;
        --del)
            if [[ $# -lt 3 ]]; then
                echo "Usage: $0 --del <env> <id>"
                exit 1
            fi
            init_dirs_and_configs
            delete_node "$2" "$3"
            echo "Node deleted."
            ;;
        --stop)
            stop_background_daemons
            ;;
        --help|-h)
            echo "TERMINUS - Standalone Network Operations Monitor"
            echo "Usage:"
            echo "  $0                  Start TUI (spawns daemon and web server if not running)"
            echo "  $0 --daemon         Run sweep daemon in foreground"
            echo "  $0 --web            Run web config server in foreground"
            echo "  $0 --add <env> <n> <a> [t] Add a node to an environment"
            echo "  $0 --del <env> <id>  Delete a node by ID from an environment"
            echo "  $0 --stop           Stop background daemon and web server"
            echo "  $0 --help           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Run '$0 --help' for usage."
            exit 1
            ;;
    esac
    exit 0
fi

# Default: Initialize and start background daemons if not running, then start TUI
init_dirs_and_configs

# Start sweep daemon in background
start_d=0
if [[ -f "${PID_DIR}/daemon.pid" ]]; then
    dpid=$(cat "${PID_DIR}/daemon.pid" 2>/dev/null || true)
    if [[ -z "$dpid" ]] || ! kill -0 "$dpid" 2>/dev/null; then
        start_d=1
    fi
else
    start_d=1
fi
if [[ $start_d -eq 1 ]]; then
    # Use standard background execution
    "$0" --daemon >/dev/null 2>&1 &
    sleep 0.2
fi

# Start webserver in background
start_w=0
if [[ -f "${PID_DIR}/web.pid" ]]; then
    wpid=$(cat "${PID_DIR}/web.pid" 2>/dev/null || true)
    if [[ -z "$wpid" ]] || ! kill -0 "$wpid" 2>/dev/null; then
        start_w=1
    fi
else
    start_w=1
fi
if [[ $start_w -eq 1 ]]; then
    "$0" --web >/dev/null 2>&1 &
    sleep 0.2
fi

# Launch TUI
run_tui
