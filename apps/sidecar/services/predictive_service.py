# apps/sidecar/services/predictive_service.py
from __future__ import annotations
import time
from typing import List
from apps.sidecar.repositories import buffers
from apps.sidecar.models.predictive import SeriesResp
from apps.sidecar.core.anomaly import run_predictions

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

    ts = [s["t"] for s in win]
    vals = [s["v"] for s in win]

    # Shared math so API == worker behavior
    preds, future_ts, future_preds, anomalies_idx, _z = run_predictions(
        ts, vals, window_s=window_s, alpha=alpha, future_steps=future_steps
    )

    return SeriesResp(
        sensor_id=sensor_id,
        ts=ts,
        vals=vals,
        preds=preds,
        anomalies_idx=anomalies_idx,
        future_ts=future_ts,
        future_preds=future_preds,
    )
