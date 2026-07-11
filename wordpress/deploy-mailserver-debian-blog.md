This utility script came about due to someone posting on Facebook asking if anyone out there could help build out a Debian 13 system with Postfix, Dovecot, Let's Encrypt, a firewall—everything you will need to get a mail server up and running. While configuring all of these components manually can take hours of trial and error, automation makes it repeatable in seconds.

**WARNING:** Before you read any further, a word of caution: do not try to run your own mail server unless you are well versed in combating spam, configuring DNS, DKIM, SPF, and DMARC. The modern email ecosystem is incredibly hostile to self-hosted servers. If you want mail to be reliably delivered to external networks (like Gmail, Outlook, or Yahoo), I would strongly suggest using a professional hosted solution or simply just using Gmail.

If you are still ready to proceed—perhaps for a home lab, private relay, or internal network—here is a breakdown of how the automation script works and how it simplifies this complex deployment.

---

## What the Script Automates

Setting up a mail server requires configuring multiple independent daemons to communicate securely and work in harmony. The script installs and configures:

1. **Postfix MTA**: Handles sending and receiving mail.
2. **Dovecot MDA**: Exposes IMAP/IMAPS for clients and provides a SASL socket for Postfix to authenticate users.
3. **OpenDKIM**: Generates cryptographic keys and signs outgoing mail headers.
4. **Let's Encrypt / Certbot**: Automated TLS certificate retrieval and deploy reload hooks.
5. **UFW Firewall**: Configures ports 25, 465, 587, 143, 993, and 80.
6. **Rollback Feature**: Completely purges all packages and configuration files if you need to start fresh.

---

## Step-by-Step Automation Process

Here is the technical breakdown of the script's workflow:

### 1. Pre-seeding and Installation
Postfix usually prompts for configuration choices during package installation. To prevent the installation from pausing for user input, the script pre-seeds `debconf` values before calling `apt-get`:

```bash
export DEBIAN_FRONTEND=noninteractive
debconf-set-selections <<EOF
postfix postfix/main_mailer_type select Internet Site
postfix postfix/mailname string mail.example.com
EOF
```

### 2. TLS Certificates
The script prompts whether you want to acquire a Let's Encrypt certificate. If selected, it stops Postfix (to free up port 80), runs Certbot in standalone mode, and installs a deploy hook to reload Postfix and Dovecot automatically when the certificates renew:

```bash
certbot certonly --standalone --non-interactive --agree-tos \
  -m "admin@example.com" -d "mail.example.com"
```

If Let's Encrypt is bypassed, it generates a fallback self-signed OpenSSL certificate.

### 3. Postfix (`main.cf` & `master.cf`)
Postfix is configured to require TLS for authenticated users, enable SASL auth via Dovecot, and enforce anti-spam/anti-relay rules. The script uses `postconf -e` to write these settings directly to `/etc/postfix/main.cf`. 

Additionally, it appends blocks to `/etc/postfix/master.cf` to enable the secure **Submission (587)** and **SMTPS (465)** ports.

### 4. Dovecot SSL and Mailboxes
Rather than putting SSL configuration into a custom file, the script modifies the standard `/etc/dovecot/conf.d/10-ssl.conf` file, keeping configurations clean and aligned with Debian package standards. General IMAP listeners and local Unix `Maildir/` delivery settings are configured in `/etc/dovecot/conf.d/99-mailserver.conf`.

### 5. OpenDKIM Signing
To prevent your emails from going directly to spam folders, OpenDKIM is configured to listen on localhost port 8891. The script runs `opendkim-genkey` to generate a 2048-bit DKIM key under the selector `mail` and stores the public TXT record in `/etc/opendkim/keys/example.com/mail.txt`.

### 6. Firewall Rules
UFW rules are added to allow the SMTP/IMAP ports:
- `25/tcp` (SMTP relaying)
- `587/tcp` (Submission)
- `465/tcp` (SMTPS)
- `143/tcp` (IMAP)
- `993/tcp` (IMAPS)
- `80/tcp` (ACME HTTP-01 renewals)

---

## Reversibility: The Rollback Feature

Deploying mail servers often involves testing. If you make a mistake or want to reclaim the system resources, you can trigger a full uninstallation and cleanup by passing the `--rollback` flag:

```bash
sudo ./deploy-mailserver-debian.sh --rollback
```

This rollback logic will:
- Stop and disable the mail services.
- Delete certbot certificates associated with the mail hostname.
- Perform a complete `apt-get purge` on the mail-related packages to wipe their defaults.
- Clean up leftover folders (`/etc/postfix`, `/etc/dovecot`, `/etc/opendkim`).
- Revert `/etc/hosts` changes.
- Delete the corresponding UFW rules.

---

## How to Get the Script

The script is open source and hosted in my public GitHub repository.

### Option 1: Direct Download
To download only this specific script directly to your Debian server:

```bash
curl -O https://raw.githubusercontent.com/Richie086/scripts-public/refs/heads/main/projects/deploy-mailserver-debian.sh
chmod +x deploy-mailserver-debian.sh
```

### Option 2: Clone the Repository
To clone the entire scripts collection:

```bash
git clone https://github.com/Richie086/scripts-public.git
```
Navigate to the `projects/` directory to locate the script.
