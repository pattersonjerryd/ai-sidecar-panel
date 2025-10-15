# apps/sidecar/services/alerts_service.py
from __future__ import annotations
from typing import List
import numpy as np
import time

from apps.sidecar.repositories import buffers
from apps.sidecar.repositories import alerts_repo
from apps.sidecar.models.alerts import AlertEvent, AlertsResp

# ---------- local helpers (mirror predictive math) -----------------

def _ewma(y: np.ndarray, alpha: float) -> np.ndarray:
    if y.size == 0:
        return y
    out = np.empty_like(y, dtype=float)
    out[0] = y[0]
    for i in range(1, y.size):
        out[i] = alpha * y[i - 1] + (1 - alpha) * out[i - 1]
    return out

def _one_step(y: np.ndarray, alpha: float) -> np.ndarray:
    if y.size == 0:
        return y
    base = _ewma(y, alpha)
    preds = np.roll(base, 1)
    preds[0] = base[0]
    return preds

def _z_scores(y: np.ndarray, preds: np.ndarray) -> np.ndarray:
    if y.size < 2:
        return np.zeros_like(y, dtype=float)
    resid = y - preds
    mu = float(resid.mean())
    sd = float(resid.std() + 1e-9)
    return (resid - mu) / sd

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

    ts = np.array([s["t"] for s in win], dtype=float)
    y  = np.array([s["v"] for s in win], dtype=float)

    preds = _one_step(y, alpha)
    z = _z_scores(y, preds)

    items: List[AlertEvent] = []
    for i in range(z.size):
        if abs(z[i]) >= z_thresh:
            items.append(AlertEvent(
                sensor_id=sensor_id,
                t=float(ts[i]),
                v=float(y[i]),
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
