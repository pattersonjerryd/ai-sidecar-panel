# apps/sidecar/repositories/buffers.py
from __future__ import annotations
from collections import deque
from typing import Deque, Dict, List, TypedDict

class Sample(TypedDict):
    t: float  # unix seconds
    v: float  # value

# In-memory ring buffers per sensor. Easy to swap for SQLite later.
MAX_POINTS: int = 10_000
_DATA: Dict[str, Deque[Sample]] = {}

def _buf(sensor_id: str) -> Deque[Sample]:
    if sensor_id not in _DATA:
        _DATA[sensor_id] = deque(maxlen=MAX_POINTS)
    return _DATA[sensor_id]

def append(sensor_id: str, t: float, v: float) -> None:
    """Append a sample to the sensor's ring buffer."""
    _buf(sensor_id).append({"t": float(t), "v": float(v)})

def all_samples(sensor_id: str) -> List[Sample]:
    """Return a copy of all samples for a sensor (oldest→newest)."""
    return list(_DATA.get(sensor_id, []))

def window(sensor_id: str, cutoff_ts: float) -> List[Sample]:
    """Return samples with t >= cutoff_ts."""
    buf = _DATA.get(sensor_id, [])
    if not buf:
        return []
    # Deque is ordered oldest→newest; filter in order
    return [s for s in buf if s["t"] >= float(cutoff_ts)]

def clear(sensor_id: str) -> None:
    """Clear a sensor's buffer (useful for tests)."""
    _DATA.pop(sensor_id, None)

def sensors() -> List[str]:
    """List sensor IDs currently present."""
    return list(_DATA.keys())
