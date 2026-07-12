#!/usr/bin/env bash
#
# deploy-postfix-mailserver.sh
#
# Automates deployment of a Postfix-based mail server on Debian 13 (trixie),
# using Dovecot for SASL auth and IMAP. Also sets up TLS (self-signed or
# Let's Encrypt), OpenDKIM signing, and UFW firewall rules.
#
# Every value the script needs (domain, hostname, admin email, and the
# Let's Encrypt/IMAP/DKIM choices) can be passed as a flag. Anything you
# don't pass, it will STOP and prompt you for interactively before
# continuing — nothing is silently assumed unless you pass --non-interactive,
# in which case sane defaults are used for the yes/no options (required
# values still cause it to fail rather than guess).
#
# Usage:
#   sudo ./deploy-postfix-mailserver.sh
#     (fully interactive — prompts for every value)
#
#   sudo ./deploy-postfix-mailserver.sh --domain example.com --hostname mail.example.com --admin-email postmaster@example.com
#     (pre-fills those three; still prompts for Let's Encrypt/IMAP/DKIM choices)
#
# Flags:
#   --domain <domain>          Mail domain (e.g. example.com)
#   --hostname <fqdn>           Mail server FQDN (e.g. mail.example.com)
#   --admin-email <email>       Postmaster/admin contact address
#   --letsencrypt                Obtain a Let's Encrypt cert via certbot (needs port 80
#                                reachable and DNS already pointed at this host)
#   --no-imap                    Skip Dovecot IMAP (SASL-only, for relay/submission use)
#   --no-dkim                    Skip OpenDKIM setup
#   --non-interactive             Never prompt; use defaults for anything not passed as
#                                a flag (fails if domain/hostname/admin-email are missing)
#   -h | --help                  Show this help text
#
# Idempotent-ish: safe to re-run; it will skip package installs already
# satisfied and overwrite config files it manages (with a timestamped
# backup of anything it replaces).

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults / flag parsing
# ---------------------------------------------------------------------------
MAIL_DOMAIN=""
MAIL_HOSTNAME=""
ADMIN_EMAIL=""
USE_LETSENCRYPT=""
ENABLE_IMAP=""
ENABLE_DKIM=""
NON_INTERACTIVE=0

