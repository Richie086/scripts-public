# Walkthrough - Wedge 400 Switch API & Standalone Crawler Ingestion Engine

Ongoing log of accomplishments, test validations, and features implemented.

---

## 1. What was accomplished
- **Project Decoupling**:
  - Separated concerns into two independent deployable systems under `/home/rtroiano/repositories/scripts-public/scripts-public/projects/`.
- **Wedge-400-Switch-API** (Hardware Mock Agent):
  - Retains SQLite persistence configuration, glassy Dracula/Nord theme switcher, detailed list views, and OpenBMC sensor mocks.
  - Removed crawling engines from backend to keep the agent self-contained.
  - Implemented routes CRUD (`POST /api/sys/routes` and `GET /api/sys/routes`) enabling external ingestion tools to register dynamic mockup paths directly into the SQLite backend.
  - Updated the Web UI to show a clean **Dynamic Routes** list dashboard to check, search, and run query checks on registered endpoints.
  - Pytest validation: 10 tests passing cleanly.
  - Deployed to `192.168.1.80` on port `8000` (Nginx: `/projects/wedge-switch-400-api`).
- **API-Crawler** (Ingester & Orchestrator):
  - Created a new FastAPI application crawling repository URLs or doc pages on-the-fly.
  - Automatically filters static paths, constructs structured mock payloads (versions, power specs, cpu statuses, etc.), and POSTs route packages directly onto the switch database.
  - Exposes in-memory config endpoint to update target switch endpoint URL.
  - Created a dedicated glassy **Crawler Console UI** allowing catalog navigation, raw URL crawling, and a live log tracking panel showing ingestion results.
  - Pytest validation: Mock testing completed with 3 tests passing cleanly.
  - Deployed to `192.168.1.80` on port `8001` (Nginx: `/projects/bmc-api-crawler`).
- **Custom Antigravity Dashboard Commands**:
  - Registered `/dashboard` and `/projects` commands inside the `.agents/commands/` directory of the `scripts-public` repository.
  - These commands trigger the agent to display a structured markdown table summarizing all active development sites, credentials, and directories.

---

## 2. Test Verification and Results

### Pytest Validation
- **Wedge-400-Switch-API**:
  ```text
  tests/test_api.py ..........                                             [100%]
  ======================== 10 passed, 3 warnings in 0.59s ========================
  ```
- **API-Crawler**:
  ```text
  tests/test_crawler.py ...                                                [100%]
  ======================== 3 passed, 3 warnings in 0.42s =========================
  ```

### Remote Execution Tests (Bypassing Basic Auth)
Crawling OpenBMC Wedge 400 test file:
```bash
curl -u admin:admin -s -X POST -H 'Content-Type: application/json' -d '{"url": "https://raw.githubusercontent.com/facebook/openbmc/refs/heads/helium/tests2/tests/wedge400/test_rest_endpoint.py"}' http://127.0.0.1/projects/bmc-api-crawler/api/crawl
```
Response:
```json
{
  "status":"completed",
  "url":"https://raw.githubusercontent.com/facebook/openbmc/refs/heads/helium/tests2/tests/wedge400/test_rest_endpoint.py",
  "target_switch":"http://127.0.0.1:8000/projects/wedge-switch-400-api",
  "endpoints_found":["/api/sys/feutil/fan1","/api/sys/feutil/fan2", ...],
  "registered":["/api/sys/feutil/fan1","/api/sys/feutil/fan2", ...],
  "failed":[]
}
```

Querying registered route response:
```bash
curl -u admin:admin -s http://127.0.0.1/projects/wedge-switch-400-api/api/sys/vddcore
```
Output:
```json
{"voltage_v":1.05,"status":"nominal"}
```

---

## 3. Operations and Console Links (Basic Auth `admin:admin`)
1. **Wedge 400 Console Dashboard**:
   👉 **[http://192.168.1.80/projects/wedge-switch-400-api](http://192.168.1.80/projects/wedge-switch-400-api)**
2. **API Crawler Console**:
   👉 **[http://192.168.1.80/projects/bmc-api-crawler](http://192.168.1.80/projects/bmc-api-crawler)**
3. **Spotify Backstage Portal**:
   👉 **[http://192.168.1.80:3000](http://192.168.1.80:3000)**
