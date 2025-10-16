# apps/sidecar/services/alerts_service.py
from __future__ import annotations
from typing import List
import time

from apps.sidecar.repositories import buffers
from apps.sidecar.repositories import alerts_repo
from apps.sidecar.models.alerts import AlertEvent, AlertsResp
from apps.sidecar.core.anomaly import run_predictions

# ---------- public API ---------------------------------------------

def rebuild_alerts(sensor_id: str, *, window_s: int = 600, alpha: float = 0.3, z_thresh: float = 3.0) -> None:
    """
    Recompute anomalies over the rolling window and store as alert events.
    """
    all_samples = buffers.all_samples(sensor_id)
    if not all_samples:
        alerts_repo.replace_all(sensor_id, [])
        return

    cutoff = time.time() - window_s
    win = [s for s in all_samples if s["t"] >= cutoff] or all_samples[-min(len(all_samples), 2):]

    ts = [s["t"] for s in win]
    vals = [s["v"] for s in win]

    # Use shared anomaly detection logic
    preds, _fts, _fp, anomalies_idx, z = run_predictions(
        ts, vals, window_s=window_s, alpha=alpha, future_steps=0
    )

    items: List[AlertEvent] = []
    for i in anomalies_idx:
        if i < len(ts) and i < len(vals) and i < len(z):
            items.append(AlertEvent(
                sensor_id=sensor_id,
                t=float(ts[i]),
                v=float(vals[i]),
                z=float(z[i]),
                msg=f"Anomaly z={z[i]:.2f} at t={ts[i]:.0f}"
            ))

    alerts_repo.replace_all(sensor_id, items)

def recent(sensor_id: str, limit: int = 50) -> AlertsResp:
    """Return recent alerts for UI consumption (without recomputation)."""
    return AlertsResp(sensor_id=sensor_id, items=alerts_repo.recent(sensor_id, limit=limit))

def refresh_and_get(sensor_id: str, *, window_s: int = 600, alpha: float = 0.3, z_thresh: float = 3.0, limit: int = 50) -> AlertsResp:
    """
    Rebuild alerts from current buffer, then return the last `limit` items.
    Use this from the HTTP route for up-to-date UI.
    """
    rebuild_alerts(sensor_id, window_s=window_s, alpha=alpha, z_thresh=z_thresh)
    return recent(sensor_id, limit=limit)
