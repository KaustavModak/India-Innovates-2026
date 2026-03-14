"""
Security middleware: CORS, rate limiting, request logging.
"""

from fastapi import Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_settings
from app.redis_client import cache_service
import time
import logging

settings = get_settings()
logger = logging.getLogger("election_audit")


def setup_cors(app):
    """Configure CORS middleware."""
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis counters."""

    async def dispatch(self, request: Request, call_next):
        # Exempt health checks
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"

        try:
            count = await cache_service.increment_counter(key, ttl=60)
            if count > settings.RATE_LIMIT_PER_MINUTE:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Try again in a minute.",
                )
        except HTTPException:
            raise
        except Exception:
            # If Redis is down, allow the request through
            pass

        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests with timing."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"status={response.status_code} "
            f"duration={duration:.3f}s "
            f"ip={request.client.host if request.client else 'unknown'}"
        )

        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response
