from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Map common status codes to stable error codes if not provided
    status_code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
        status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    }
    code = status_code_map.get(exc.status_code, "ERROR")
    message = str(exc.detail) if exc.detail else "An error occurred."
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": {},
            }
        },
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    details = {}
    for err in errors:
        loc = ".".join(str(l) for l in err.get("loc", []))
        details[loc] = err.get("msg", "Validation failed")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_FAILURE",
                "message": "Input validation failed. Please check the provided fields.",
                "details": details,
            }
        },
    )

async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Ensure no internal details or secrets are exposed
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "details": {},
            }
        },
    )
