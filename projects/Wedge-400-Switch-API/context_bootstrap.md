# Context Bootstrap: Wedge 400 Switch API Mock Agent

If you are continuing development on this project in a new conversation, paste the content of this file to give the AI agent immediate full context.

---

## 1. Project Overview
- **Name**: Wedge 400 Switch API
- **Directory**: `/home/rtroiano/repositories/scripts-public/scripts-public/projects/Wedge-400-Switch-API`
- **Role**: Emulates switch hardware status (sensors, port statuses, VLANs, LLDP) matching OpenBMC specifications. Supports dynamic custom mock route registration.
- **Backend Stack**: Python, FastAPI, SQLite (standard `sqlite3` library, zero external DB dependencies).
- **Frontend Stack**: Single Page App served from `/` (HTML, Vanilla CSS, Vanilla Javascript). Supports Dracula (dark) and Nord (light) themes with `localStorage` persistence. Has a glassy 4px beveled look.
- **Port**: `8000` (loopback). Proxied via Nginx.

## 2. Deployed Environment
- **Host**: `192.168.1.80` (Ubuntu Server)
- **Nginx Location**: `/projects/wedge-switch-400-api`
- **Service Name**: `wedge400-api.service`
- **Access URL**: [http://192.168.1.80/projects/wedge-switch-400-api](http://192.168.1.80/projects/wedge-switch-400-api)
- **Nginx Basic Auth**: `admin` / `admin`

## 3. Database Schema (`switch_config.db`)
- `ports` (port_id TEXT PK, name TEXT, admin_state TEXT, oper_state TEXT, speed_gbps INTEGER, mtu INTEGER, transceiver_present INTEGER, rx_power_dbm REAL, tx_power_dbm REAL, errors_in INTEGER, errors_out INTEGER)
- `vlans` (vlan_id INTEGER PK, name TEXT, ports TEXT)
- `dynamic_routes` (path TEXT PK, payload TEXT)

## 4. Key API Endpoints
- `GET /api/sys/sensors`: Returns emulated temperature, fans, and voltage readings.
- `GET /api/sys/ports`: Returns all port configurations.
- `PATCH /api/sys/ports/{port_id:path}`: Updates admin_state, speed_gbps, and mtu in the database.
- `GET /api/sys/vlans` & `POST /api/sys/vlans`: Retrieve and create VLAN associations.
- `POST /api/sys/routes` & `GET /api/sys/routes`: CRUD for registering dynamic custom JSON routes.
- `GET /api/sys/{rest_of_path:path}`: Wildcard fallback matching registered dynamic routes.

## 5. Development Commands
- Compile checks: `./build.sh`
- Running unit tests: `.venv/bin/pytest`
- Deploy to remote server: `WEDGE_ADMIN_USER="admin" WEDGE_ADMIN_PASS="admin" ./deploy.sh`

---

## 6. Prompt to Resume Development (Copy-Paste)
> "I want to resume development on the Wedge 400 Switch API project located in `/home/rtroiano/repositories/scripts-public/scripts-public/projects/Wedge-400-Switch-API`. It is a FastAPI backend with SQLite persistence emulating switch sensors and ports, serving a glassy Dracula/Nord UI dashboard. It is deployed under systemd and Nginx Basic Auth on 192.168.1.80. Please read the source files, run unit tests, and help me with the next steps."
