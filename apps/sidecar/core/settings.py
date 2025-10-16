from pathlib import Path
import os

def _getenv_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _getenv_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default

# --- Data directory and SQLite configuration (no Pydantic needed) ---
DATA_DIR = Path(os.getenv("SIDECAR_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = os.getenv("SIDECAR_DB_PATH", str(DATA_DIR / "sidecar.db"))

# --- Retention window used by optional pruning ---
RETENTION_HOURS = _getenv_int("SIDECAR_RETENTION_HOURS", 24)

# --- Sampling & anomaly knobs (used by simulator/ingest path) ---
SAMPLE_INTERVAL_S = _getenv_int("SIDECAR_SAMPLE_INTERVAL_S", 5)  # dev simulator cadence
ANOMALY_Z_THRESHOLD = _getenv_float("SIDECAR_ANOMALY_Z_THRESHOLD", 3.0)

# --- API token for /ingest ---
API_TOKEN = os.getenv("SIDECAR_API_TOKEN", "dev-secret-change-me")

# --- Notifications ---
# Per-sensor dedupe window (seconds) to avoid paging storms
NOTIFY_DEDUP_SECONDS = _getenv_int("SIDECAR_NOTIFY_DEDUP_SECONDS", 300)
# Quiet hours (local time) in "start-end" 24h format, e.g., "22-6"; empty = disabled
QUIET_HOURS = os.getenv("SIDECAR_QUIET_HOURS", "")

# Email (SMTP) — stdlib only
EMAIL_ENABLED = os.getenv("SIDECAR_EMAIL_ENABLED", "0") == "1"
EMAIL_SMTP_HOST = os.getenv("SIDECAR_EMAIL_SMTP_HOST", "")
EMAIL_SMTP_PORT = _getenv_int("SIDECAR_EMAIL_SMTP_PORT", 587)
EMAIL_SMTP_TLS = os.getenv("SIDECAR_EMAIL_SMTP_TLS", "1") == "1"  # startTLS if True; else implicit SSL
EMAIL_USERNAME = os.getenv("SIDECAR_EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("SIDECAR_EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("SIDECAR_EMAIL_FROM", "")
EMAIL_TO = [s for s in os.getenv("SIDECAR_EMAIL_TO", "").split(",") if s.strip()]

# Webhook — stdlib urllib POST
WEBHOOK_ENABLED = os.getenv("SIDECAR_WEBHOOK_ENABLED", "0") == "1"
WEBHOOK_URL = os.getenv("SIDECAR_WEBHOOK_URL", "")

# Optional: explicitly export names
__all__ = [
    "DATA_DIR",
    "DB_PATH",
    "RETENTION_HOURS",
    "SAMPLE_INTERVAL_S",
    "ANOMALY_Z_THRESHOLD",
    "API_TOKEN",
    "NOTIFY_DEDUP_SECONDS",
    "QUIET_HOURS",
    "EMAIL_ENABLED",
    "EMAIL_SMTP_HOST",
    "EMAIL_SMTP_PORT",
    "EMAIL_SMTP_TLS",
    "EMAIL_USERNAME",
    "EMAIL_PASSWORD",
    "EMAIL_FROM",
    "EMAIL_TO",
    "WEBHOOK_ENABLED",
    "WEBHOOK_URL",
]
