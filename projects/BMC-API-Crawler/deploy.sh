#!/usr/bin/env bash
# Standalone BMC API Crawler Automated Deployment Script
set -euo pipefail

DEV_HOST="${DEV_HOST:-webserver@192.168.1.80}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_webserver}"
CRAWLER_PORT="${CRAWLER_PORT:-8001}"
CRAWLER_PATH_PREFIX="${CRAWLER_PATH_PREFIX:-/projects/bmc-api-crawler}"

echo "============================================="
echo "Starting BMC API Crawler Deployment"
echo "============================================="

# 1. Run local compile and tests
echo "[1/6] Running local validations and tests..."
./build.sh
.venv/bin/pytest
echo "[✓] Local checks and tests passed successfully."

# 2. Package and Sync files to remote server
echo "[2/6] Syncing files to remote server..."
tar -czf /tmp/bmc_api_crawler.tar.gz pyproject.toml src/ tests/

ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mkdir -p /home/webserver/bmc-crawler && sudo chown -R webserver:webserver /home/webserver/bmc-crawler"
scp -i "${SSH_KEY}" /tmp/bmc_api_crawler.tar.gz "${DEV_HOST}":/tmp/

ssh -i "${SSH_KEY}" "${DEV_HOST}" "
  cd /home/webserver/bmc-crawler &&
  tar -xzf /tmp/bmc_api_crawler.tar.gz &&
  rm -f /tmp/bmc_api_crawler.tar.gz
"
rm -f /tmp/bmc_api_crawler.tar.gz
echo "[✓] Source files synchronized."

# 3. Setup virtual environment and dependencies on remote server
echo "[3/6] Configuring remote virtual environment..."
ssh -i "${SSH_KEY}" "${DEV_HOST}" "
  cd /home/webserver/bmc-crawler &&
  python3 -m venv .venv &&
  .venv/bin/pip install --upgrade pip &&
  .venv/bin/pip install .
"
echo "[✓] Remote dependencies installed."

# 4. Check Basic Auth (Reuses existing wedge htpasswd file)
echo "[4/6] Checking Nginx Basic Authentication..."
if ! ssh -i "${SSH_KEY}" "${DEV_HOST}" "[ -f /etc/nginx/.wedge_htpasswd ]"; then
    echo "[!] Remote htpasswd /etc/nginx/.wedge_htpasswd not found. Generating defaults (admin:admin)..."
    local_hash=$(openssl passwd -apr1 "admin")
    echo "admin:${local_hash}" > /tmp/wedge_htpasswd_local
    scp -i "${SSH_KEY}" /tmp/wedge_htpasswd_local "${DEV_HOST}":/tmp/.wedge_htpasswd
    ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo mv /tmp/.wedge_htpasswd /etc/nginx/.wedge_htpasswd && sudo chown root:www-data /etc/nginx/.wedge_htpasswd && sudo chmod 640 /etc/nginx/.wedge_htpasswd"
    rm -f /tmp/wedge_htpasswd_local
fi
echo "[+] Secure htpasswd verified."

# 5. Inject Nginx configuration block safely
echo "[5/6] Injecting Nginx configuration location block..."

cat <<'EOF' > /tmp/nginx_crawler_injector_local.py
import sys

nginx_config_path = "/etc/nginx/sites-available/default"
with open(nginx_config_path, "r") as f:
    content = f.read()

target_block = """
    # BMC API Crawler location block
    location /projects/bmc-api-crawler {
        auth_basic "BMC API Ingestion Control";
        auth_basic_user_file /etc/nginx/.wedge_htpasswd;
        rewrite ^/projects/bmc-api-crawler/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
"""

if "/projects/bmc-api-crawler" not in content:
    idx = content.find("location / {")
    if idx != -1:
        updated_content = content[:idx] + target_block + "\n" + content[idx:]
        with open(nginx_config_path, "w") as f:
            f.write(updated_content)
        print("Successfully injected Nginx location block for BMC API Crawler.")
    else:
        print("Error: Could not locate 'location / {' block in Nginx config.")
        sys.exit(1)
else:
    print("Nginx location block for BMC API Crawler already exists. Skipping injection.")
EOF

scp -i "${SSH_KEY}" /tmp/nginx_crawler_injector_local.py "${DEV_HOST}":/tmp/nginx_crawler_injector.py
rm -f /tmp/nginx_crawler_injector_local.py

ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo python3 /tmp/nginx_crawler_injector.py && rm -f /tmp/nginx_crawler_injector.py"
ssh -i "${SSH_KEY}" "${DEV_HOST}" "sudo nginx -t && sudo systemctl reload nginx"
echo "[✓] Nginx reloaded."

# 6. Configure Systemd service
echo "[6/6] Provisioning systemd service..."

cat <<EOF > /tmp/bmc-crawler.service
[Unit]
Description=BMC API Crawler (FastAPI)
After=network.target

[Service]
Type=simple
User=webserver
WorkingDirectory=/home/webserver/bmc-crawler
Environment="API_ROOT_PATH=${CRAWLER_PATH_PREFIX}"
Environment="SWITCH_API_URL=http://127.0.0.1:8000/projects/wedge-switch-400-api"
ExecStart=/home/webserver/bmc-crawler/.venv/bin/uvicorn crawler.main:app --host 127.0.0.1 --port ${CRAWLER_PORT}
Restart=always
RestartSec=10
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

scp -i "${SSH_KEY}" /tmp/bmc-crawler.service "${DEV_HOST}":/tmp/
ssh -i "${SSH_KEY}" "${DEV_HOST}" "
  sudo mv /tmp/bmc-crawler.service /etc/systemd/system/ &&
  sudo systemctl daemon-reload &&
  sudo systemctl enable bmc-crawler &&
  sudo systemctl restart bmc-crawler
"
rm -f /tmp/bmc-crawler.service

echo "============================================="
echo "Deployment Complete! BMC API Crawler is running."
echo "Access link (requires Basic Auth):"
echo "- Crawler Console: http://192.168.1.80/projects/bmc-api-crawler"
echo "============================================="
