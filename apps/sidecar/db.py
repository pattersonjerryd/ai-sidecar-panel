# apps/sidecar/db.py
from __future__ import annotations
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path("data/cortex.db")

async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS readings(
                ts TEXT NOT NULL,           -- ISO8601 UTC
                sensor_id TEXT NOT NULL,
                value REAL NOT NULL,
                baseline REAL NOT NULL,
                z REAL NOT NULL,
                slope REAL NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts(
                ts TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS rules(
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                condition TEXT NOT NULL,
                action TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_readings ON readings(sensor_id, ts)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts)")
        await conn.commit()

async def journal_mode() -> str:
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute("PRAGMA journal_mode;") as cur:
            (mode,) = await cur.fetchone()
            return mode

# ---- writes ----
async def add_reading(*, sensor_id: str, value: float, baseline: float, z: float, slope: float) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO readings (ts, sensor_id, value, baseline, z, slope) "
            "VALUES (datetime('now'), ?, ?, ?, ?, ?)",
            (sensor_id, float(value), float(baseline), float(z), float(slope)),
        )
        await conn.commit()

# ---- reads ----
async def fetch_history(sensor_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    async with aiosqlite.connect(DB_PATH) as conn:
        async with conn.execute(
            "SELECT ts, value, baseline, z, slope "
            "FROM readings WHERE sensor_id=? ORDER BY ts DESC LIMIT ?",
            (sensor_id, int(limit)),
        ) as cur:
            async for ts, value, baseline, z, slope in cur:
                rows.append({
                    "ts": ts,
                    "value": float(value),
                    "baseline": float(baseline),
                    "z": float(z),
                    "slope": float(slope),
                })
    rows.reverse()
    return rows
