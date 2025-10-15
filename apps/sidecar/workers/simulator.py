# apps/sidecar/workers/simulator.py
from __future__ import annotations
import time
import math
import random
import threading

from apps.sidecar.repositories.buffers import append

def start(sensor_id: str = "ai_test", period: float = 1.0) -> None:
    """
    Start a background thread that appends synthetic data every `period` seconds.
    Produces a smooth baseline with small noise and occasional jump anomalies.
    """
    def loop() -> None:
        t0 = time.time()
        i = 0
        while True:
            base = 50.0 + 5.0 * math.sin(i / 30.0) + 0.01 * i
            v = base + random.uniform(-0.7, 0.7)

            # rare jump anomalies
            if random.random() < 0.02:
                v += random.choice([-12.0, 12.0])

            append(sensor_id, t0 + i * period, float(v))
            time.sleep(period)
            i += 1

    threading.Thread(target=loop, daemon=True).start()
