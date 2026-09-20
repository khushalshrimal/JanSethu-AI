import uuid
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.middleware import RequestCorrelationMiddleware, SecurityHeadersMiddleware
from app.core.rate_limiter import rate_limit_middleware
from app.core.logging import logger
from app.api.v1.api import api_router
from app.database.session import engine
from app.database.base import Base

# Initialize Database tables if not existing
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Custom Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestCorrelationMiddleware)

# Rate Limiting Middleware
@app.middleware("http")
async def rate_limiting_http_middleware(request: Request, call_next):
    try:
        rate_limit_middleware(request)
    except AppException as exc:
        req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": req_id
                }
            }
        )
    return await call_next(request)

# Configurable CORS Middleware
allowed_origins = settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if settings.APP_ENV == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Global Exception Handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    logger.warning(f"Domain exception: {exc.code} - {exc.message}", extra={"request_id": req_id})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id
            }
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra={"request_id": req_id})
    
    # Safe user-facing message in production, detailed message in debug mode
    message = str(exc) if settings.DEBUG else "An unexpected error occurred. Please contact system support."
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": message,
                "request_id": req_id
            }
        }
    )

# Mount API V1 router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level health fallback
@app.get("/health", tags=["Health Check"])
@app.get("/", tags=["Root"])
def root_health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs" if settings.DEBUG else "disabled",
        "api_v1_health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

