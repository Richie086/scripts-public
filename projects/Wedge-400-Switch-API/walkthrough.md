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
  - **Active Directory Integration**:
    - Integrated `ldap3` library for authenticating domain logins with support for live search queries of `memberOf` group attributes.
    - Added support for dedicated AD service account bind DN/password lookups and password verification.
    - Implemented secure JWT-based HTTP-only session cookies.
    - Added an AD Simulation Mode allowing local offline verification using preconfigured mock accounts (`ad_admin` / `AdminPass123`, `ad_operator` / `OperatorPass123`, `ad_viewer` / `ViewerPass123`).
    - Added a Dracula login screen overlay and an admin-only AD Settings Configuration dashboard tab.
    - Restrained switch telemetry modification endpoints (ASIC reset, port configuration, and VLAN creation) using role-based permissions (`admin`, `operator`, `viewer`).
    - Expanded Pytest validation to 18 unit tests passing cleanly.
- **API-Crawler** (Ingester & Orchestrator):
  - Created a new FastAPI application crawling repository URLs or doc pages on-the-fly.
  - Automatically filters static paths, constructs structured mock payloads (versions, power specs, cpu statuses, etc.), and POSTs route packages directly onto the switch database.
  - Exposes in-memory config endpoint to update target switch endpoint URL.
  - Created a dedicated glassy **Crawler Console UI** allowing catalog navigation, raw URL crawling, and a live log tracking panel showing ingestion results.
  - Pytest validation: Mock testing completed with 3 tests passing cleanly.
  - Deployed to `192.168.1.80` on port `8001` (Nginx: `/projects/bmc-api-crawler`).

---

## 2. Test Verification and Results

### Pytest Validation
- **Wedge-400-Switch-API**:
  ```text
  tests/test_api.py ..........                                             [ 55%]
  tests/test_auth.py ........                                              [100%]
  ======================= 18 passed, 15 warnings in 0.88s ========================
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

## 3. Operations and Console Links
1. **Wedge 400 Console Dashboard** (Secured by AD login; Nginx Basic Auth bypassed):
   👉 **[http://192.168.1.80/projects/wedge-switch-400-api/](http://192.168.1.80/projects/wedge-switch-400-api/)**
2. **Wedge 400 API Interactive Docs** (Protected by Basic Auth `admin:admin`):
   👉 **[http://192.168.1.80/projects/wedge-switch-400-api/docs](http://192.168.1.80/projects/wedge-switch-400-api/docs)**
3. **BMC API Crawler Console** (Protected by Basic Auth `admin:admin`):
   👉 **[http://192.168.1.80/projects/bmc-api-crawler](http://192.168.1.80/projects/bmc-api-crawler)**
4. **Spotify Backstage Portal**:
   👉 **[http://192.168.1.80:3000](http://192.168.1.80:3000)**
