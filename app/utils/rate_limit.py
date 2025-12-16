import time
from fastapi import Request, HTTPException

# naive in-memory limiter: (ip -> [timestamps])

HITS: dict[str, list[float]] = {}

def limit(request: Request, max_per_minute: int = 60):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - 60

    ts = HITS.get(ip, [])
    ts = [t for t in ts if t >= window_start]
    if len(ts) >= max_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    ts.append(now)
    HITS[ip] = ts


    
    