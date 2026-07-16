#!/usr/bin/env bash
# Wedge 400 Switch API Automated Deployment Script
# Strict shell options for safety and reliability
set -euo pipefail

# Configuration defaults (Respects env variables, fallbacks to LAN settings)
DEV_HOST="${DEV_HOST:-webserver@192.168.1.80}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_webserver}"
API_PORT="${API_PORT:-8000}"
API_PATH_PREFIX="${API_PATH_PREFIX:-/projects/wedge-switch-400-api}"

echo "============================================="
echo "Starting Wedge 400 Switch API Deployment"
echo "============================================="

# 1. Run local validation checks
echo "[1/6] Running local compile and unit tests..."
./build.sh
.venv/bin/pytest
echo "[✓] Local checks and tests passed successfully."

# 2. Package and Sync files to remote server
echo "[2/6] Syncing files to remote server..."
tar -czf /tmp/wedge_switch_api.tar.gz pyproject.toml src/

ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mkdir -p /home/webserver/wedge400-api && sudo chown -R webserver:webserver /home/webserver/wedge400-api"
scp -i "${SSH_KEY}" /tmp/wedge_switch_api.tar.gz "${DEV_HOST}":/tmp/

ssh -i "${SSH_KEY}" "${DEV_HOST}" "
  cd /home/webserver/wedge400-api &&
  tar -xzf /tmp/wedge_switch_api.tar.gz &&
  rm -f /tmp/wedge_switch_api.tar.gz
"
rm -f /tmp/wedge_switch_api.tar.gz
echo "[✓] Source files synchronized."

# 3. Setup virtual environment and dependencies on remote server
echo "[3/6] Configuring remote virtual environment..."
ssh -i "${SSH_KEY}" "${DEV_HOST}" "
  cd /home/webserver/wedge400-api &&
  python3 -m venv .venv &&
  .venv/bin/pip install --upgrade pip &&
  .venv/bin/pip install .
"
echo "[✓] Remote dependencies installed."

# 4. Provision Basic Authentication credentials
echo "[4/6] Checking Nginx Basic Authentication..."
if ! ssh -i "${SSH_KEY}" "${DEV_HOST}" "[ -f /etc/nginx/.wedge_htpasswd ]"; then
    echo "[!] Remote htpasswd file /etc/nginx/.wedge_htpasswd not found."
    
    # Read admin username
    if [[ -z "${WEDGE_ADMIN_USER:-}" ]]; then
        read -p "Enter username for Wedge Switch API Access [admin]: " WEDGE_ADMIN_USER
        WEDGE_ADMIN_USER="${WEDGE_ADMIN_USER:-admin}"
    fi
    
    # Read admin password
    if [[ -z "${WEDGE_ADMIN_PASS:-}" ]]; then
        read -s -p "Enter password for Wedge Switch API Access [admin]: " WEDGE_ADMIN_PASS
        echo ""
        WEDGE_ADMIN_PASS="${WEDGE_ADMIN_PASS:-admin}"
    fi
    
    # Generate hash locally using openssl
    local_hash=$(openssl passwd -apr1 "${WEDGE_ADMIN_PASS}")
    echo "${WEDGE_ADMIN_USER}:${local_hash}" > /tmp/wedge_htpasswd_local
    
    # Copy to remote and move to destination
    scp -i "${SSH_KEY}" /tmp/wedge_htpasswd_local "${DEV_HOST}":/tmp/.wedge_htpasswd
    ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mv /tmp/.wedge_htpasswd /etc/nginx/.wedge_htpasswd && sudo chown root:www-data /etc/nginx/.wedge_htpasswd && sudo chmod 640 /etc/nginx/.wedge_htpasswd"
    rm -f /tmp/wedge_htpasswd_local
    echo "[+] Secure htpasswd file created successfully."
else
    echo "[+] Remote htpasswd file already exists. Skipping credentials generation."
fi

# 5. Inject Nginx configuration block safely
echo "[5/6] Injecting Nginx configuration location block..."

# Write the python injector script locally
cat <<'EOF' > /tmp/nginx_injector_local.py
import re
import sys

nginx_config_path = "/etc/nginx/sites-available/default"
with open(nginx_config_path, "r") as f:
    content = f.read()

# 1. Clean out any pre-existing Wedge API location blocks to prevent duplicates/conflicts
clean_content = re.sub(
    r"\s*# Wedge 400 Switch API.*?(?=location / {)",
    "\n",
    content,
    flags=re.DOTALL
)
clean_content = re.sub(
    r"\s*location\s+~?\s*\"?\^?/projects/wedge-switch-400-api.*?\n\s*}\s*\n",
    "\n",
    clean_content,
    flags=re.DOTALL
)

target_block = """
    # Wedge 400 Switch API Swagger docs block (protected by Nginx Basic Auth)
    location ~ ^/projects/wedge-switch-400-api/(docs|openapi.json) {
        auth_basic "Wedge 400 Switch Control Docs";
        auth_basic_user_file /etc/nginx/.wedge_htpasswd;
        rewrite ^/projects/wedge-switch-400-api/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }

    # Wedge 400 Switch API Console and APIs (secured by App-level AD Auth)
    location /projects/wedge-switch-400-api {
        auth_basic off;
        rewrite ^/projects/wedge-switch-400-api/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
"""

idx = clean_content.find("location / {")
if idx != -1:
    updated_content = clean_content[:idx] + target_block + "\n" + clean_content[idx:]
    with open(nginx_config_path, "w") as f:
        f.write(updated_content)
    print("Successfully injected and updated Nginx location blocks for Wedge 400 API.")
else:
    print("Error: Could not locate 'location / {' block in Nginx config.")
    sys.exit(1)
EOF

# Copy to remote and execute
scp -i "${SSH_KEY}" /tmp/nginx_injector_local.py "${DEV_HOST}":/tmp/nginx_injector.py
rm -f /tmp/nginx_injector_local.py

ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo python3 /tmp/nginx_injector.py && rm -f /tmp/nginx_injector.py"
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo nginx -t && sudo systemctl reload nginx"
echo "[✓] Nginx reloaded."

# 6. Configure Systemd service
echo "[6/6] Provisioning systemd service..."

cat <<EOF > /tmp/wedge400-api.service
[Unit]
Description=Wedge 400 Switch API (FastAPI)
After=network.target

[Service]
Type=simple
User=webserver
WorkingDirectory=/home/webserver/wedge400-api
Environment="API_ROOT_PATH=${API_PATH_PREFIX}"
Environment="SWITCH_PORT_COUNT=16"
Environment="SWITCH_PORT_SPEED=400"
Environment="DATABASE_PATH=/home/webserver/wedge400-api/switch_config.db"
ExecStart=/home/webserver/wedge400-api/.venv/bin/uvicorn fastapi_starter.main:app --host 127.0.0.1 --port ${API_PORT}
Restart=always
RestartSec=10
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

scp -i "${SSH_KEY}" /tmp/wedge400-api.service "${DEV_HOST}":/tmp/
ssh -i "${SSH_KEY}" "${DEV_HOST}" "
  sudo mv /tmp/wedge400-api.service /etc/systemd/system/ &&
  sudo systemctl daemon-reload &&
  sudo systemctl enable wedge400-api &&
  sudo systemctl restart wedge400-api
"
rm -f /tmp/wedge400-api.service

echo "============================================="
echo "Deployment Complete! Wedge 400 API is running."
echo "Access link (requires Basic Auth):"
echo "- Swagger Docs: http://192.168.1.80/projects/wedge-switch-400-api/docs"
echo "============================================="
