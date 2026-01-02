from fastapi import Request, HTTPException, status, Depends
import time
from threading import Lock

# Simple in-memory sliding-window rate limiter.
# Not suitable for multi-process production, but useful for lightweight protection.

_store = {}
_lock = Lock()

def _now():
    return int(time.time())

def limit_leads(max_requests: int = 5, window_seconds: int = 60):
    async def _limit(request: Request):
        # use client host as key (best-effort)
        client = request.client.host if request.client else 'unknown'
        key = f"leads:{client}"
        now = _now()
        with _lock:
            entry = _store.get(key)
            if not entry:
                _store[key] = [now]
                return True
            # drop old timestamps
            window_start = now - window_seconds
            entry = [t for t in entry if t >= window_start]
            if len(entry) >= max_requests:
                # Too many
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
            entry.append(now)
            _store[key] = entry
        return True
    return _limit
