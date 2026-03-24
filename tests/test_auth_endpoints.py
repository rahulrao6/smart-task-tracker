"""Integration tests for authentication endpoints."""
import pytest
from httpx import AsyncClient

from src.app.auth import _DEFAULT_USER_STORE, _DEFAULT_TOKEN_STORE


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication REST endpoints."""

    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "securepass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_user(self, client: AsyncClient):
        """Test registering duplicate username fails."""
        # Create first user
        await client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "securepass123"},
        )
        # Try to create duplicate
        response = await client.post(
            "/api/auth/register",
            json={"username": "testuser", "password": "otherpass123"},
        )
        assert response.status_code == 400

    async def test_register_weak_password(self, client: AsyncClient):
        """Test that weak passwords are rejected."""
        response = await client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "weak"},
        )
        assert response.status_code == 400

    async def test_login_valid_credentials(self, client: AsyncClient):
        """Test login with valid credentials."""
        # Register user
        await client.post(
            "/api/auth/register",
            json={"username": "loginuser", "password": "securepass123"},
        )
        # Login
        response = await client.post(
            "/api/auth/login",
            json={"username": "loginuser", "password": "securepass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "wrongpass"},
        )
        assert response.status_code == 401

    @pytest.mark.skip(reason="Rate limiting disabled in test environment")
    async def test_login_rate_limiting(self, client: AsyncClient):
        """Test that login endpoint has rate limiting."""
        # Make multiple failed login attempts
        for i in range(6):
            response = await client.post(
                "/api/auth/login",
                json={"username": "user", "password": "wrong"},
            )
            if i < 5:
                assert response.status_code in [401, 400]
            else:
                # 6th request should be rate limited
                assert response.status_code == 429

    async def test_refresh_token(self, client: AsyncClient):
        """Test token refresh."""
        # Register and get tokens
        reg_response = await client.post(
            "/api/auth/register",
            json={"username": "refreshuser", "password": "securepass123"},
        )
        refresh_token = reg_response.json()["refresh_token"]

        # Use refresh token
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient):
        """Test getting current user info."""
        # Register user
        reg_response = await client.post(
            "/api/auth/register",
            json={"username": "currentuser", "password": "securepass123"},
        )
        access_token = reg_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["is_active"] is True

    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test getting current user without authentication fails."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 403

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
