# BMC API Crawler Service

The Standalone BMC API Crawler is a FastAPI-based service designed to fetch raw documentation or test file URLs, extract REST endpoints (following `/api/sys/...`), and dynamically register them onto the target Wedge 400 Mock Switch.

## Features
- **Lifespan-Managed FastAPI Backend**: Uses modern lifespan handlers for cleaner startup telemetry.
- **Glassy Theme-Swappable Console**: Dracula (dark) and Nord (light) responsive UI with beveled panels.
- **Dynamic Endpoint Registration**: Translates scraped endpoint names to dynamic mock payloads.

---

## Installation & Setup

1. **Navigate to the Project Directory**:
   ```bash
   cd projects/BMC-API-Crawler
   ```

2. **Initialize the Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -e .[dev]
   ```

---

## Running the App

### Running Locally
To launch the development server locally on port 8001:
```bash
.venv/bin/uvicorn crawler.main:app --host 127.0.0.1 --port 8001
```

### Deployed Server
The service is automatically deployed using `systemd` and routed under Nginx.
- **Service Name**: `bmc-crawler.service`
- **Location Prefix**: `/projects/bmc-api-crawler`
- **Production URL**: `http://192.168.1.80/projects/bmc-api-crawler`

---

## Validation & Testing

### Running Tests
To run the mock test suite using `pytest`:
```bash
.venv/bin/pytest
```

### Running Build/Compile Checks
To run the compile and syntax checks locally:
```bash
./build.sh
```

---

## Deployment

Deploy changes to the remote development server:
```bash
./deploy.sh
```
