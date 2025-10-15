# apps/sidecar/models/predictive.py
from __future__ import annotations
from typing import List
from pydantic import BaseModel

class SeriesResp(BaseModel):
    """
    Canonical response schema for the predictive overlay endpoint.
    Keeps HTTP layer simple and lets services/repositories evolve independently.
    """
    sensor_id: str
    ts: List[float]           # UNIX seconds for each observed point
    vals: List[float]         # actual observations
    preds: List[float]        # one-step-ahead predictions aligned to ts
    anomalies_idx: List[int]  # indices into ts/vals flagged as anomalies
    future_ts: List[float]    # projected timestamps (UNIX seconds)
    future_preds: List[float] # projected values aligned to future_ts
