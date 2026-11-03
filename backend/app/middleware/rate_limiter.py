"""
Rate Limiting Middleware for KarigarConnect.

Uses slowapi for per-IP and per-user throttling on sensitive endpoints.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi import FastAPI, Request


def _get_identifier(request: Request) -> str:
    """Combine IP + user ID (from JWT) for user-aware rate-limiting."""
    # Try to extract user_id from state if auth middleware set it
    user_id = getattr(request.state, "user_id", None)
    ip = get_remote_address(request)
    return f"{ip}:{user_id}" if user_id else ip


# Limiter instance shared across the application
limiter = Limiter(key_func=_get_identifier, default_limits=["60/minute"])


def register_rate_limiter(app: FastAPI) -> None:
    """Attach slowapi rate limiter to the FastAPI application."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
