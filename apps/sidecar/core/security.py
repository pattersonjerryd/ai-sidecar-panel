from __future__ import annotations

from fastapi import Header, HTTPException, status
from apps.sidecar.core.settings import API_TOKEN

async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Very small header-based token check.
    Send header: X-API-Key: <token>
    """
    if API_TOKEN is None or API_TOKEN == "":
        # If someone disabled tokens entirely, allow (dev only).
        return
    if x_api_key != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
        )
