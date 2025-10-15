# apps/sidecar/api/alerts.py
from __future__ import annotations
from fastapi import APIRouter, Query
from apps.sidecar.models.alerts import AlertsResp
from apps.sidecar.services import alerts_service as svc

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("", response_model=AlertsResp)
def alerts(
    sensor_id: str = Query("ai_test", description="Sensor identifier"),
    window_s: int = Query(600, ge=1, description="Rolling window (seconds) used to detect anomalies"),
    alpha: float = Query(0.3, ge=0.01, le=0.99, description="EWMA smoothing"),
    z_thresh: float = Query(3.0, ge=1.0, le=10.0, description="Z-score threshold for anomalies"),
    limit: int = Query(25, ge=1, le=200, description="Max alerts to return (most recent first)")
) -> AlertsResp:
    """
    Recompute anomalies over the rolling window and return the most recent `limit` alerts.
    """
    return svc.refresh_and_get(
        sensor_id,
        window_s=window_s,
        alpha=alpha,
        z_thresh=z_thresh,
        limit=limit,
    )
