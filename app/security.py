from typing import Optional

from fastapi import Header, HTTPException, status

from app.config import settings


async def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key", convert_underscores=False),
):
    """
    Simple header-based API key check. Expects header: X-API-Key: <key>.
    """
    expected = settings.api_key
    if not expected:
        raise HTTPException(status_code=500, detail="API key not configured")
    if x_api_key == expected:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "API-Key"},
    )
