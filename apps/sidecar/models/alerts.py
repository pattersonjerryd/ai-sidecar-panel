# apps/sidecar/models/alerts.py
from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel

AlertKind = Literal["anomaly"]

class AlertEvent(BaseModel):
    sensor_id: str
    t: float          # unix seconds
    v: float          # value at time t
    z: float          # residual z-score at time t
    kind: AlertKind = "anomaly"
    msg: str | None = None

class AlertsResp(BaseModel):
    sensor_id: str
    items: List[AlertEvent]
