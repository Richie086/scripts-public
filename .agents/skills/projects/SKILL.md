---
name: projects
description: Show a dashboard list of all active projects, folders, and deployment URLs
---

# Project Status Dashboard

Below is the status dashboard of your active development projects. Please review these details and display them as a beautifully formatted markdown table.

### Active Projects List:
1. **Spotify Backstage** (Developer Portal)
   - Remote Directory: `/projects/backstage` (Hetzner VM)
   - Public HTTPS URL: [https://backstage.exit-code.net](https://backstage.exit-code.net)
   - Local Dev Directory: `/home/webserver/backstage-app` (on `192.168.1.80`)
   - Local Dev URL: [http://192.168.1.80:3000](http://192.168.1.80:3000)
   - Status: Active in production under backstage.service (IP Restricted to owner)

2. **Wedge 400 Switch API** (Hardware Mock Agent)
   - Local Directory: `/home/rtroiano/repositories/scripts-public/scripts-public/projects/Wedge-400-Switch-API`
   - Remote Host URL: [http://192.168.1.80/projects/wedge-switch-400-api](http://192.168.1.80/projects/wedge-switch-400-api)
   - Credentials: `admin` / `admin`
   - Status: Active (SQLite Persistence, running on port 8000)

3. **API Crawler** (Ingestion Orchestrator)
   - Local Directory: `/home/rtroiano/repositories/scripts-public/scripts-public/projects/BMC-API-Crawler`
   - Remote Host URL: [http://192.168.1.80/projects/bmc-api-crawler](http://192.168.1.80/projects/bmc-api-crawler)
   - Credentials: `admin` / `admin`
   - Status: Active (Pushes to loopback port 8000, running on port 8001)

4. **FastAPI Starter** (Project Template)
   - Local Directory: `/home/rtroiano/repositories/fastapi-starter`
   - Local Server URL: [http://localhost:8002](http://localhost:8002)
   - Status: Running locally on port 8002

Please render a structured table summarizing these projects, their links, directories, and current configuration states.
