from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Iterator, Optional

from apps.sidecar.core.settings import DB_PATH, DATA_DIR

__all__ = ["get_conn", "init_db"]

_CONN: Optional[sqlite3.Connection] = None


def get_conn() -> sqlite3.Connection:
    """
    Return a process-local sqlite3 connection configured for
    WAL and row access by column name.
    """
    global _CONN
    if _CONN is not None:
        return _CONN

    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, detect_types=0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # pragmatic defaults for app workload
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    _CONN = conn
    return _CONN


def init_db() -> None:
    """
    Idempotent DB initializer. Safe to call multiple times.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS samples(
            sensor_id TEXT NOT NULL,
            t        REAL NOT NULL,
            v        REAL NOT NULL,
            PRIMARY KEY(sensor_id, t)
        );
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_samples_sensor_t ON samples(sensor_id, t);"
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts(
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            t         REAL NOT NULL,
            v         REAL NOT NULL,
            z         REAL NOT NULL,
            msg       TEXT NOT NULL
        );
        """
    )
    conn.commit()


# Initialize on import so we don't have to touch app startup wiring.
init_db()
