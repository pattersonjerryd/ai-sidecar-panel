from __future__ import annotations

from typing import List, Tuple
import math

def ewma(series: List[float], alpha: float) -> List[float]:
    """Simple EWMA baseline."""
    if not series:
        return []
    out = [series[0]]
    a = float(alpha)
    for x in series[1:]:
        out.append(a * x + (1 - a) * out[-1])
    return out

def z_scores(vals: List[float], baseline: List[float], window_s: int) -> List[float]:
    """
    Z scores based on residuals using a rolling std over the same window length (samples).
    Assumes vals and baseline are aligned and same length.
    """
    n = len(vals)
    if n == 0:
        return []
    # crude rolling std over residuals with a minimum epsilon
    res = [vals[i] - baseline[i] for i in range(n)]
    w = max(5, min(n, int(window_s)))  # fallback if caller passes seconds; UI already passes 600
    out: List[float] = []
    for i in range(n):
        lo = max(0, i - w + 1)
        window = res[lo : i + 1]
        mu = sum(window) / len(window)
        var = sum((r - mu) ** 2 for r in window) / max(1, (len(window) - 1))
        sd = math.sqrt(var) if var > 1e-9 else 1e-6
        out.append((res[i] - mu) / sd)
    return out

def project_future(last_value: float, steps: int) -> List[float]:
    """Hold-last-value projection for now (UI expects something)."""
    return [last_value] * max(0, int(steps))

def run_predictions(
    ts: List[float], vals: List[float], window_s: int, alpha: float, future_steps: int
) -> Tuple[List[float], List[float], List[float], List[int], List[float]]:
    """
    Returns: preds, future_ts, future_preds, anomalies_idx, z
    Keeps the math minimal & deterministic so API and worker share behavior.
    """
    preds = ewma(vals, alpha) if vals else []
    z = z_scores(vals, preds, window_s) if vals else []
    future_ts = []
    future_preds = project_future(preds[-1], future_steps) if preds else []
    anomalies_idx = [i for i, z_i in enumerate(z) if abs(z_i) >= 3.0]
    return preds, future_ts, future_preds, anomalies_idx, z
