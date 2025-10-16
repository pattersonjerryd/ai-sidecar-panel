from __future__ import annotations

import time
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from apps.sidecar.repositories.storage.sample_repo import SampleRepo
from apps.sidecar.repositories.storage.alert_repo import AlertRepo
from apps.sidecar.core.anomaly import run_predictions
from apps.sidecar.core.security import require_api_key
from apps.sidecar.core.settings import ANOMALY_Z_THRESHOLD
from apps.sidecar.services.notify import notify_alert

router = APIRouter(tags=["ingest"])

class IngestPayload(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=128)
    v: float
    t: Optional[float] = Field(None, description="Epoch seconds; defaults to server time")

@router.post("/ingest")
async def ingest_reading(
    payload: IngestPayload,
    _auth: None = Depends(require_api_key),
):
    """
    Ingest a single reading. Minimal behavior:
      1) Append sample to SQLite
      2) Recompute z on recent window
      3) If |z_last| >= threshold, persist an alert
    Returns a tiny ack so devices can confirm write.
    """
    sensor_id = payload.sensor_id
    t = float(payload.t) if payload.t is not None else time.time()
    v = float(payload.v)

    samples = SampleRepo()
    alerts = AlertRepo()

    # 1) write sample
    samples.add_sample(sensor_id, t, v)

    # 2) recompute on recent history (keep it small for fast writes)
    series = samples.get_series(sensor_id=sensor_id, start_ts=None, end_ts=None, limit=600)
    ts = [tv[0] for tv in series]
    vals = [tv[1] for tv in series]
    preds, _fts, _fp, _idx, z = run_predictions(ts, vals, window_s=600, alpha=0.3, future_steps=0)

    # 3) optional alert
    z_last = z[-1] if z else 0.0
    alerted = False
    if abs(z_last) >= ANOMALY_Z_THRESHOLD:
        msg = f"ingest anomaly z={z_last:.2f}"
        alerts.add_alert(sensor_id=sensor_id, t=t, v=v, z=z_last, msg=msg)
        # best-effort fanout (email/webhook); do not block request if it fails
        try:
            notify_alert(sensor_id=sensor_id, t=t, v=v, z=z_last, msg=msg)
        except Exception:
            pass
        alerted = True

    return {
        "ok": True,
        "sensor_id": sensor_id,
        "t": t,
        "v": v,
        "z": z_last,
        "alerted": alerted,
    }
