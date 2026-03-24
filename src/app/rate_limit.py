"""Rate limiting middleware and utilities."""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple, Callable
from functools import wraps

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Token bucket rate limiter for API endpoints."""

    def __init__(self, requests: int, period_seconds: int):
        """Initialize rate limiter.

        Args:
            requests: Number of requests allowed per period
            period_seconds: Time period in seconds
        """
        self.requests = requests
        self.period = timedelta(seconds=period_seconds)
        self.buckets: Dict[str, Tuple[int, datetime]] = defaultdict(
            lambda: (self.requests, datetime.utcnow())
        )

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key.

        Args:
            key: Identifier (e.g., IP address or user ID)

        Returns:
            True if request is allowed, False otherwise
        """
        now = datetime.utcnow()
        available, last_reset = self.buckets[key]

        # Reset bucket if period has passed
        if now - last_reset >= self.period:
            self.buckets[key] = (self.requests, now)
            return True

        # Decrement bucket
        if available > 0:
            self.buckets[key] = (available - 1, last_reset)
            return True

        return False

    def get_reset_after(self, key: str) -> int:
        """Get seconds until rate limit resets."""
        _, last_reset = self.buckets[key]
        now = datetime.utcnow()
        reset_at = last_reset + self.period
        seconds_left = (reset_at - now).total_seconds()
        return max(0, int(seconds_left))


class RateLimitExceeded(HTTPException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware for global rate limiting by IP."""

    def __init__(self, app, requests: int = 100, period_seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests, period_seconds)

    async def dispatch(self, request: Request, call_next: Callable):
        """Apply rate limiting to request."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        if not self.limiter.is_allowed(client_ip):
            retry_after = self.limiter.get_reset_after(client_ip)
            raise RateLimitExceeded(retry_after)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests)
        response.headers["X-RateLimit-Remaining"] = str(
            self.limiter.buckets[client_ip][0]
        )
        response.headers["X-RateLimit-Reset"] = str(
            self.limiter.get_reset_after(client_ip)
        )
        return response


def rate_limit(requests: int = 100, period_seconds: int = 60):
    """Decorator to rate limit a function.

    Args:
        requests: Number of requests allowed
        period_seconds: Time period in seconds
    """
    limiter = RateLimiter(requests, period_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use username from kwargs as key, or use "global" for unauthenticated
            key = kwargs.get("current_user", "global")
            if not limiter.is_allowed(key):
                retry_after = limiter.get_reset_after(key)
                raise RateLimitExceeded(retry_after)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
