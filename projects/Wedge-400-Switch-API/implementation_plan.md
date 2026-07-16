# Implementation Plan - Decoupling Wedge 400 Switch API & BMC API Crawler

This document details the architectural decoupling of the Switch mock hardware agent and the documentation Ingestion/Crawler engine into two separate projects.

---

## 1. Goal Description
To separate concerns, we will split the codebase into two distinct, deployable projects under `/home/rtroiano/repositories/scripts-public/scripts-public/projects/`:
1. **Wedge-400-Switch-API** (Existing):
   - Represents the mock OpenBMC hardware agent.
   - Manages physical hardware simulation (sensors, ports, VLANs, LLDP).
   - Exposes a clean CRUD API for registering dynamic mock routes (`POST/GET /api/sys/routes`).
   - Serves the hardware Switch Console UI dashboard (without crawler features).
2. **BMC-API-Crawler** (New):
   - A standalone service that crawls OpenBMC tests or API documentation URLs.
   - Extracts endpoints and automatically structures mock JSON payloads.
   - Pushes (POSTs) the discovered routes directly to the target Wedge 400 Switch API.
   - Serves a dedicated Crawler Console UI where users can view documentation catalogs, execute crawls, and check dynamic registration logs.

---

## 2. Decoupled Architecture

```mermaid
graph TD
    User([User Browser]) -->|Access Console| Crawler[BMC-API-Crawler (Port 8001)]
    User -->|Access Switch Console| Switch[Wedge-400-Switch-API (Port 8000)]
    Crawler -->|Ingest / Crawl URL| Github[Github / Raw Docs]
    Crawler -->|Push Discovered Routes| Switch
```

- **Wedge-400-Switch-API** will run on port `8000` (Nginx route: `/projects/wedge-switch-400-api`).
- **BMC-API-Crawler** will run on port `8001` (Nginx route: `/projects/bmc-api-crawler`).

---

## 3. Proposed Changes

### Component 1: Wedge-400-Switch-API Updates

#### [MODIFY] `src/fastapi_starter/models.py`
- Remove crawler-specific models (`CrawlerRequest`, `CrawlerResponse`).
- Keep `DynamicEndpoint` schema (representing routes registered by the crawler).

#### [MODIFY] `src/fastapi_starter/api.py`
- Delete `POST /api/sys/crawlers` and `GET /api/sys/crawlers` endpoints.
- Add `POST /api/sys/routes` (to register a dynamic route) and `GET /api/sys/routes` (to list them).
- Keep the fallback wildcard handler, pulling from the database of registered dynamic routes.

#### [MODIFY] `src/fastapi_starter/templates/index.html`
- Remove the "API Crawlers & Docs" tab from the navigation and content area.
- Replace it with a "Dynamic Routes" tab which simply lists the routes registered on this switch and allows query-testing them.

#### [MODIFY] `tests/test_api.py`
- Remove test cases for crawler fetching.
- Add test cases verifying registering dynamic routes via `POST /api/sys/routes` and querying them.

---

### Component 2: BMC-API-Crawler (New Project)

#### [NEW] `pyproject.toml`
Set up metadata and dependencies (`fastapi`, `uvicorn`, `httpx`, `jinja2`).

#### [NEW] `build.sh`
Compile checker script for python files.

#### [NEW] `deploy.sh`
Deployment script that:
- Syncs files to the remote server `/home/webserver/bmc-crawler`.
- Installs python virtual environment.
- Configures Nginx Basic Auth and Nginx route `/projects/bmc-api-crawler` proxying to `127.0.0.1:8001`.
- Creates and runs `bmc-crawler.service` systemd unit.

#### [NEW] `src/crawler/main.py`
The FastAPI application:
- Exposes `POST /api/crawl` taking a target URL, fetching and parsing it, generating mock payloads, and sending `POST /api/sys/routes` calls to the Wedge 400 Switch.
- Exposes config paths to update target Switch API endpoint.
- Serves the Crawler Dashboard UI.

#### [NEW] `src/crawler/templates/index.html`
A dedicated glassy, 4px-bevel console:
- Navigation sidebar (Crawler Home, Browse Docs, Target Switch Settings).
- Live crawler logs terminal panel.
- Interactive documentation index links to click-crawl directly.

#### [NEW] `tests/test_crawler.py`
Pytest suite checking the crawler parsing logic and target switch mapping.

---

## 4. Verification Plan

### Automated Tests
Run tests for both projects:
- Wedge-400-Switch-API: `.venv/bin/pytest`
- BMC-API-Crawler: `.venv/bin/pytest`

### Manual Verification
1. Deploy both projects via their respective `./deploy.sh` scripts.
2. Open the Crawler UI at `http://192.168.1.80/projects/bmc-api-crawler/` (Basic Auth).
3. Set the Switch Endpoint in Settings: `http://127.0.0.1:8000/projects/wedge-switch-400-api`.
4. Run a crawl against `test_rest_endpoint.py`.
5. Open the Switch Console at `http://192.168.1.80/projects/wedge-switch-400-api/`. Go to the "Dynamic Routes" tab, and verify that the crawled endpoints are listed and return correct mock data.
