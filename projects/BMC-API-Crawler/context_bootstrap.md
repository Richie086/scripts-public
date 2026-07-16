# Context Bootstrap: Standalone API Crawler Ingest Engine

If you are continuing development on this project in a new conversation, paste the content of this file to give the AI agent immediate full context.

---

## 1. Project Overview
- **Name**: Standalone API Crawler
- **Directory**: `/home/rtroiano/repositories/scripts-public/scripts-public/projects/BMC-API-Crawler`
- **Role**: Scrapes target document and test URLs, filters static paths, constructs structured mock payloads, and registers them directly onto the Switch's SQLite database.
- **Backend Stack**: Python, FastAPI.
- **Frontend Stack**: Single Page App served from `/` (HTML, Vanilla CSS, Vanilla Javascript). Supports Dracula (dark) and Nord (light) themes with `localStorage` persistence. Has a glassy 4px beveled look.
- **Port**: `8001` (loopback). Proxied via Nginx.

## 2. Deployed Environment
- **Host**: `192.168.1.80` (Ubuntu Server)
- **Nginx Location**: `/projects/bmc-api-crawler`
- **Service Name**: `bmc-crawler.service`
- **Access URL**: [http://192.168.1.80/projects/bmc-api-crawler](http://192.168.1.80/projects/bmc-api-crawler)
- **Nginx Basic Auth**: `admin` / `admin`

## 3. Integration Mechanism
- Communicates directly with the Wedge 400 Switch API on the loopback address `http://127.0.0.1:8000/projects/wedge-switch-400-api` to register routes (`POST /api/sys/routes`). This bypasses external Nginx Basic Authentication.
- Active Target Switch URL is saved in-memory and can be updated dynamically via settings.

## 4. Key API Endpoints
- `GET /api/settings` & `POST /api/settings`: Get and update the active Target Switch API base URL.
- `POST /api/crawl`: Takes `{"url": "...", "switch_url": "..."}`. Scrapes the raw file, extracts endpoints, generates mock payloads, and pushes them to the switch.

## 5. Development Commands
- Compile checks: `./build.sh`
- Running unit tests (uses mock requests): `.venv/bin/pytest`
- Deploy to remote server: `./deploy.sh`

---

## 6. Prompt to Resume Development (Copy-Paste)
> "I want to resume development on the Standalone API Crawler project located in `/home/rtroiano/repositories/scripts-public/scripts-public/projects/BMC-API-Crawler`. It is a FastAPI backend scraping URLs for REST endpoints, formatting mock payloads, and POSTing them to a target mock switch. It serves a glassy Dracula/Nord UI dashboard and is deployed under systemd and Nginx Basic Auth on 192.168.1.80. Please read the source files, run unit tests, and help me with the next steps."
