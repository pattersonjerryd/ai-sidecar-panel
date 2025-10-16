from __future__ import annotations

from typing import List, Optional
from apps.sidecar.repositories.storage.sqlite import get_conn

class AlertRepo:
    """SQLite-based repository for anomaly alerts."""
    
    def add_alert(self, sensor_id: str, t: float, v: float, z: float, msg: str) -> int:
        """
        Add a new alert to the database.
        Returns the ID of the inserted alert.
        """
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO alerts (sensor_id, t, v, z, msg) VALUES (?, ?, ?, ?, ?)",
            (sensor_id, t, v, z, msg)
        )
        conn.commit()
        return cur.lastrowid
    
    def get_alerts(
        self,
        sensor_id: str,
        start_ts: Optional[float] = None,
        end_ts: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[dict]:
        """
        Get alerts for a sensor.
        Returns list of alert dictionaries with keys: id, sensor_id, t, v, z, msg
        """
        conn = get_conn()
        cur = conn.cursor()
        
        query = "SELECT id, sensor_id, t, v, z, msg FROM alerts WHERE sensor_id = ?"
        params = [sensor_id]
        
        if start_ts is not None:
            query += " AND t >= ?"
            params.append(start_ts)
        
        if end_ts is not None:
            query += " AND t <= ?"
            params.append(end_ts)
        
        query += " ORDER BY t DESC"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        return [
            {
                "id": row[0],
                "sensor_id": row[1],
                "t": row[2],
                "v": row[3],
                "z": row[4],
                "msg": row[5]
            }
            for row in rows
        ]
    
    def get_recent_alerts(self, sensor_id: str, limit: int = 10) -> List[dict]:
        """Get the most recent alerts for a sensor."""
        return self.get_alerts(sensor_id, limit=limit)
