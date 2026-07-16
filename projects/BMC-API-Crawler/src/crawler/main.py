import os
import re
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Root path prefix for Nginx proxy routing
API_ROOT_PATH = os.getenv("API_ROOT_PATH", "/projects/bmc-api-crawler")

# Global setting mapping to the target switch REST API
SWITCH_API_URL = os.getenv("SWITCH_API_URL", "http://127.0.0.1:8000/projects/wedge-switch-400-api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"BMC API Crawler starting up. Default Target Switch: {SWITCH_API_URL}")
    yield

app = FastAPI(
    title="BMC API Crawler Service",
    version="1.0.0",
    root_path=API_ROOT_PATH,
    description="Standalone documentation parser that extracts BMC API endpoints and registers them to a mock switch.",
    lifespan=lifespan
)

class CrawlRequest(BaseModel):
    url: str = Field(..., description="The documentation or test file URL to crawl")
    switch_url: str = Field(default=None, description="Optional override switch endpoint URL")

class SettingsUpdateRequest(BaseModel):
    switch_url: str = Field(..., description="The target switch console API base URL")

@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    return HTMLResponse("BMC API Crawler Dashboard. (Template not found)", status_code=404)

@app.get("/api/settings")
def get_settings():
    global SWITCH_API_URL
    return {"switch_url": SWITCH_API_URL}

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    global SWITCH_API_URL
    SWITCH_API_URL = req.switch_url.rstrip("/")
    return {"status": "success", "switch_url": SWITCH_API_URL}

@app.post("/api/crawl")
def post_crawl(req: CrawlRequest):
    global SWITCH_API_URL
    target_switch = req.switch_url.rstrip("/") if req.switch_url else SWITCH_API_URL
    
    # 1. Fetch raw text content from target doc URL
    try:
        response = httpx.get(req.url, timeout=10.0, follow_redirects=True)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch doc URL. Status: {response.status_code}")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"HTTP connection error fetching doc: {exc}")
        
    text = response.text
    
    # 2. Extract potential endpoints
    matches = re.findall(r'/api/sys/[a-zA-Z0-9_/-]+', text)
    cleaned_endpoints = []
    for match in matches:
        cleaned = re.sub(r'[\'\"\\,;\]\)\s]+$', '', match)
        if cleaned.startswith("/api/sys/"):
            cleaned_endpoints.append(cleaned)
            
    unique_endpoints = sorted(list(set(cleaned_endpoints)))
    
    # 3. Filter out static endpoints to prevent collisions
    static_paths = [
        "/api/sys/sensors", "/api/sys/presence", "/api/sys/firmware_info/all", 
        "/api/sys/switch_reset", "/api/sys/ports", "/api/sys/vlans", "/api/sys/lldp", "/api/sys/routes"
    ]
    
    registered_routes = []
    failed_routes = []
    
    # 4. Generate mock payloads and push to the Wedge 400 Switch API
    for path in unique_endpoints:
        if any(path.startswith(static) for static in static_paths):
            continue
            
        payload = {"simulated": True, "endpoint": path}
        if "presence" in path:
            device_name = path.split("/")[-1]
            payload = {"device": device_name, "present": True}
        elif "firmware" in path:
            payload = {"version": "v1.2.3", "active": True, "type": "CPLD"}
        elif "reset" in path or "reboot" in path:
            payload = {"status": "success", "message": "System trigger executed."}
        elif "vdd" in path or "volt" in path:
            payload = {"voltage_v": 1.05, "status": "nominal"}
        elif "mac" in path:
            payload = {"mac_address": "00:1a:2b:3c:4d:5e"}
        elif "cpu" in path:
            payload = {"cpu_utilization_percent": 12.5, "cores": 4}
        elif "eeprom" in path:
            payload = {"eeprom_status": "programmed", "serial": "W400-SCM-123456"}
            
        # POST to Wedge 400 switch dynamic routes register endpoint
        switch_register_url = f"{target_switch}/api/sys/routes"
        try:
            reg_response = httpx.post(
                switch_register_url,
                json={"path": path, "payload": payload},
                timeout=5.0
            )
            if reg_response.status_code == 200:
                registered_routes.append(path)
            else:
                failed_routes.append({"path": path, "error": f"Switch API returned status: {reg_response.status_code}"})
        except Exception as exc:
            failed_routes.append({"path": path, "error": f"Failed to connect to switch at {switch_register_url}: {exc}"})
            
    return {
        "status": "completed",
        "url": req.url,
        "target_switch": target_switch,
        "endpoints_found": unique_endpoints,
        "registered": registered_routes,
        "failed": failed_routes
    }

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
