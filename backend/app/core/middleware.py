import uuid
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger

class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Attaches unique X-Request-ID to incoming HTTP requests and responses for end-to-end tracing.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id
        
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = str(process_time_ms)
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects production-grade security headers into every HTTP response.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Enforce HSTS if served over HTTPS in production
        if settings.APP_ENV == "production" and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
        return response
