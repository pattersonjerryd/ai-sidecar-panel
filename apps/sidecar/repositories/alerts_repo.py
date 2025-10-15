# apps/sidecar/repositories/alerts_repo.py
from __future__ import annotations
from collections import deque
from typing import Deque, Dict, List
from apps.sidecar.models.alerts import AlertEvent

# Per-sensor rolling store of alert events (in-memory).
# Easy to swap for SQLite/Influx later.
MAX_ALERTS_PER_SENSOR = 500
_STORE: Dict[str, Deque[AlertEvent]] = {}

def _dq(sensor_id: str) -> Deque[AlertEvent]:
    if sensor_id not in _STORE:
        _STORE[sensor_id] = deque(maxlen=MAX_ALERTS_PER_SENSOR)
    return _STORE[sensor_id]

def replace_all(sensor_id: str, items: List[AlertEvent]) -> None:
    """Replace the alert list for a sensor (used by rebuild)."""
    dq = _dq(sensor_id)
    dq.clear()
    dq.extend(items[-MAX_ALERTS_PER_SENSOR:])

def append(sensor_id: str, item: AlertEvent) -> None:
    _dq(sensor_id).append(item)

def recent(sensor_id: str, limit: int = 50) -> List[AlertEvent]:
    dq = _dq(sensor_id)
    if limit <= 0:
        return list(dq)
    return list(dq)[-limit:]

def clear(sensor_id: str) -> None:
    _STORE.pop(sensor_id, None)
