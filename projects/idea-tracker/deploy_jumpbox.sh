#!/usr/bin/env bash
# Deploy Idea Forge to jumpbox (ideaforge.extremesarcasm.org).
# Dry-run by default. Pass --apply to execute.
#
# Usage:
#   ./deploy_jumpbox.sh
#   ./deploy_jumpbox.sh --apply
#   IDEA_FORGE_SSH_KEY=~/.ssh/jumpbox.pem ./deploy_jumpbox.sh --apply

set -euo pipefail

APPLY=0
SSH_KEY="${IDEA_FORGE_SSH_KEY:-${SSH_KEY:-$HOME/.ssh/jumpbox.pem}}"
SSH_USER="${IDEA_FORGE_SSH_USER:-ubuntu}"
SSH_HOST="${IDEA_FORGE_SSH_HOST:-jumpbox.extremesarcasm.org}"
PUBLIC_HOST="${IDEA_FORGE_PUBLIC_HOST:-ideaforge.extremesarcasm.org}"
REMOTE_APP_DIR="${IDEA_FORGE_REMOTE_DIR:-/opt/idea-forge}"
REMOTE_DATA_DIR="${IDEA_FORGE_DATA_DIR:-/var/lib/idea-forge}"
REPO_URL="${IDEA_FORGE_REPO_URL:-https://github.com/Richie086/scripts.git}"
REPO_BRANCH="${IDEA_FORGE_BRANCH:-cursor/idea-tracker-1f3c}"
APP_SUBDIR="projects/idea-tracker"

for arg in "$@"; do
  case "$arg" in
    --apply|--force) APPLY=1 ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
  esac
done

log() { printf '[deploy] %s\n' "$*"; }
run() {
  if [[ "$APPLY" -eq 1 ]]; then
    log "+ $*"
    "$@"
  else
    log "DRY-RUN: $*"
  fi
}