usage() { sed -n '2,37p' "$0" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain) MAIL_DOMAIN="$2"; shift 2 ;;
    --hostname) MAIL_HOSTNAME="$2"; shift 2 ;;
    --admin-email) ADMIN_EMAIL="$2"; shift 2 ;;
    --letsencrypt) USE_LETSENCRYPT=1; shift ;;
    --no-imap) ENABLE_IMAP=0; shift ;;
    --no-dkim) ENABLE_DKIM=0; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1"; usage; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log()  { echo -e "\033[1;32m[+]\033[0m $*"; }
warn() { echo -e "\033[1;33m[!]\033[0m $*"; }
die()  { echo -e "\033[1;31m[x]\033[0m $*" >&2; exit 1; }

backup_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    cp -a "$f" "${f}.bak.$(date +%Y%m%d%H%M%S)"
  fi
}

prompt_if_missing() {
  local varname="$1" promptText="$2"
  local current="${!varname}"
  if [[ -z "$current" ]]; then
    if [[ "$NON_INTERACTIVE" -eq 1 ]]; then
      die "Missing required value for --${varname,,} and --non-interactive was set."
    fi
    read -rp "$promptText: " value
    printf -v "$varname" '%s' "$value"
  fi
}

# For values not passed as a flag, stop and prompt for a yes/no answer
# instead of silently assuming a default. If --non-interactive is set and
# the value wasn't passed via flag, fall back to the given default.
prompt_yes_no() {
  local varname="$1" promptText="$2" default="$3" # default: "y" or "n"
  local current="${!varname}"
  if [[ -n "$current" ]]; then
    return # already explicitly set via a CLI flag — don't re-prompt
  fi
  if [[ "$NON_INTERACTIVE" -eq 1 ]]; then
    printf -v "$varname" '%s' "$( [[ "$default" == "y" ]] && echo 1 || echo 0 )"
    return
  fi
  local hint ans
  hint=$([[ "$default" == "y" ]] && echo "Y/n" || echo "y/N")
  read -rp "$promptText [$hint]: " ans
  ans="${ans:-$default}"
  if [[ "$ans" =~ ^[Yy] ]]; then
    printf -v "$varname" '%s' 1
  else
    printf -v "$varname" '%s' 0
  fi
}

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
[[ $EUID -eq 0 ]] || die "This script must be run as root (sudo)."

if [[ -f /etc/os-release ]]; then
  . /etc/os-release
  if [[ "${ID:-}" != "debian" ]]; then
    warn "This script targets Debian 13 (trixie); detected ID=${ID:-unknown}. Continuing anyway."
  elif [[ "${VERSION_ID:-}" != "13" && "${VERSION_CODENAME:-}" != "trixie" ]]; then
    warn "Detected Debian version ${VERSION_ID:-unknown}, not 13/trixie. Continuing anyway."
  fi
else
  warn "Could not detect OS release info. Continuing anyway."
fi

prompt_if_missing MAIL_DOMAIN   "Mail domain (e.g. example.com)"
prompt_if_missing MAIL_HOSTNAME "Mail server FQDN (e.g. mail.example.com)"
prompt_if_missing ADMIN_EMAIL   "Admin/postmaster email address"

prompt_yes_no USE_LETSENCRYPT "Obtain a Let's Encrypt certificate now? (requires DNS for $MAIL_HOSTNAME already pointed here and port 80 reachable — otherwise a self-signed cert is used)" "n"
prompt_yes_no ENABLE_IMAP     "Enable Dovecot IMAP (143/993) for end-user mail access, not just SASL relay auth?" "y"
prompt_yes_no ENABLE_DKIM     "Set up OpenDKIM signing (recommended for deliverability)?" "y"

log "Domain:        $MAIL_DOMAIN"
log "Hostname:      $MAIL_HOSTNAME"
log "Admin email:   $ADMIN_EMAIL"
log "Let's Encrypt: $([[ $USE_LETSENCRYPT -eq 1 ]] && echo yes || echo "no (self-signed)")"
log "IMAP:          $([[ $ENABLE_IMAP -eq 1 ]] && echo enabled || echo disabled)"
log "DKIM:          $([[ $ENABLE_DKIM -eq 1 ]] && echo enabled || echo disabled)"
echo

# ---------------------------------------------------------------------------
# 1. System hostname / mailname
# ---------------------------------------------------------------------------
log "Setting system hostname and mailname..."
hostnamectl set-hostname "$MAIL_HOSTNAME"
echo "$MAIL_HOSTNAME" > /etc/mailname

if ! grep -q "$MAIL_HOSTNAME" /etc/hosts; then
  echo "127.0.1.1 $MAIL_HOSTNAME ${MAIL_HOSTNAME%%.*}" >> /etc/hosts
fi

# ---------------------------------------------------------------------------
# 2. Package install (non-interactive)
# ---------------------------------------------------------------------------
log "Pre-seeding debconf for a non-interactive Postfix install..."
export DEBIAN_FRONTEND=noninteractive
debconf-set-selections <<EOF
postfix postfix/main_mailer_type select Internet Site
postfix postfix/mailname string $MAIL_HOSTNAME
EOF

log "Updating apt and installing packages..."
apt-get update -qq
PKGS=(postfix postfix-pcre mailutils libsasl2-modules ufw openssl)
[[ $ENABLE_IMAP -eq 1 ]] && PKGS+=(dovecot-core dovecot-imapd) || PKGS+=(dovecot-core)
[[ $ENABLE_DKIM -eq 1 ]] && PKGS+=(opendkim opendkim-tools)
[[ $USE_LETSENCRYPT -eq 1 ]] && PKGS+=(certbot)
apt-get install -y -qq "${PKGS[@]}"

# ---------------------------------------------------------------------------
# 3. TLS certificate
# ---------------------------------------------------------------------------
CERT_DIR="/etc/postfix/tls"
mkdir -p "$CERT_DIR"

if [[ $USE_LETSENCRYPT -eq 1 ]]; then
  log "Requesting a Let's Encrypt certificate via certbot (standalone, port 80)..."
  systemctl stop postfix || true
  certbot certonly --standalone --non-interactive --agree-tos \
    -m "$ADMIN_EMAIL" -d "$MAIL_HOSTNAME" \
    || die "certbot failed — check that port 80 is reachable and DNS for $MAIL_HOSTNAME points here."
  CERT_FILE="/etc/letsencrypt/live/$MAIL_HOSTNAME/fullchain.pem"
  KEY_FILE="/etc/letsencrypt/live/$MAIL_HOSTNAME/privkey.pem"
  # Keep the cert renewed and reload postfix/dovecot afterward.
  cat > /etc/letsencrypt/renewal-hooks/deploy/mailserver-reload.sh <<'HOOK'
#!/bin/sh
systemctl reload postfix dovecot 2>/dev/null || true
HOOK
  chmod +x /etc/letsencrypt/renewal-hooks/deploy/mailserver-reload.sh
else
  log "Generating a self-signed TLS certificate (replace with a real one, or re-run with --letsencrypt, when ready)..."
  openssl req -new -x509 -days 825 -nodes \
    -out "$CERT_DIR/mail.crt" -keyout "$CERT_DIR/mail.key" \
    -subj "/CN=$MAIL_HOSTNAME" \
    -addext "subjectAltName=DNS:$MAIL_HOSTNAME"
  chmod 600 "$CERT_DIR/mail.key"
  CERT_FILE="$CERT_DIR/mail.crt"
  KEY_FILE="$CERT_DIR/mail.key"
fi

# ---------------------------------------------------------------------------
# 4. Postfix main.cf
# ---------------------------------------------------------------------------
log "Configuring Postfix (main.cf)..."
backup_file /etc/postfix/main.cf

postconf -e "myhostname = $MAIL_HOSTNAME"
postconf -e "mydomain = $MAIL_DOMAIN"
postconf -e "myorigin = \$mydomain"
postconf -e "inet_interfaces = all"
postconf -e "inet_protocols = ipv4"
postconf -e "mydestination = \$myhostname, localhost.\$mydomain, localhost, \$mydomain"
postconf -e "mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128"
postconf -e "relayhost ="
postconf -e "message_size_limit = 26214400"
postconf -e "mailbox_size_limit = 0"
postconf -e "recipient_delimiter = +"
postconf -e "home_mailbox = Maildir/"

# TLS
postconf -e "smtpd_tls_cert_file = $CERT_FILE"
postconf -e "smtpd_tls_key_file = $KEY_FILE"
postconf -e "smtpd_tls_security_level = may"
postconf -e "smtpd_tls_auth_only = yes"
postconf -e "smtp_tls_security_level = may"
postconf -e "smtpd_tls_protocols = !SSLv2,!SSLv3,!TLSv1,!TLSv1.1"
postconf -e "smtpd_tls_mandatory_protocols = !SSLv2,!SSLv3,!TLSv1,!TLSv1.1"

# SASL (via Dovecot) for authenticated relay/submission
postconf -e "smtpd_sasl_type = dovecot"
postconf -e "smtpd_sasl_path = private/auth"
postconf -e "smtpd_sasl_auth_enable = yes"
postconf -e "smtpd_sasl_security_options = noanonymous"
postconf -e "broken_sasl_auth_clients = yes"

# Basic anti-relay / recipient restrictions
postconf -e "smtpd_relay_restrictions = permit_mynetworks,permit_sasl_authenticated,reject_unauth_destination"
postconf -e "smtpd_recipient_restrictions = permit_mynetworks,permit_sasl_authenticated,reject_unauth_pipelining,reject_non_fqdn_recipient,reject_unknown_recipient_domain,reject_unauth_destination"
postconf -e "smtpd_helo_required = yes"

if [[ $ENABLE_DKIM -eq 1 ]]; then
  postconf -e "milter_default_action = accept"
  postconf -e "milter_protocol = 6"
  postconf -e "smtpd_milters = inet:localhost:8891"
  postconf -e "non_smtpd_milters = inet:localhost:8891"
fi

# ---------------------------------------------------------------------------
# 5. Postfix master.cf — enable submission (587) and smtps (465)
# ---------------------------------------------------------------------------
log "Enabling submission (587) and smtps (465) services in master.cf..."
backup_file /etc/postfix/master.cf

enable_service_block() {
  local name="$1"
  if ! grep -q "^${name}\s" /etc/postfix/master.cf; then
    cat >> /etc/postfix/master.cf <<EOF

${name}     inet  n       -       y       -       -       smtpd
  -o syslog_name=postfix/${name}
  -o smtpd_tls_wrappermode=$( [[ "$name" == "smtps" ]] && echo yes || echo no )
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
  -o smtpd_recipient_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING
EOF
  fi
}
enable_service_block submission
enable_service_block smtps

# ---------------------------------------------------------------------------
# 6. Dovecot — SASL auth (+ optional IMAP)
# ---------------------------------------------------------------------------
log "Configuring Dovecot for SASL auth${ENABLE_IMAP:+ and IMAP}..."

mkdir -p /etc/dovecot/conf.d
backup_file /etc/dovecot/conf.d/10-master.conf

cat > /etc/dovecot/conf.d/99-mailserver.conf <<EOF
mail_location = maildir:~/Maildir

passdb {
  driver = pam
}
userdb {
  driver = passwd
}

service auth {
  unix_listener /var/spool/postfix/private/auth {
    mode = 0660
    user = postfix
    group = postfix
  }
}

ssl = required
ssl_cert = <$CERT_FILE
ssl_key = <$KEY_FILE
EOF

if [[ $ENABLE_IMAP -eq 1 ]]; then
  sed -i 's/^#\?protocols = .*/protocols = imap/' /etc/dovecot/conf.d/10-mail.conf 2>/dev/null || true
  cat >> /etc/dovecot/conf.d/99-mailserver.conf <<'EOF'
service imap-login {
  inet_listener imap {
    port = 143
  }
  inet_listener imaps {
    port = 993
    ssl = yes
  }
}
EOF
else
  cat >> /etc/dovecot/conf.d/99-mailserver.conf <<'EOF'
# IMAP disabled by deploy flag (--no-imap); auth-only for SMTP SASL.
service imap-login {
  inet_listener imap {
    port = 0
  }
  inet_listener imaps {
    port = 0
  }
}
EOF
fi

# ---------------------------------------------------------------------------
# 7. OpenDKIM
# ---------------------------------------------------------------------------
DKIM_SELECTOR="mail"
if [[ $ENABLE_DKIM -eq 1 ]]; then
  log "Setting up OpenDKIM (selector: $DKIM_SELECTOR)..."
  mkdir -p /etc/opendkim/keys/"$MAIL_DOMAIN"
  if [[ ! -f /etc/opendkim/keys/"$MAIL_DOMAIN"/${DKIM_SELECTOR}.private ]]; then
    opendkim-genkey -b 2048 -d "$MAIL_DOMAIN" -D /etc/opendkim/keys/"$MAIL_DOMAIN" -s "$DKIM_SELECTOR" -v
  fi
  chown -R opendkim:opendkim /etc/opendkim/keys
  chmod 600 /etc/opendkim/keys/"$MAIL_DOMAIN"/${DKIM_SELECTOR}.private

  cat > /etc/opendkim.conf <<EOF
Syslog			yes
UMask			002
Socket			inet:8891@localhost
PidFile		/run/opendkim/opendkim.pid
OversignHeaders	From
Domain			$MAIL_DOMAIN
KeyFile		/etc/opendkim/keys/$MAIL_DOMAIN/${DKIM_SELECTOR}.private
Selector		$DKIM_SELECTOR
Mode			sv
EOF

  systemctl enable opendkim
  systemctl restart opendkim
fi

# ---------------------------------------------------------------------------
# 8. Firewall (UFW)
# ---------------------------------------------------------------------------
log "Configuring UFW firewall rules..."
ufw allow 25/tcp    comment 'SMTP'        || true
ufw allow 587/tcp   comment 'Submission'  || true
ufw allow 465/tcp   comment 'SMTPS'       || true
[[ $ENABLE_IMAP -eq 1 ]] && { ufw allow 143/tcp comment 'IMAP' || true; ufw allow 993/tcp comment 'IMAPS' || true; }
[[ $USE_LETSENCRYPT -eq 1 ]] && ufw allow 80/tcp comment 'ACME HTTP-01' || true
ufw allow OpenSSH || true
if ! ufw status | grep -q "Status: active"; then
  warn "UFW is not currently active. Enabling it now (make sure SSH access is allowed first!)."
  ufw --force enable
fi

# ---------------------------------------------------------------------------
# 9. Start/enable services
# ---------------------------------------------------------------------------
log "Enabling and (re)starting services..."
systemctl enable postfix dovecot >/dev/null
systemctl restart dovecot
systemctl restart postfix

# ---------------------------------------------------------------------------
# 10. Summary / next steps
# ---------------------------------------------------------------------------
echo
log "Deployment complete. Verify service status with: systemctl status postfix dovecot${ENABLE_DKIM:+ opendkim}"
echo
echo "=================================================================="
echo " DNS records you still need to create for $MAIL_DOMAIN:"
echo "=================================================================="
echo
echo "  MX     $MAIL_DOMAIN.        ->  10 $MAIL_HOSTNAME."
echo "  A/AAAA $MAIL_HOSTNAME.      ->  <this server's public IP>"
echo
echo "  SPF (TXT on $MAIL_DOMAIN):"
echo "    v=spf1 mx a:$MAIL_HOSTNAME -all"
echo
echo "  DMARC (TXT on _dmarc.$MAIL_DOMAIN):"
echo "    v=DMARC1; p=quarantine; rua=mailto:$ADMIN_EMAIL"
echo
if [[ $ENABLE_DKIM -eq 1 ]]; then
  echo "  DKIM (TXT on ${DKIM_SELECTOR}._domainkey.$MAIL_DOMAIN):"
  echo "    See: /etc/opendkim/keys/$MAIL_DOMAIN/${DKIM_SELECTOR}.txt"
  echo "    ---"
  cat /etc/opendkim/keys/"$MAIL_DOMAIN"/${DKIM_SELECTOR}.txt 2>/dev/null || echo "    (file not found — check opendkim-genkey output above)"
  echo "    ---"
fi
echo "=================================================================="
echo
if [[ $USE_LETSENCRYPT -eq 0 ]]; then
  warn "Using a self-signed certificate — mail clients and some receiving"
  warn "servers will flag this. Re-run with --letsencrypt once DNS is live"
  warn "and port 80 is reachable, or supply your own cert/key at:"
  warn "  $CERT_DIR/mail.crt / mail.key"
fi
log "To create a mail user, add a normal Linux user account (useradd -m <name>; passwd <name>)"
log "— Dovecot/Postfix are configured to authenticate against system (PAM) accounts."
echo
echo "=================================================================="
echo " If this script was useful, tips are appreciated:"
echo "   https://www.paypal.me/RichardTroiano"
echo "=================================================================="
