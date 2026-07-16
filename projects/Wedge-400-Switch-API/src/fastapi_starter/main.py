import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi_starter.api import router, auth_router
from fastapi_starter.database import init_db

# Load root_path from environment variable to allow dynamic proxy routing
API_ROOT_PATH = os.getenv("API_ROOT_PATH", "/projects/wedge-switch-400-api")

app = FastAPI(
    title="Wedge 400 Switch API",
    version="1.0.0",
    root_path=API_ROOT_PATH,
    description="REST API interface matching OCP Wedge 400 OpenBMC test specifications and switch configuration."
)

@app.on_event("startup")
def startup_event():
    # Initialize SQLite database and seed defaults on startup
    init_db()

app.include_router(router)
app.include_router(auth_router)

@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    return HTMLResponse("Wedge 400 Switch API Dashboard. (Template not found)", status_code=404)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
