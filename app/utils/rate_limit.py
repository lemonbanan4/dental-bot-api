from fastapi import Request, HTTPException, status
import time
from collections import defaultdict

# Simple in-memory rate limiting for the chat endpoint
# In production, this should ideally share logic with app/rate_limit.py or use Redis
_request_counts = defaultdict(list)

def limit(request: Request, max_per_minute: int = 60):
    """
    Rate limit checker called inside route handlers.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean up old requests
    _request_counts[client_ip] = [t for t in _request_counts[client_ip] if t > now - 60]
    
    if len(_request_counts[client_ip]) >= max_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    _request_counts[client_ip].append(now)