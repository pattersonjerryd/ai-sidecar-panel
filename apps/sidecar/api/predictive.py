# apps/sidecar/api/predictive.py
from __future__ import annotations
from fastapi import APIRouter, Query
from apps.sidecar.models.predictive import SeriesResp
from apps.sidecar.services.predictive_service import get_series, ingest_point

router = APIRouter(prefix="/predictive", tags=["predictive"])

@router.get("/series", response_model=SeriesResp)
def series(
    sensor_id: str = Query("ai_test"),
    window_s: int = Query(600, ge=1, description="Rolling window size in seconds"),
    alpha: float = Query(0.3, ge=0.01, le=0.99, description="EWMA smoothing factor"),
    future_steps: int = Query(30, ge=0, description="How many future points to predict")
) -> SeriesResp:
    """Return rolling predictive overlay for one sensor."""
    return get_series(sensor_id, window_s, alpha, future_steps)

@router.post("/ingest")
def ingest(sensor_id: str, v: float, t: float | None = None):
    """Manually append a sample (for testing or manual injection)."""
    ingest_point(sensor_id, v, t)
    return {"status": "ok"}
