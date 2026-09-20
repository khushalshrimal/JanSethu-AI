from typing import Optional, Dict, Any

class AppException(Exception):
    def __init__(
        self, 
        message: str, 
        code: str = "INTERNAL_SERVER_ERROR", 
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=400, details=details)

class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid credentials or token expired"):
        super().__init__(message=message, code="AUTHENTICATION_ERROR", status_code=401)

class AuthorizationError(AppException):
    def __init__(self, message: str = "Insufficient permissions to perform this action"):
        super().__init__(message=message, code="AUTHORIZATION_ERROR", status_code=403)

class NotFoundError(AppException):
    def __init__(self, message: str = "Requested resource not found"):
        super().__init__(message=message, code="NOT_FOUND", status_code=404)

class ConflictError(AppException):
    def __init__(self, message: str = "Resource state conflict"):
        super().__init__(message=message, code="RESOURCE_CONFLICT", status_code=409)

class RateLimitError(AppException):
    def __init__(self, message: str = "Too many requests. Please try again later."):
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED", status_code=429)
