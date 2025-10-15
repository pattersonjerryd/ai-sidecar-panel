# predictive.py
# Lightweight predictive analytics: EWMA smoothing, residual z-score anomaly detection,
# and short-term future projection.

from __future__ import annotations
from typing import List, Tuple, Dict
import numpy as np


def ewma(y: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Exponentially Weighted Moving Average."""
    if y.size == 0:
        return y
    out = np.empty_like(y, dtype=float)
    out[0] = y[0]
    for i in range(1, y.size):
        out[i] = alpha * y[i - 1] + (1 - alpha) * out[i - 1]
    return out


def one_step_ahead_preds(y: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Predict y[i] using EWMA up to i−1."""
    if y.size == 0:
        return y
    baseline = ewma(y, alpha=alpha)
    preds = np.roll(baseline, 1)
    preds[0] = baseline[0]
    return preds


def zscore_anomalies(y: np.ndarray, preds: np.ndarray, z_thresh: float = 3.0) -> np.ndarray:
    """Return boolean mask where residual z-score >= threshold."""
    if y.size < 5:
        return np.zeros_like(y, dtype=bool)
    resid = y - preds
    mu, sd = np.mean(resid), np.std(resid) + 1e-9
    z = (resid - mu) / sd
    return np.abs(z) >= z_thresh


def infer_step_seconds(ts: np.ndarray) -> float:
    """Infer sampling period from timestamps."""
    if ts.size < 2:
        return 1.0
    diffs = np.diff(ts)
    med = np.median(diffs)
    return float(med if med > 0 else 1.0)


def project_future(y: np.ndarray, ts: np.ndarray, steps: int = 30, alpha: float = 0.3) -> Tuple[np.ndarray, np.ndarray]:
    """Flat short-term projection using last EWMA value."""
    if y.size == 0 or ts.size == 0:
        return np.array([], dtype=float), np.array([], dtype=float)
    baseline = ewma(y, alpha=alpha)
    last_hat = float(baseline[-1])
    step_s = infer_step_seconds(ts)
    start = float(ts[-1]) + step_s
    future_ts = start + step_s * np.arange(steps, dtype=float)
    future_yhat = np.full(steps, last_hat, dtype=float)
    return future_ts, future_yhat


def analyze_series(ts: List[float], vals: List[float], alpha: float = 0.3, future_steps: int = 30) -> Dict:
    """Given timestamps and values, return predictions, anomalies, and projections."""
    if len(ts) != len(vals):
        raise ValueError("ts and vals must be same length")
    arr_ts = np.array(ts, dtype=float)
    arr_y = np.array(vals, dtype=float)

    preds = one_step_ahead_preds(arr_y, alpha=alpha)
    anomalies = zscore_anomalies(arr_y, preds)
    fut_ts, fut_pred = project_future(arr_y, arr_ts, steps=future_steps, alpha=alpha)

    return {
        "preds": preds.tolist(),
        "anomalies_mask": anomalies.astype(bool).tolist(),
        "future_ts": fut_ts.tolist(),
        "future_preds": fut_pred.tolist(),
    }
