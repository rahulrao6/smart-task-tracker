"""Tests for rate limiting."""
import pytest
from datetime import datetime, timedelta

from src.app.rate_limit import RateLimiter, RateLimitExceeded, rate_limit


class TestRateLimiter:
    """Test token bucket rate limiter."""

    def test_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests=10, period_seconds=60)
        assert limiter.requests == 10
        assert limiter.period == timedelta(seconds=60)

    def test_limiter_allows_requests(self):
        """Test that limiter allows requests within limit."""
        limiter = RateLimiter(requests=5, period_seconds=60)
        
        for i in range(5):
            assert limiter.is_allowed("test_key") is True

    def test_limiter_blocks_excess_requests(self):
        """Test that limiter blocks requests exceeding limit."""
        limiter = RateLimiter(requests=2, period_seconds=60)
        
        assert limiter.is_allowed("test_key") is True
        assert limiter.is_allowed("test_key") is True
        assert limiter.is_allowed("test_key") is False

    def test_limiter_different_keys(self):
        """Test that limits are per-key."""
        limiter = RateLimiter(requests=2, period_seconds=60)
        
        # Key 1
        assert limiter.is_allowed("key1") is True
        assert limiter.is_allowed("key1") is True
        assert limiter.is_allowed("key1") is False
        
        # Key 2 should have separate limit
        assert limiter.is_allowed("key2") is True
        assert limiter.is_allowed("key2") is True
        assert limiter.is_allowed("key2") is False

    def test_get_reset_after(self):
        """Test getting reset time."""
        limiter = RateLimiter(requests=1, period_seconds=60)
        
        # Use up the limit
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")
        
        # Get reset time
        reset_after = limiter.get_reset_after("test_key")
        assert 0 <= reset_after <= 60

    def test_rate_limit_exception(self):
        """Test rate limit exception."""
        exc = RateLimitExceeded(retry_after=30)
        assert exc.status_code == 429
        assert "Rate limit exceeded" in str(exc.detail)
        assert "Retry-After" in exc.headers


class TestRateLimitDecorator:
    """Test rate limit decorator."""

    @pytest.mark.asyncio
    async def test_decorator_blocks_excess_calls(self):
        """Test that decorator blocks excess function calls."""
        @rate_limit(requests=2, period_seconds=60)
        async def limited_func(current_user: str = None):
            return "success"

        # First two calls should succeed
        result1 = await limited_func()
        result2 = await limited_func()
        assert result1 == "success"
        assert result2 == "success"
        
        # Third call should raise exception
        with pytest.raises(RateLimitExceeded):
            await limited_func()

    @pytest.mark.asyncio
    async def test_decorator_per_user_limits(self):
        """Test that decorator enforces per-user limits."""
        @rate_limit(requests=1, period_seconds=60)
        async def limited_func(current_user: str = None):
            return f"success-{current_user}"

        # User 1
        result1 = await limited_func(current_user="user1")
        assert result1 == "success-user1"
        
        # User 1 exceeds limit
        with pytest.raises(RateLimitExceeded):
            await limited_func(current_user="user1")
        
        # User 2 should have separate limit
        result2 = await limited_func(current_user="user2")
        assert result2 == "success-user2"
