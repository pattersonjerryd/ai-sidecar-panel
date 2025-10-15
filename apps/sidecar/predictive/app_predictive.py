# app_predictive.py
# FastAPI router exposing predictive overlay endpoints.

from __future__ import annotations
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict
import time
from collections import deque
from .predictive import analyze_series

router = APIRouter(prefix="/predictive", tags=["predictive"])

# simple in-memory sensor store
DATA: Dict[str, deque] = {}
MAX_POINTS = 10_000


class IngestReq(BaseModel):
    sensor_id: str = "ai_test"
    t: float | None = None
    v: float


@router.post("/ingest")
def ingest(req: IngestReq) -> Dict[str, str]:
    if req.sensor_id not in DATA:
        DATA[req.sensor_id] = deque(maxlen=MAX_POINTS)
    ts = req.t or time.time()
    DATA[req.sensor_id].append({"t": ts, "v": req.v})
    return {"status": "ok"}


class SeriesResp(BaseModel):
    sensor_id: str
    ts: List[float]
    vals: List[float]
    preds: List[float]
    anomalies_idx: List[int]
    future_ts: List[float]
    future_preds: List[float]


@router.get("/series", response_model=SeriesResp)
def get_series(
    sensor_id: str = Query("ai_test"),
    window_s: int = Query(600),
    alpha: float = Query(0.3),
    future_steps: int = Query(30),
):
    if sensor_id not in DATA:
        return SeriesResp(sensor_id=sensor_id, ts=[], vals=[], preds=[], anomalies_idx=[], future_ts=[], future_preds=[])
    buf = list(DATA[sensor_id])
    cutoff = time.time() - window_s
    window = [s for s in buf if s["t"] >= cutoff]
    if len(window) < 2:
        window = buf[-min(len(buf), 2):]
    ts = [s["t"] for s in window]
    vals = [s["v"] for s in window]
    analysis = analyze_series(ts, vals, alpha=alpha, future_steps=future_steps)
    anomalies_idx = [i for i, flag in enumerate(analysis["anomalies_mask"]) if flag]
    return SeriesResp(
        sensor_id=sensor_id,
        ts=ts,
        vals=vals,
        preds=analysis["preds"],
        anomalies_idx=anomalies_idx,
        future_ts=analysis["future_ts"],
        future_preds=analysis["future_preds"],
    )
