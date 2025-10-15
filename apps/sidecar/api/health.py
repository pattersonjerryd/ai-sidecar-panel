# apps/sidecar/api/health.py
from __future__ import annotations
import time
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health():
    """Simple liveness probe with server timestamp."""
    return {"status": "ok", "ts": time.time()}
