# apps/sidecar/collector_sim.py
"""
Cortex Link – Collector Simulator
Generates a few synthetic sensor readings every second and writes them to SQLite.
Keeps a tiny in-memory history per sensor to compute a baseline (EWMA),
a rolling z-score, and a simple slope estimate.

This module is passive until you call `start()` from your FastAPI startup hook.
"""

from __future__ import annotations
import asyncio
import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Deque, List

from apps.sidecar.db import add_reading  # uses the helper we defined in db.py


# --- Tunables ---------------------------------------------------------------
TICK_SEC = 1.0           # write frequency
HIST_LEN = 120           # rolling window for stats
EWMA_ALPHA = 0.15        # smoothing for baseline
SENSORS = [
    # id,          nominal, unit,  noise,  drift
    ("A1",  "Leak Zone 1",  "%",     0.8,   0.000),   # slow/no drift, occasional spikes
    ("A2",  "Humidity",     "%RH",   1.2,   0.0005),
    ("A3",  "Temp Inlet",   "°C",    0.3,   0.0002),
]
NOMINALS = {"A1": 10.0, "A2": 35.0, "A3": 24.0}


# --- Simple per-sensor state -----------------------------------------------
@dataclass
class SensorState:
    sid: str
    label: str
    unit: str
    noise: float
    drift: float
    baseline: float = 0.0
    history: Deque[float] = field(default_factory=lambda: deque(maxlen=HIST_LEN))
    times:   Deque[float] = field(default_factory=lambda: deque(maxlen=HIST_LEN))

    def step(self, t: float) -> float:
        base = NOMINALS.get(self.sid, 0.0)
        # slow drift + gaussian noise
        val = base + (self.drift * t) + random.gauss(0.0, self.noise)

        # occasional spike for A1 to simulate leak “events”
        if self.sid == "A1" and random.random() < 0.04:
            val += random.uniform(5, 12)

        # clamp percentages
        if self.unit in ("%", "%RH"):
            val = max(0.0, min(100.0, val))

        # update history + ewma baseline
        self.history.append(val)
        self.times.append(t)
        self.baseline = (EWMA_ALPHA * val) + (1.0 - EWMA_ALPHA) * (self.baseline or val)
        return val

    def stats(self):
        # rolling mean/std (population)
        n = len(self.history)
        if n < 3:
            return 0.0, 0.0, 0.0  # residual, z, slope/min
        mu = sum(self.history) / n
        var = sum((x - mu) ** 2 for x in self.history) / n
        sd = math.sqrt(max(var, 1e-12))
        residual = (self.history[-1] - self.baseline)

        # slope via simple least squares over timestamps
        xs = list(self.times)
        ys = list(self.history)
        xbar = sum(xs) / n
        ybar = sum(ys) / n
        num = sum((xs[i] - xbar) * (ys[i] - ybar) for i in range(n))
        den = sum((xs[i] - xbar) ** 2 for i in range(n)) or 1e-12
        slope_per_sec = num / den
        slope_per_min = slope_per_sec * 60.0

        z = (ys[-1] - mu) / sd
        return residual, z, slope_per_min


class CollectorSim:
    """
    Start/stop a background task that writes readings into the DB every TICK_SEC.
    """
    def __init__(self, tick_sec: float = TICK_SEC):
        self.tick_sec = tick_sec
        self._task: asyncio.Task | None = None
        self._running = False
        self._t0 = time.time()

        self.sensors: Dict[str, SensorState] = {
            sid: SensorState(sid, label, unit, noise, drift)
            for (sid, label, unit, noise, drift) in SENSORS
        }

    async def _loop(self):
        while self._running:
            t = time.time() - self._t0
            for s in self.sensors.values():
                val = s.step(t)
                residual, z, slope_min = s.stats()
                # store into DB using our helper (ts will be UTC via sqlite "now")
                await add_reading(
                    sensor_id=s.sid,
                    value=float(val),
                    baseline=float(s.baseline),
                    z=float(z),
                    slope=float(slope_min),
                )
            await asyncio.sleep(self.tick_sec)

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=self.tick_sec * 2)
            except asyncio.TimeoutError:
                self._task.cancel()

# Convenience factory
def create_collector() -> CollectorSim:
    return CollectorSim()
