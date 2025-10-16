from __future__ import annotations

from typing import List, Tuple, Optional
from apps.sidecar.repositories.storage.sqlite import get_conn

class SampleRepo:
    """SQLite-based repository for sensor samples."""
    
    def add_sample(self, sensor_id: str, t: float, v: float) -> None:
        """Add a single sample to the database."""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO samples (sensor_id, t, v) VALUES (?, ?, ?)",
            (sensor_id, t, v)
        )
        conn.commit()
    
    def get_series(
        self, 
        sensor_id: str, 
        start_ts: Optional[float] = None, 
        end_ts: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Tuple[float, float]]:
        """
        Get time series data for a sensor.
        Returns list of (timestamp, value) tuples ordered by timestamp.
        """
        conn = get_conn()
        cur = conn.cursor()
        
        query = "SELECT t, v FROM samples WHERE sensor_id = ?"
        params = [sensor_id]
        
        if start_ts is not None:
            query += " AND t >= ?"
            params.append(start_ts)
        
        if end_ts is not None:
            query += " AND t <= ?"
            params.append(end_ts)
        
        query += " ORDER BY t"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        cur.execute(query, params)
        return [(row[0], row[1]) for row in cur.fetchall()]
    
    def get_latest(self, sensor_id: str) -> Optional[Tuple[float, float]]:
        """Get the most recent sample for a sensor."""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT t, v FROM samples WHERE sensor_id = ? ORDER BY t DESC LIMIT 1",
            (sensor_id,)
        )
        row = cur.fetchone()
        return (row[0], row[1]) if row else None
