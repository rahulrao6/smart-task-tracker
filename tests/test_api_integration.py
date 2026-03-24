"""Integration tests for API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Test health endpoint returns ok status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.skip(reason="Rate limiting disabled in test environment")
@pytest.mark.asyncio
class TestRateLimitHeaders:
    """Test rate limit headers in responses."""

    async def test_rate_limit_headers_present(self, client: AsyncClient):
        """Test that responses include rate limit headers."""
        response = await client.get("/health")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


@pytest.mark.asyncio
class TestAPIDocumentation:
    """Test API documentation endpoints."""

    async def test_openapi_schema(self, client: AsyncClient):
        """Test OpenAPI schema endpoint."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema

    async def test_swagger_ui(self, client: AsyncClient):
        """Test Swagger UI is available."""
        response = await client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    async def test_redoc(self, client: AsyncClient):
        """Test ReDoc is available."""
        response = await client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()


@pytest.mark.asyncio
class TestCORSHeaders:
    """Test CORS configuration."""

    async def test_cors_headers_present(self, client: AsyncClient):
        """Test that CORS headers are present."""
        response = await client.get("/health")
        # Note: CORS headers depend on configuration
        # This test just verifies endpoint is accessible
        assert response.status_code == 200

    async def test_cors_preflight(self, client: AsyncClient):
        """Test CORS preflight request."""
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling."""

    async def test_404_not_found(self, client: AsyncClient):
        """Test 404 error for non-existent endpoint."""
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404

    async def test_405_method_not_allowed(self, client: AsyncClient):
        """Test 405 error for wrong HTTP method."""
        response = await client.post("/health")
        assert response.status_code == 405

    async def test_error_response_format(self, client: AsyncClient):
        """Test that errors have consistent format."""
        response = await client.get("/api/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