SSH=(ssh -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new "${SSH_USER}@${SSH_HOST}")
SCP=(scp -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$SSH_KEY" ]]; then
  log "ERROR: SSH key not found at: $SSH_KEY"
  log "Copy your PEM into this environment, chmod 600, then re-run."
  log "  mkdir -p ~/.ssh && chmod 700 ~/.ssh"
  log "  # copy jumpbox.pem to ~/.ssh/jumpbox.pem"
  log "  chmod 600 ~/.ssh/jumpbox.pem"
  exit 1
fi

log "host=$SSH_HOST user=$SSH_USER public=$PUBLIC_HOST key=$SSH_KEY apply=$APPLY"

if [[ "$APPLY" -eq 0 ]]; then
  log "Dry-run only. Re-run with --apply to deploy."
fi

run "${SSH[@]}" "echo ok && uname -a && python3 --version"

REMOTE_SETUP=$(cat <<EOF
set -euo pipefail
sudo mkdir -p '$REMOTE_APP_DIR' '$REMOTE_DATA_DIR'
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip git nginx
if [[ ! -d '$REMOTE_APP_DIR/repo/.git' ]]; then
  sudo git clone --branch '$REPO_BRANCH' '$REPO_URL' '$REMOTE_APP_DIR/repo'
else
  sudo git -C '$REMOTE_APP_DIR/repo' fetch origin
  sudo git -C '$REMOTE_APP_DIR/repo' checkout '$REPO_BRANCH'
  sudo git -C '$REMOTE_APP_DIR/repo' pull --ff-only origin '$REPO_BRANCH' || true
fi
sudo python3 -m venv '$REMOTE_APP_DIR/venv'
sudo '$REMOTE_APP_DIR/venv/bin/pip' install --upgrade pip
sudo '$REMOTE_APP_DIR/venv/bin/pip' install -r '$REMOTE_APP_DIR/repo/$APP_SUBDIR/requirements.txt' gunicorn
sudo mkdir -p /etc/idea-forge
if [[ ! -f /etc/idea-forge/env ]]; then
  SECRET=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
  ADMIN_PW=\$(python3 -c 'import secrets; print(secrets.token_urlsafe(12))')
  sudo tee /etc/idea-forge/env >/dev/null <<ENV
SEEDBANK_HOST=127.0.0.1
SEEDBANK_PORT=5050
SEEDBANK_PUBLIC_HOST=$PUBLIC_HOST
SEEDBANK_DATA=$REMOTE_DATA_DIR
SEEDBANK_SSH=0
SEEDBANK_DEBUG=0
SEEDBANK_SECRET=\$SECRET
SEEDBANK_ADMIN_PASSWORD=\$ADMIN_PW
ENV
  sudo chmod 600 /etc/idea-forge/env
  echo "WROTE_NEW_ENV admin_password=\$ADMIN_PW"
else
  echo "KEEPING_EXISTING_ENV"
fi
sudo chown -R www-data:www-data '$REMOTE_DATA_DIR' || sudo chown -R ubuntu:ubuntu '$REMOTE_DATA_DIR'
EOF
)

if [[ "$APPLY" -eq 1 ]]; then
  log "Running remote bootstrap…"
  "${SSH[@]}" "bash -s" <<<"$REMOTE_SETUP"
else
  log "DRY-RUN: would run remote bootstrap (apt, clone, venv, env file)"
fi

run "${SCP[@]}" "$SCRIPT_DIR/idea-forge.service" "${SSH_USER}@${SSH_HOST}:/tmp/idea-forge.service"
run "${SCP[@]}" "$SCRIPT_DIR/nginx-ideaforge.conf" "${SSH_USER}@${SSH_HOST}:/tmp/nginx-ideaforge.conf"

REMOTE_ENABLE=$(cat <<EOF
set -euo pipefail
sudo cp /tmp/idea-forge.service /etc/systemd/system/idea-forge.service
sudo sed -i 's|__REMOTE_APP_DIR__|$REMOTE_APP_DIR|g' /etc/systemd/system/idea-forge.service
sudo sed -i 's|__APP_SUBDIR__|$APP_SUBDIR|g' /etc/systemd/system/idea-forge.service
sudo systemctl daemon-reload
sudo systemctl enable idea-forge
sudo systemctl restart idea-forge
sudo cp /tmp/nginx-ideaforge.conf /etc/nginx/sites-available/ideaforge
sudo sed -i 's|__PUBLIC_HOST__|$PUBLIC_HOST|g' /etc/nginx/sites-available/ideaforge
sudo ln -sfn /etc/nginx/sites-available/ideaforge /etc/nginx/sites-enabled/ideaforge
sudo nginx -t
sudo systemctl reload nginx
if ! sudo test -f /etc/letsencrypt/live/$PUBLIC_HOST/fullchain.pem; then
  sudo apt-get install -y certbot python3-certbot-nginx
  sudo certbot --nginx -d '$PUBLIC_HOST' --non-interactive --agree-tos --register-unsafely-without-email || true
fi
sudo systemctl status idea-forge --no-pager | head -20
curl -s -o /dev/null -w 'local_app=%{http_code}\n' http://127.0.0.1:5050/ || true
curl -s -o /dev/null -w 'public_http=%{http_code}\n' http://$PUBLIC_HOST/ || true
curl -s -o /dev/null -w 'public_https=%{http_code}\n' https://$PUBLIC_HOST/ || true
EOF
)

if [[ "$APPLY" -eq 1 ]]; then
  log "Enabling systemd + nginx…"
  "${SSH[@]}" "bash -s" <<<"$REMOTE_ENABLE"
  log "Done. Open https://$PUBLIC_HOST/"
  log "Initial admin password is in /etc/idea-forge/env on the server (SEEDBANK_ADMIN_PASSWORD) if newly created."
else
  log "DRY-RUN: would install systemd unit, nginx site, certbot, restart services"
fi
