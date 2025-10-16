# AI Sidecar Panel — System Diagram

> High-level flow of data and responsibilities. Keep this document updated as modules evolve.

---

## Topology (Mermaid)

```mermaid
flowchart LR
  %% LAYOUT
  %% LR = left-to-right
  %% Use <br/> for line breaks in labels (GitHub Mermaid)

  subgraph Sensor_Layer[Sensor Layer]
    S1["Simulated Sensor<br/>apps/sidecar/workers/simulator.py"]
  end

  subgraph Buffer_Repo_Layer[Buffer / Repo Layer]
    B["In-mem Buffers + Simple Store<br/>apps/sidecar/repositories/"]
  end

  subgraph Services[Services]
    P["Predictive Service<br/>EWMA + z-score<br/>apps/sidecar/services/predictive_service.py"]
    A["Alerts Repo / Service<br/>apps/sidecar/repositories/alerts_repo.py"]
  end

  subgraph API_Routers[API (FastAPI Routers)]
    R1[/health/]
    R2[/predictive/series]
    R3[/predictive/ingest]
    R4[/alerts]
  end

  subgraph UI_Static[UI (Static)]
    UI["index.html + css<br/>Chart.js + fetch()"]
  end

  %% Wiring
  S1 -->|push samples| B
  B  -->|read window| P
  P  -->|preds + anomalies| A
  P  -->|JSON| R2
  B  -->|JSON| R3
  A  -->|JSON| R4
  R1 --- UI
  R2 --- UI
  R3 --- UI
  R4 --- UI
```

---

## Module Responsibilities

- **workers/simulator.py**  
  Generates baseline + noise with rare spikes; writes to buffer.  
  Config: `SIM_SENSOR_ID`, `SIM_PERIOD_SEC`, `ENABLE_SIMULATOR`.

- **repositories/**  
  `buffers.py` (ring buffer + window queries), `alerts_repo.py` (append/list anomalies).

- **services/predictive_service.py**  
  EWMA baseline, one-step prediction, short future projection; flags anomalies (z-score).  
  Returns `{ ts, vals, preds, future_ts, future_preds, anomalies_idx }`.

- **api/**  
  `health.py` (uptime), `predictive.py` (`GET /predictive/series`, `POST /predictive/ingest`), `alerts.py` (`GET /alerts`).

- **static/**  
  `index.html` (Chart.js lines + anomalies) and `css/style.css` (dark theme).

---

## Data Shapes

**Series response**
```json
{
  "sensor_id": "ai_test",
  "ts": [1706056700, 1706056701],
  "vals": [53.2, 53.4],
  "preds": [53.1, 53.3],
  "future_ts": [1706056800, 1706056801],
  "future_preds": [52.9, 52.8],
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

## Request / Response Map

| Route | Method | Source → Dest | Notes |
|---|---|---|---|
| `/health` | GET | App → API → UI | Liveness + uptime |
| `/predictive/series` | GET | Buffers → Predictive → UI | Windowed series + predictions |
| `/predictive/ingest` | POST | UI/External → Buffers | Optional manual/sample ingest |
| `/alerts` | GET | Alerts Repo → UI | Most recent anomaly events |

---

## Runtime Sequence (happy path)

1. **Startup**: `main.py` checks `ENABLE_SIMULATOR` → `start_simulator(...)`.  
2. **Simulator loop** writes `(t, v)` into buffer.  
3. **UI** polls `/predictive/series` (~1.5s).  
4. **Predictive service** computes EWMA, residuals, anomalies; returns JSON.  
5. **UI** renders Actual/Prediction/Future; anomalies as red dots.  
6. **Alerts widget** polls `/alerts` (~5s).

---

## Extension Points

- Real sensors (MQTT/Modbus/HTTP collectors → `repositories.buffers`).  
- Modeling (ARIMA/Prophet/Kalman/LSTM) with same response shape.  
- Persistence (SQLite/Postgres/TimescaleDB) behind repo interface.  
- Transport (WebSockets `/ws/series`).

---

## Config Flags

- `ENABLE_SIMULATOR = True`  
- `SIM_SENSOR_ID = "ai_test"`  
- `SIM_PERIOD_SEC = 1.0`

> Future: move to `.env` with `pydantic-settings`.
