"""
Centralized Error Handling Middleware for KarigarConnect.

Intercepts all exceptions and returns a uniform JSON error response:
  { "code": <http_status>, "detail": <message>, "timestamp": <iso8601> }
"""
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _error_response(code: int, detail: str) -> JSONResponse:
    """Build a uniform error response."""
    return JSONResponse(
        status_code=code,
        content={
            "code": code,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Collect field-level validation messages into a readable string
        errors = []
        for err in exc.errors():
            loc = " -> ".join(str(part) for part in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            errors.append(f"{loc}: {msg}")
        detail = "Validation failed: " + "; ".join(errors)
        return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the real error server-side
        print(f"[ERROR] Unhandled exception on {request.method} {request.url}: {type(exc).__name__}: {exc}")
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected internal error occurred. Please try again or contact support.",
        )
