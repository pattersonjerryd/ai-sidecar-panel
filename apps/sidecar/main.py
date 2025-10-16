# apps/sidecar/main.py
from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Routers (HTTP layer)
from apps.sidecar.api.health import router as health_router
from apps.sidecar.api.predictive import router as predictive_router
from apps.sidecar.api.alerts import router as alerts_router
from apps.sidecar.api.ingest import router as ingest_router

# Simulator (import concrete function directly)
from apps.sidecar.workers.simulator import start as start_simulator

# -------- Config --------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_HTML = STATIC_DIR / "index.html"

APP_TITLE = "Sidecar Panel"
APP_VERSION = "0.4"

# Toggle the built-in data simulator (turn off when using real sensors)
ENABLE_SIMULATOR = True
SIM_SENSOR_ID = "ai_test"
SIM_PERIOD_SEC = 1.0

# -------- App --------
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# Dev CORS (relax for now; tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static assets (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Home → serve dashboard
@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    if INDEX_HTML.exists():
        return HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Sidecar</h1><p>No index.html found in /static.</p>")

# API routers
app.include_router(health_router)       # /health
app.include_router(predictive_router)   # /predictive/series, /predictive/ingest
app.include_router(alerts_router)       # /alerts
app.include_router(ingest_router)       # /ingest

# Backgrounds (simulator)
@app.on_event("startup")
def _start_backgrounds() -> None:
    if ENABLE_SIMULATOR:
        start_simulator(sensor_id=SIM_SENSOR_ID, period=SIM_PERIOD_SEC)
