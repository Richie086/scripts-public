# Debian 13 (Trixie) Mail Server Deployment Script

The [deploy-mailserver-debian.sh](deploy-mailserver-debian.sh) script provides automated, idempotent installation and configuration of a complete, secure mail server on Debian 13 (Trixie).

## Overview of Components

The script automates the setup of the following components:
1. **MTA (Mail Transfer Agent)**: Postfix is installed and configured for sending and receiving mail.
2. **MDA (Mail Delivery Agent) & SASL**: Dovecot handles delivery to Unix `Maildir/` format, authenticates users for sending (SASL over a socket), and provides secure IMAP access.
3. **DKIM (DomainKeys Identified Mail)**: OpenDKIM signs outgoing mail to ensure authenticity and improve deliverability.
4. **TLS Encryption**: Secures mail transfers and client access using Let's Encrypt (Certbot standalone) or local self-signed certificates.
5. **Firewall**: UFW rules are set up for secure communication (ports 25, 465, 587, 143, 993, and optionally 80).
6. **Rollback capability**: An optional `--rollback` flag allows complete uninstallation and cleanup of all configurations and packages.

---

## Prerequisites

- **Debian 13 (Trixie)** system.
- **Root access** (must run with `sudo` or as the `root` user).
- **Public IP Address** with ports `25`, `587`, `465`, `143`, and `993` open and not blocked by your ISP or cloud firewall.
- **Port 80** open if using Let's Encrypt (Certbot needs standalone HTTP-01 verification).
- **DNS Records** already pointed at the server's public IP address before running Let's Encrypt cert creation.

---

## Usage

The script is highly flexible, supporting fully interactive prompting or non-interactive flag-based runs.

### 1. Interactive (Default)
If run without arguments, it prompts for missing required inputs:
```bash
sudo ./deploy-mailserver-debian.sh
```

### 2. Semi-Interactive / Pre-filled
Pre-fill critical parameters and prompt for yes/no features:
```bash
sudo ./deploy-mailserver-debian.sh --domain example.com --hostname mail.example.com --admin-email postmaster@example.com
```

### 3. Fully Non-Interactive (Automation/CI)
Fails if required values are missing; uses defaults for yes/no options:
```bash
sudo ./deploy-mailserver-debian.sh \
  --domain example.com \
  --hostname mail.example.com \
  --admin-email postmaster@example.com \
  --letsencrypt \
  --non-interactive
```

### Script Flags
- `--domain <domain>`: Base mail domain (e.g. `example.com`).
- `--hostname <fqdn>`: Fully-qualified domain name of the mail server (e.g. `mail.example.com`).
- `--admin-email <email>`: Administrator contact/postmaster email.
- `--letsencrypt`: Acquire a valid Let's Encrypt SSL certificate.
- `--no-imap`: Skip Dovecot IMAP (MTA/SASL authentication only).
- `--no-dkim`: Skip OpenDKIM signing setup.
- `--non-interactive`: Run silently with default values.
- `--rollback`: Perform a complete cleanup and package uninstallation.
- `-h | --help`: Show usage text.

---

## Service Configuration Details

### Postfix
- **Location**: `/etc/postfix/main.cf` and `/etc/postfix/master.cf`
- **Actions**:
  - Sets system mail identity (`myhostname`, `mydomain`, `myorigin`).
  - Configures secure TLS settings, disabling deprecated protocol versions (SSLv2, SSLv3, TLSv1, TLSv1.1).
  - Integrates Dovecot SASL for sending mail (`smtpd_sasl_type = dovecot`).
  - Enforces spam/anti-relay rules (`permit_mynetworks, permit_sasl_authenticated, reject_unauth_destination`, etc.).
  - Configures Milters for OpenDKIM on port `8891`.
  - Enables secure Submission on port `587` (STARTTLS) and SMTPS on port `465` (Implicit TLS) in `master.cf`.

### Dovecot
- **Location**: `/etc/dovecot/conf.d/10-ssl.conf` and `/etc/dovecot/conf.d/99-mailserver.conf`
- **Actions**:
  - SSL/TLS settings (`ssl = required`, `ssl_cert`, `ssl_key`) are configured in `10-ssl.conf`.
  - Mailboxes are delivered to local `~/Maildir` directories.
  - Implements PAM system user authentication.
  - Exposes an authentication socket at `/var/spool/postfix/private/auth` for Postfix.
  - Opens ports `143` (IMAP) and `993` (IMAPS) in `99-mailserver.conf`.

### OpenDKIM
- **Location**: `/etc/opendkim.conf` and `/etc/opendkim/keys/`
- **Actions**:
  - Generates a 2048-bit DKIM key under selector `mail` for the domain.
  - Configures OpenDKIM daemon to listen on `localhost:8891`.
  - Sets up headers signing and saves the public TXT record key to `/etc/opendkim/keys/<domain>/mail.txt`.

---

## Rollback & Uninstallation

If you need to uninstall the mail server packages or start from a fresh slate, you can trigger the rollback mechanism:
```bash
sudo ./deploy-mailserver-debian.sh --rollback
```

**What the Rollback does:**
1. Stops and disables `postfix`, `dovecot`, and `opendkim` services.
2. Deletes certbot Let's Encrypt certificates associated with the mail hostname.
3. Purges all mail-related packages: `postfix`, `postfix-pcre`, `mailutils`, `libsasl2-modules`, `dovecot-core`, `dovecot-imapd`, `opendkim`, `opendkim-tools`, `certbot`.
4. Performs `apt-get autoremove --purge` to clean up dangling dependencies.
5. Deletes all configuration directories and files created by the script:
   - `/etc/postfix`
   - `/etc/dovecot`
   - `/etc/opendkim`
   - `/etc/opendkim.conf`
   - `/etc/mailname`
   - Certbot renewal reload hooks
6. Removes host-specific local mappings in `/etc/hosts`.
7. Deletes firewall rules (ports 25, 587, 465, 143, 993, 80) from `UFW`.
8. Warns you if the system hostname matches the deleted mail server hostname, prompting manual restoration.

---

## DNS Configuration Requirements

For mail deliverability, you **must** configure these DNS records on your domain registrar:

1. **MX (Mail Exchange)**:
   - **Type**: `MX`
   - **Name**: `@` (or empty)
   - **Value**: `10 mail.yourdomain.com.` (points to your FQDN)

2. **A Record**:
   - **Type**: `A`
   - **Name**: `mail` (or FQDN subhost)
   - **Value**: `<your-server-public-ip>`

3. **SPF (Sender Policy Framework)**:
   - **Type**: `TXT`
   - **Name**: `@`
   - **Value**: `v=spf1 mx a:mail.yourdomain.com -all`

4. **DMARC (Domain-based Message Authentication)**:
   - **Type**: `TXT`
   - **Name**: `_dmarc`
   - **Value**: `v=DMARC1; p=quarantine; rua=mailto:postmaster@yourdomain.com`

5. **DKIM**:
   - **Type**: `TXT`
   - **Name**: `mail._domainkey`
   - **Value**: Read the contents of `/etc/opendkim/keys/yourdomain.com/mail.txt` for the public key.

---

## Post-Installation: Adding Users

Dovecot and Postfix authenticate against standard Linux system users (via PAM/NSS). To add a new email user:

1. Create a Linux user account on the server:
   ```bash
   sudo useradd -m -s /sbin/nologin username
   ```
2. Set a password for the user:
   ```bash
   sudo passwd username
   ```
This user will now be able to log into IMAP (username: `username`, password: the password you set) and send/receive emails under `username@yourdomain.com`.
