# AI Sidecar Panel — System Diagram

> High-level flow of data and responsibilities. Keep this document updated as modules evolve.

---

## Topology (Mermaid)

```mermaid
flowchart LR
  subgraph Sensor Layer
    S1[Simulated Sensor\napps/sidecar/workers/simulator.py]
  end

  subgraph Buffer/Repo Layer
    B[In-mem Buffers + Simple Store\napps/sidecar/repositories/]
  end

  subgraph Services
    P[Predictive Service\nEWMA + z-score\napps/sidecar/services/predictive_service.py]
    A[Alerts Repo/Service\napps/sidecar/repositories/alerts_repo.py]
  end

  subgraph API (FastAPI Routers)
    R1[/health/]
    R2[/predictive/series]
    R3[/predictive/ingest]
    R4[/alerts]
  end

  subgraph UI (Static)
    UI[index.html + css\nChart.js + fetch()]
  end

  S1 -- push samples --> B
  B  -- read window --> P
  P  -- preds + anomalies --> A
  P  -- JSON --> R2
  B  -- JSON --> R3
  A  -- JSON --> R4
  R1 --- UI
  R2 --- UI
  R3 --- UI
  R4 --- UI
```

---

## Module Responsibilities

- **workers/simulator.py**
  - Generates baseline + noise with rare spikes.
  - Periodic write to buffer via repository API.
  - Config: `SIM_SENSOR_ID`, `SIM_PERIOD_SEC`, `ENABLE_SIMULATOR`.

- **repositories/**
  - `buffers.py`: ring buffer / time-series append + window queries.
  - `alerts_repo.py`: append + list recent anomalies per sensor.

- **services/predictive_service.py**
  - EWMA baseline, one-step prediction, short “future” projection.
  - Anomaly flagging via z-score over residuals.
  - Returns `{ ts, vals, preds, future_ts, future_preds, anomalies_idx }`.

- **api/**
  - `health.py`: uptime & status.
  - `predictive.py`:
    - `GET /predictive/series`: build windowed series + predictions.
    - `POST /predictive/ingest`: optional manual/sample injection.
  - `alerts.py`: `GET /alerts`: recent anomaly events.

- **static/**
  - `index.html`: Chart.js (Actual, Prediction, Future, Anomaly scatter) + “Recent Alerts” table.
  - `css/style.css`: dark Grafana-style theme.

---

## Data Shapes

**Series response**
```json
{
  "sensor_id": "ai_test",
  "ts": [1706056700, 1706056701, ...],
  "vals": [53.2, 53.4, ...],
  "preds": [53.1, 53.3, ...],
  "future_ts": [1706056800, 1706056801, ...],
  "future_preds": [52.9, 52.8, ...],
  "anomalies_idx": [101, 137]
}
```

**Alerts response**
```json
{
  "sensor_id": "ai_test",
  "items": [
    {"t": 1706056793, "v": 65.33, "z": 5.28, "msg": "Anomaly z=5.28 at t=1706056793"}
  ]
}
```

---

## Request/Response Map

| Route | Method | Source → Dest | Notes |
|---|---|---|---|
| `/health` | GET | App → API → UI | Liveness + uptime |
| `/predictive/series` | GET | Buffers → Predictive → UI | Windowed series + predictions |
| `/predictive/ingest` | POST | UI/External → Buffers | Optional manual/sample ingest |
| `/alerts` | GET | Alerts Repo → UI | Most recent anomaly events |

---

## Runtime Sequence (happy path)

1. **Startup**: `main.py` checks `ENABLE_SIMULATOR` → `start_simulator(...)`.
2. **Simulator loop**: computes `v` and `t`, appends to buffer.
3. **UI polling**: `index.html` calls `/predictive/series` every ~1.5s.
4. **Predictive service**: reads window, computes EWMA & residuals, flags anomalies, returns JSON.
5. **UI render**: Chart.js updates Actual/Prediction/Future; anomalies plotted as red dots.
6. **Alerts widget**: polls `/alerts` every ~5s to list recent anomaly events.

---

## Extension Points

- **Real sensors**: replace `workers/simulator` with MQTT/Modbus/HTTP collector writing to `repositories.buffers`.
- **Modeling**: swap EWMA for ARIMA, Prophet, Kalman, or an LSTM head; maintain same response shape.
- **Persistence**: lift buffers to SQLite/PostgreSQL/TimescaleDB; keep repo interface stable.
- **Transport**: switch UI polling → WebSockets (`/ws/series`) for push updates.

---

## Config Flags (current)

- `ENABLE_SIMULATOR = True`
- `SIM_SENSOR_ID = "ai_test"`
- `SIM_PERIOD_SEC = 1.0`

> Future: move to `.env` and parse with `pydantic-settings`.

---

## Non-Goals (for now)

- Multi-tenant auth/roles  
- Long-term historical storage/retention  
- Complex alert rules engine  
