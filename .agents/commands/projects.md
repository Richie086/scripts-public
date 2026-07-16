---
name: projects
description: "Show a dashboard list of all active projects, folders, and deployment URLs"
---
Below is the status dashboard of your active development projects. Please review these details and display them as a beautifully formatted markdown table.

### Active Projects List:
1. **Spotify Backstage** (Developer Portal Portal)
   - Local Directory (Remote host): `/home/webserver/backstage-app`
   - Remote Host URL: [http://192.168.1.80:3000](http://192.168.1.80:3000)
   - Credentials: Guest Auth (Permissions Disabled)
   - Status: Active (Running via systemd/yarn)

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

Please render a structured table summarizing these projects, their links, directories, and current configuration states.
