#!/bin/bash
# NETMON V3 Automated Deployment Script
# Strict shell options for safety and reliability
set -euo pipefail

# Configuration defaults (Respects env variables, fallbacks to LAN settings)
DEV_HOST="${DEV_HOST:-webserver@192.168.1.80}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_webserver}"
NETMON_PORT="${NETMON_PORT:-8085}"

echo "============================================="
echo "Starting Netmon V3 Deployment on ${DEV_HOST}"
echo "============================================="

# 1. Compile locally with relaxed security flag (-r)
echo "[1/6] Compiling local netmon.sh..."
shc -r -f netmon.sh -o netmon

# 2. Ensure target folders exist on remote server
echo "[2/6] Setting up remote target directory..."
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mkdir -p /home/webserver/netmon && sudo chown -R webserver:webserver /home/webserver/netmon"

# 3. Transfer source and compiled C files
echo "[3/6] Syncing files to remote server..."
scp -i "${SSH_KEY}" netmon.sh netmon.sh.x.c "${DEV_HOST}":/home/webserver/netmon/

# 4. Compile directly on remote server to bypass yama/ptrace_scope restrictions
echo "[4/6] Compiling binary on remote host..."
ssh -i "${SSH_KEY}" "${DEV_HOST}" "gcc -O2 /home/webserver/netmon/netmon.sh.x.c -o /home/webserver/netmon/netmon && chmod +x /home/webserver/netmon/netmon"

# 5. Provision credentials and Nginx configuration
echo "[5/6] Configuring Nginx reverse proxy..."

# Check if htpasswd file exists on target server
if ! ssh -i "${SSH_KEY}" "${DEV_HOST}" "[ -f /etc/nginx/.netmon_htpasswd ]"; then
    echo "[!] Remote htpasswd file /etc/nginx/.netmon_htpasswd not found."
    
    # Read admin username
    if [[ -z "${NETMON_ADMIN_USER:-}" ]]; then
        read -p "Enter username for Netmon Admin Dashboard: " NETMON_ADMIN_USER
    fi
    
    # Read admin password
    if [[ -z "${NETMON_ADMIN_PASS:-}" ]]; then
        read -s -p "Enter password for Netmon Admin Dashboard: " NETMON_ADMIN_PASS
        echo ""
    fi
    
    # Generate hash locally using openssl
    local_hash=$(openssl passwd -apr1 "${NETMON_ADMIN_PASS}")
    echo "${NETMON_ADMIN_USER}:${local_hash}" > /tmp/netmon_htpasswd_local
    
    # Copy to remote /tmp and move to destination
    scp -i "${SSH_KEY}" /tmp/netmon_htpasswd_local "${DEV_HOST}":/tmp/.netmon_htpasswd
    ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mv /tmp/.netmon_htpasswd /etc/nginx/.netmon_htpasswd && sudo chown root:www-data /etc/nginx/.netmon_htpasswd && sudo chmod 640 /etc/nginx/.netmon_htpasswd"
    rm -f /tmp/netmon_htpasswd_local
    echo "[+] Secure htpasswd file created successfully."
else
    echo "[+] Remote htpasswd file already exists. Skipping credentials generation."
fi

# Write config locally first to avoid shell expansion issues
cat <<EOF > /tmp/nginx_netmon_default
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    # Secure admin routes
    location ~ ^/(admin|delete|add) {
        auth_basic "Netmon Admin Settings";
        auth_basic_user_file /etc/nginx/.netmon_htpasswd;
        
        proxy_pass http://127.0.0.1:${NETMON_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # Public operations dashboard
    location / {
        proxy_pass http://127.0.0.1:${NETMON_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    location /nginx_status_raw {
        stub_status on;
        access_log off;
        allow 127.0.0.1;
        deny all;
    }
}
EOF

scp -i "${SSH_KEY}" /tmp/nginx_netmon_default "${DEV_HOST}":/tmp/nginx_netmon_default
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo cp /tmp/nginx_netmon_default /etc/nginx/sites-available/default && sudo nginx -t && sudo systemctl reload nginx"
rm -f /tmp/nginx_netmon_default

# 6. Configure and enable systemd service files
echo "[6/6] Setting up Systemd services..."
cat <<EOF > /tmp/netmon-daemon.service
[Unit]
Description=Netmon V3 Parallel Sweep Daemon
After=network.target

[Service]
Type=simple
User=webserver
ExecStart=/home/webserver/netmon/netmon --daemon
Restart=always
RestartSec=10
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > /tmp/netmon-web.service
[Unit]
Description=Netmon V3 HTTP Configuration Server
After=network.target

[Service]
Type=simple
User=webserver
Environment="NETMON_PORT=${NETMON_PORT}"
ExecStart=/home/webserver/netmon/netmon --web
Restart=always
RestartSec=10
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

scp -i "${SSH_KEY}" /tmp/netmon-daemon.service /tmp/netmon-web.service "${DEV_HOST}":/tmp/
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo cp /tmp/netmon-daemon.service /tmp/netmon-web.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable netmon-daemon netmon-web && sudo systemctl restart netmon-daemon netmon-web"
rm -f /tmp/netmon-daemon.service /tmp/netmon-web.service

# Clean up temp remote files
ssh -i "${SSH_KEY}" "${DEV_HOST}" "rm -f /tmp/netmon-daemon.service /tmp/netmon-web.service /tmp/nginx_netmon_default"

echo "============================================="
echo "Deployment Complete! Netmon V3 is running."
echo "Access links:"
echo "- Web UI: http://192.168.1.80/"
echo "- Nginx Status: http://192.168.1.80/nginx_status"
echo "============================================="
