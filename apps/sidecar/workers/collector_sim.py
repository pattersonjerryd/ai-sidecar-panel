from __future__ import annotations
import time
import math
import random
from typing import Optional

from apps.sidecar.repositories.storage.sample_repo import SampleRepo
from apps.sidecar.repositories.storage.alert_repo import AlertRepo
from apps.sidecar.core.anomaly import run_predictions
from apps.sidecar.core.settings import SAMPLE_INTERVAL_S, ANOMALY_Z_THRESHOLD
from apps.sidecar.services.notify import notify_alert

# NOTE: This is a lightweight dev simulator that:
# 1) generates a smooth signal with occasional dips/spikes
# 2) appends samples to SQLite (SampleRepo)
# 3) computes Z in-process and writes alerts when |z| >= threshold

def simulate_value(t: float) -> float:
    base = 50.0 + 3.0 * math.sin(t / 60.0)  # slow wave
    noise = random.uniform(-0.4, 0.4)
    # rare shock
    if random.random() < 0.01:
        shock = random.choice([-10.0, +8.0])
    else:
        shock = 0.0
    return base + noise + shock

def run_simulator(sensor_id: str = "ai_test", interval_s: Optional[int] = None) -> None:
    repo = SampleRepo()
    alerts = AlertRepo()
    dt = interval_s or SAMPLE_INTERVAL_S
    history_ts: list[float] = []
    history_vals: list[float] = []
    while True:
        t = time.time()
        v = simulate_value(t)
        repo.add_sample(sensor_id, t, v)
        # maintain a small in-memory tail for z-score computation
        history_ts.append(t)
        history_vals.append(v)
        if len(history_ts) > 600:  # keep ~50 minutes at 5s cadence
            history_ts = history_ts[-600:]
            history_vals = history_vals[-600:]
        # compute z & flag
        preds, _fts, _fp, _idx, z = run_predictions(
            history_ts, history_vals, window_s=600, alpha=0.3, future_steps=0
        )
        if z:
            z_last = z[-1]
            if abs(z_last) >= ANOMALY_Z_THRESHOLD:
                msg = f"Anomaly z={z_last:.2f} at t={int(t)}"
                alerts.add_alert(sensor_id, t, v, z_last, msg)
                try:
                    notify_alert(sensor_id=sensor_id, t=t, v=v, z=z_last, msg=msg)
                except Exception:
                    pass
        time.sleep(dt)

if __name__ == "__main__":
    # Run:  python -m apps.sidecar.workers.collector_sim
    run_simulator()
