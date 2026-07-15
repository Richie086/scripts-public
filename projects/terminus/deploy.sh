#!/usr/bin/env bash
# TERMINUS Automated Deployment Script (Pure Python 3)
# Strict shell options for safety and reliability
set -euo pipefail

# Configuration defaults (Respects env variables, fallbacks to LAN settings)
DEV_HOST="${DEV_HOST:-webserver@192.168.1.80}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_webserver}"
TERMINUS_PORT="${TERMINUS_PORT:-8085}"

echo "============================================="
echo "Starting Terminus Deployment on ${DEV_HOST}"
echo "============================================="

# 1. Validate python script locally
echo "[1/5] Validating local terminus.py..."
./build.sh

# 2. Ensure target folders exist on remote server
echo "[2/5] Setting up remote target directory..."
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mkdir -p /home/webserver/terminus && sudo chown -R webserver:webserver /home/webserver/terminus"

# 3. Transfer source python script
echo "[3/5] Syncing files to remote server..."
scp -i "${SSH_KEY}" terminus.py "${DEV_HOST}":/home/webserver/terminus/
ssh -i "${SSH_KEY}" "${DEV_HOST}" "chmod +x /home/webserver/terminus/terminus.py"

# Clean up legacy compiled binaries and old files on remote
echo "Cleaning up legacy compiled C binary and shell files on remote..."
ssh -i "${SSH_KEY}" "${DEV_HOST}" "rm -f /home/webserver/terminus/terminus /home/webserver/terminus/terminus.sh /home/webserver/terminus/terminus.sh.x.c /home/webserver/terminus/config_manager.py" || true

# 4. Provision credentials and Nginx configuration
echo "[4/5] Configuring Nginx reverse proxy..."

# Check if htpasswd file exists on target server
if ! ssh -i "${SSH_KEY}" "${DEV_HOST}" "[ -f /etc/nginx/.terminus_htpasswd ]"; then
    echo "[!] Remote htpasswd file /etc/nginx/.terminus_htpasswd not found."
    
    # Read admin username
    if [[ -z "${TERMINUS_ADMIN_USER:-}" ]]; then
        read -p "Enter username for Terminus Admin Dashboard [admin]: " TERMINUS_ADMIN_USER
        TERMINUS_ADMIN_USER="${TERMINUS_ADMIN_USER:-admin}"
    fi
    
    # Read admin password
    if [[ -z "${TERMINUS_ADMIN_PASS:-}" ]]; then
        read -s -p "Enter password for Terminus Admin Dashboard [admin]: " TERMINUS_ADMIN_PASS
        echo ""
        TERMINUS_ADMIN_PASS="${TERMINUS_ADMIN_PASS:-admin}"
    fi
    
    # Generate hash locally using openssl
    local_hash=$(openssl passwd -apr1 "${TERMINUS_ADMIN_PASS}")
    echo "${TERMINUS_ADMIN_USER}:${local_hash}" > /tmp/terminus_htpasswd_local
    
    # Copy to remote /tmp and move to destination
    scp -i "${SSH_KEY}" /tmp/terminus_htpasswd_local "${DEV_HOST}":/tmp/.terminus_htpasswd
    ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mv /tmp/.terminus_htpasswd /etc/nginx/.terminus_htpasswd && sudo chown root:www-data /etc/nginx/.terminus_htpasswd && sudo chmod 640 /etc/nginx/.terminus_htpasswd"
    rm -f /tmp/terminus_htpasswd_local
    echo "[+] Secure htpasswd file created successfully."
else
    echo "[+] Remote htpasswd file already exists. Skipping credentials generation."
fi

# Write config locally first to avoid shell expansion issues
cat <<EOF > /tmp/nginx_terminus_default
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    # Secure admin routes
    location ~ ^/(admin|delete|add) {
        auth_basic "Terminus Admin Settings";
        auth_basic_user_file /etc/nginx/.terminus_htpasswd;
        
        proxy_pass http://127.0.0.1:${TERMINUS_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }

    # Public operations dashboard
    location / {
        proxy_pass http://127.0.0.1:${TERMINUS_PORT};
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

scp -i "${SSH_KEY}" /tmp/nginx_terminus_default "${DEV_HOST}":/tmp/nginx_terminus_default
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo cp /tmp/nginx_terminus_default /etc/nginx/sites-available/default && sudo nginx -t && sudo systemctl reload nginx"
rm -f /tmp/nginx_terminus_default

# 5. Configure and enable systemd service files
echo "[5/5] Setting up Systemd services..."

cat <<EOF > /tmp/terminus-daemon.service
[Unit]
Description=Terminus Parallel Sweep Daemon (Python)
After=network.target

[Service]
Type=simple
User=webserver
ExecStart=/usr/bin/python3 /home/webserver/terminus/terminus.py --daemon
Restart=always
RestartSec=10
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > /tmp/terminus-web.service
[Unit]
Description=Terminus HTTP Configuration Server (Python)
After=network.target

[Service]
Type=simple
User=webserver
Environment="TERMINUS_PORT=${TERMINUS_PORT}"
ExecStart=/usr/bin/python3 /home/webserver/terminus/terminus.py --web
Restart=always
RestartSec=10
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

scp -i "${SSH_KEY}" /tmp/terminus-daemon.service /tmp/terminus-web.service "${DEV_HOST}":/tmp/
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo cp /tmp/terminus-daemon.service /tmp/terminus-web.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable terminus-daemon terminus-web && sudo systemctl restart terminus-daemon terminus-web"
rm -f /tmp/terminus-daemon.service /tmp/terminus-web.service

# Clean up temp remote files
ssh -i "${SSH_KEY}" "${DEV_HOST}" "rm -f /tmp/terminus-daemon.service /tmp/terminus-web.service /tmp/nginx_terminus_default"

echo "============================================="
echo "Deployment Complete! Terminus is running under Python 3."
echo "Access links:"
echo "- Web UI: http://192.168.1.80/"
echo "- Nginx Status: http://192.168.1.80/nginx_status"
echo "============================================="
