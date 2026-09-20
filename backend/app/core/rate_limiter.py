import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request
from app.core.config import settings
from app.core.exceptions import RateLimitError

class RateLimiter:
    """
    In-memory sliding window rate limiter.
    Does not require external Redis, keeping local development zero-dependency.
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)
        
    def check_rate_limit(self, key: str, limit: int = None) -> bool:
        max_requests = limit or self.requests_per_minute
        now = time.time()
        window_start = now - 60.0
        
        # Clean timestamps older than 1 minute
        timestamps = [ts for ts in self.requests[key] if ts > window_start]
        self.requests[key] = timestamps
        
        if len(timestamps) >= max_requests:
            return False
            
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

def rate_limit_middleware(request: Request, max_requests: int = None):
    # Obtain client IP
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    key = f"{client_ip}:{path}"
    
    # Apply rate limiting to sensitive routes (login, register, telephony webhooks, voice)
    sensitive_prefixes = [
        f"{settings.API_V1_STR}/auth/login",
        f"{settings.API_V1_STR}/auth/register",
        f"{settings.API_V1_STR}/telephony/webhooks",
        f"{settings.API_V1_STR}/phone"
    ]
    
    if any(path.startswith(prefix) for prefix in sensitive_prefixes):
        allowed = rate_limiter.check_rate_limit(key, limit=max_requests or settings.RATE_LIMIT_PER_MINUTE)
        if not allowed:
            raise RateLimitError("Rate limit exceeded for this endpoint. Please wait a minute before retrying.")
