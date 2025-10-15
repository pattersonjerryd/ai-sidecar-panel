<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-teal?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" />
  <img src="https://img.shields.io/badge/Status-Active-success.svg" />
</p>

<h1 align="center">AI Sidecar Panel</h1>

<p align="center">
  <strong>Predictive Monitoring Dashboard for Industrial & Data Center Systems</strong><br />
  <em>Engineered to detect anomalies, learn from data, and visualize performance in real time.</em>
</p>

---

# AI Sidecar Panel

**FastAPI-based predictive monitoring dashboard** for industrial and data center applications.  
Built with a modular architecture for real-time data ingestion, anomaly detection, and predictive visualization.

---

## 🚀 Features
- **FastAPI backend** for high-performance data APIs  
- **Chart.js front-end overlay** with real-time graph updates  
- **Anomaly detection engine** using EWMA and Z-score projections  
- **Live alerts dashboard** with timestamped events  
- Modular structure for future integration with MQTT, Modbus, or IoT sensors  

---

## 🧠 Tech Stack
- **Backend:** FastAPI, Python 3.11  
- **Frontend:** HTML, CSS, JavaScript, Chart.js  
- **Environment:** Uvicorn ASGI server  
- **Storage:** Local SQLite (extendable to PostgreSQL or InfluxDB)

---

## 🧩 Project Structure
```text
ai-sidecar-panel/
├── apps/
│   └── sidecar/
│       ├── api/              # FastAPI routers
│       ├── core/             # Core config, constants
│       ├── models/           # Data models and schemas
│       ├── predictive/       # Predictive algorithms
│       ├── repositories/     # Data access layer
│       ├── static/           # Frontend assets (index.html, CSS)
│       └── workers/          # Simulators and background tasks
├── data/                     # Local data or simulation output
├── compose.yml               # Optional Docker setup
├── requirements.txt          # Python dependencies
└── README.md
```

---

## ⚙️ Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/pattersonjerryd/ai-sidecar-panel.git
cd ai-sidecar-panel
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
uvicorn apps.sidecar.main:app --reload --port 8080
```

Then open:  
👉 **http://127.0.0.1:8080/static/index.html**

---

## 🧠 Roadmap
- [ ] Add WebSocket real-time updates  
- [ ] Integrate MQTT live sensor feeds  
- [ ] Build modular AI inference layer  
- [ ] Create Docker deployment  
- [ ] Add authentication and role control  

---

## 🧾 License
MIT License © 2025 Jerry Patterson
