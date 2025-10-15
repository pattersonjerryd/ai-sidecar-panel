# apps/sidecar/services/predictive_service.py
from __future__ import annotations
import time
import numpy as np
from typing import List
from apps.sidecar.repositories import buffers
from apps.sidecar.models.predictive import SeriesResp

# --- internal math helpers --------------------------------------------------

def _ewma(y: np.ndarray, alpha: float) -> np.ndarray:
    """Exponentially weighted moving average."""
    if y.size == 0:
        return y
    out = np.empty_like(y, dtype=float)
    out[0] = y[0]
    for i in range(1, y.size):
        out[i] = alpha * y[i - 1] + (1 - alpha) * out[i - 1]
    return out


def _one_step(y: np.ndarray, alpha: float) -> np.ndarray:
    """Shift EWMA to make one-step-ahead predictions."""
    if y.size == 0:
        return y
    base = _ewma(y, alpha)
    preds = np.roll(base, 1)
    preds[0] = base[0]
    return preds


def _z_anoms(y: np.ndarray, preds: np.ndarray, z: float = 3.0) -> np.ndarray:
    """Simple z-score anomaly detection."""
    if y.size < 5:
        return np.zeros_like(y, dtype=bool)
    resid = y - preds
    mu = resid.mean()
    sd = resid.std() + 1e-9
    return np.abs((resid - mu) / sd) >= z


def _step(ts: np.ndarray) -> float:
    """Median sampling period."""
    if ts.size < 2:
        return 1.0
    d = np.diff(ts)
    m = np.median(d)
    return float(m if m > 0 else 1.0)


def _future(y: np.ndarray, ts: np.ndarray, steps: int, alpha: float):
    """Generate future timestamps and flat predictions."""
    if y.size == 0 or ts.size == 0:
        return np.array([]), np.array([])
    last = _ewma(y, alpha)[-1]
    s = _step(ts)
    start = ts[-1] + s
    fts = start + s * np.arange(steps)
    fy = np.full(steps, last)
    return fts, fy

# --- public interface -------------------------------------------------------

def ingest_point(sensor_id: str, v: float, t: float | None) -> None:
    """Append a new observation."""
    buffers.append(sensor_id, t or time.time(), float(v))


def get_series(sensor_id: str, window_s: int, alpha: float, future_steps: int) -> SeriesResp:
    """Return predictive overlay data for one sensor."""
    buf = buffers.all_samples(sensor_id)
    if not buf:
        return SeriesResp(
            sensor_id=sensor_id,
            ts=[], vals=[], preds=[], anomalies_idx=[],
            future_ts=[], future_preds=[]
        )

    cutoff = time.time() - window_s
    win = [s for s in buf if s["t"] >= cutoff] or buf[-min(len(buf), 2):]

    ts = np.array([s["t"] for s in win], dtype=float)
    y  = np.array([s["v"] for s in win], dtype=float)

    preds = _one_step(y, alpha)
    anoms = _z_anoms(y, preds)
    ai = [i for i, f in enumerate(anoms) if f]

    fts, fy = _future(y, ts, future_steps, alpha)

    return SeriesResp(
        sensor_id=sensor_id,
        ts=ts.tolist(),
        vals=y.tolist(),
        preds=preds.tolist(),
        anomalies_idx=ai,
        future_ts=fts.tolist(),
        future_preds=fy.tolist(),
    )
