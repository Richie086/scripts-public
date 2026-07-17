# Cheap & Secure Shared AI Developer Infrastructure Guide

This guide outlines a highly secure, cost-effective, and open-source setup designed for developers **Richard** (`richie086@gmail.com`) and **Tyler** (`mr.stobbe@gmail.com`) of **Exit Code Automations** collaborating on AI applications using **Google Antigravity** and **GitHub Free**.

---

## 1. Hosting Environment (Low-Cost VPS)

To keep costs to a minimum while ensuring reliability, we recommend selecting one of the following virtual private servers (VPS):
- **Hetzner Cloud**: `CPX21` (3 vCPUs, 4GB RAM, 80GB SSD, ~$8/mo) or `CPX31` (4 vCPUs, 8GB RAM, 160GB SSD, ~$15/mo).
- **OVH / Linode / DigitalOcean**: Equivalent basic instances offering at least 4GB of RAM and 2-4 vCPUs.

The shared VPS acts as the central host where both developers run their backend processes, test AI applications, and collaborate in shared work folders.

---

## 2. Secure Networking (Tailscale VPN)

To secure SSH access without exposing your server to port-scanning or brute-force bots on the public internet, use a free mesh VPN:
1. Sign up for a free account at [Tailscale](https://tailscale.com).
2. Install Tailscale on the server:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
3. Install Tailscale on both client machines.
4. Block external SSH access on the server’s firewall, keeping it open only on the Tailscale interface:
   ```bash
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow in on tailscale0 to any port 22 proto tcp
   sudo ufw enable
   ```
This setup completely eliminates the risk of public SSH brute-forcing.

---

## 3. Shared Workspace Configuration

We want a shared folder where both developers can collaborate, edit files, and build projects together without encountering permission errors.

We configure this using the `setup_shared_dev_server.sh` script, which does the following:
- Creates a `devs` user group.
- Creates `/srv/projects` and transfers ownership to `root:devs`.
- Sets the `SetGID` bit so any file created inside automatically belongs to the `devs` group.
- Sets Default Access Control Lists (ACLs) to ensure files are read-writable by all members of the `devs` group.

### Running the Setup
1. Clone this repository onto the VPS.
2. Run the script:
   ```bash
   bash bash/setup_shared_dev_server.sh
   ```
3. Add both developer accounts (`richie` and `tyler`) to the group:
   ```bash
   sudo usermod -aG devs richie
   sudo usermod -aG devs tyler
   ```

---

## 4. Git Hosting (GitHub Free)

Since we are using **GitHub Free** for Git hosting, we offload code hosting, issue tracking, and repository wikis to GitHub. This saves storage, CPU, and RAM on the VPS.

### Setup Instructions
1. **GitHub Account Setup**: Ensure both developers (`Richie086` and Tyler's GitHub account) have free GitHub accounts.
2. **Organization / Repository Sharing**: 
   - Create a free **GitHub Organization** (e.g. `exit-code-automations`) for your team to centralize ownership of private repositories.
   - Invite Tyler's GitHub account to the organization.
3. **SSH Keys on the VPS**:
   - Each developer runs `ssh-keygen` inside their user account on the VPS.
   - Add the public key (`~/.ssh/id_ed25519.pub`) to their individual GitHub account profiles.
   - This allows them to clone, commit, and push repositories directly from their server shells securely.

---

## 5. Collaborative Secrets Store (Vaultwarden)

We run **Vaultwarden** (a lightweight Rust implementation of Bitwarden) in Docker on the VPS to securely share API tokens, GCP service account credentials, and database passwords.

### Deploying the Stack
1. Ensure Docker and Docker Compose are installed on the VPS.
2. Create `/srv/projects/docker/docker-compose.yml` with the following configuration:

```yaml
version: '3.8'

services:
  vaultwarden:
    image: vaultwarden/server:latest
    container_name: vaultwarden
    restart: always
    environment:
      - WEBSOCKET_ENABLED=true
      - SIGNUPS_ALLOWED=true # Toggle to false after both devs register
    volumes:
      - ./data/vaultwarden:/data
    ports:
      - "127.0.0.1:8080:80"
```

3. Spin up the container:
   ```bash
   docker compose up -d
   ```
4. Access the web interface securely using SSH port forwarding from your local workstation:
   ```bash
   ssh -L 8080:localhost:8080 richie@vps-tailscale-ip
   ```
5. Open `http://localhost:8080` in your web browser, register your accounts (`richie086@gmail.com` and `mr.stobbe@gmail.com`), and create a shared Organization collection.

---

## 6. Sharing Accounts & API Credentials

To develop AI applications, both developers need access to API accounts (such as Vertex AI or OpenAI).

### A. Shared Service Accounts (GCP/Vertex AI)
To comply with security best practices, **do not grant the project-wide `Editor` role** to the shared key file. Instead, configure a scoped least-privilege role model:
1. Create a single Google Cloud Service Account.
2. Grant only the following specific roles:
   - **`Vertex AI User`**: To call Gemini models, embeddings, and vector services.
   - **`Storage Object Admin`**: To read/write training datasets and model weights in GCS buckets.
   - **`BigQuery User`**: (If pulling data from BQ).
3. Generate a JSON Key for the service account.
4. Save this JSON key inside Vaultwarden in a shared organization collection.
5. On the development server, developers can reference a single copy of this key placed securely in `/srv/projects/secrets/gcp-sa-key.json` (readable only by the `devs` group, configured with `chmod 640`).
6. Load credentials automatically in projects via a `.env` file referencing:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=/srv/projects/secrets/gcp-sa-key.json
   ```

### B. Shared API Tokens (OpenAI/Anthropic)
1. Store tokens in the shared Vaultwarden organization.
2. Store project-specific credentials in a project-specific `.env` file (e.g. `/srv/projects/my-ai-app/.env`).

---

## 7. Developing with Google Antigravity

With the shared VPS configured:
1. Each developer connects their local VS Code client to the VPS using the **Remote-SSH** extension.
2. Open the `/srv/projects` workspace folder in VS Code.
3. Install the **Google Antigravity** extension inside the remote VS Code session.
4. When writing code, Antigravity runs contextually within each developer's isolated user workspace on the server, respecting their remote configuration.
5. Code is committed and pushed directly to your private GitHub repositories.

---

## 8. Automated Documentation & Project Dashboards

To track and monitor all developer repositories, we deploy a Python-based status scanner that automatically builds:
- A Markdown dashboard: `markdown/PROJECT_DASHBOARD.md`
- A beautiful, beveled Dracula-themed HTML dashboard: `web/index.html`

The script (`python/generate_project_dashboard.py`) runs health status pings, checks local repository directories, and extracts the branch name and last git commit hash, date, message, and author for each active project.

### Automating the Dashboard via Cron
To run this scan automatically on the server every hour:
1. Open the crontab editor on the Dev VM:
   ```bash
   crontab -e
   ```
2. Add the following entry (adjusting the path to your cloned repository):
   ```cron
   0 * * * * /usr/bin/python3 /srv/projects/scripts-public/python/generate_project_dashboard.py >/dev/null 2>&1
   ```
This keeps your developer team wiki and portal status completely synchronized without manual updates.
