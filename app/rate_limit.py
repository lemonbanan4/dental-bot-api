from fastapi import Request, HTTPException, status
from typing import Optional
import time
from threading import Lock
from app.config import settings

_store = {}
_lock = Lock()

def _now():
    return int(time.time() * 1000)

async def _redis_limit(request: Request, max_requests: int, window_seconds: int):
    """Use Redis sorted set per client to implement sliding window rate limit."""
    try:
        r = request.app.state.redis
    except Exception:
        r = None

    client = request.client.host if request.client else 'unknown'
    key = f"leads:{client}"
    now = _now()
    window_ms = window_seconds * 1000

    if r:
        # Use ZADD/ZREMRANGEBYSCORE/ZCARD atomically via pipeline
        try:
            # remove old
            await r.zremrangebyscore(key, 0, now - window_ms)
            await r.zadd(key, {str(now): now})
            count = await r.zcard(key)
            await r.expire(key, window_seconds + 5)
            if count > max_requests:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
            return True
        except HTTPException:
            raise
        except Exception:
            # fallthrough to in-memory fallback
            pass

    # Fallback in-memory limiter (per-process)
    with _lock:
        entry = _store.get(key, [])
        # drop old
        cutoff = now - window_ms
        entry = [t for t in entry if t >= cutoff]
        if len(entry) >= max_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        entry.append(now)
        _store[key] = entry
    return True

def limit_leads(max_requests: int = 5, window_seconds: int = 60):
    async def _limit(request: Request):
        # If REDIS_URL configured and app.state.redis is set, _redis_limit will use it.
        return await _redis_limit(request, max_requests, window_seconds)
    return _limit
