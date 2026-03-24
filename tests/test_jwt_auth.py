"""Tests for JWT authentication module."""
import pytest
from datetime import timedelta
from jose import jwt

from src.app.jwt_auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from src.app.config import get_settings


class TestJWTTokenGeneration:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_create_access_token_with_custom_expiry(self):
        """Test creating access token with custom expiration."""
        data = {"sub": "testuser"}
        expires = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires)
        assert token is not None

    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        data = {"sub": "testuser"}
        token = create_refresh_token(data)
        assert token is not None
        assert isinstance(token, str)

    def test_token_contains_username(self):
        """Test that token contains the username."""
        settings = get_settings()
        username = "testuser"
        data = {"sub": username}
        token = create_access_token(data)
        
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )
        assert payload["sub"] == username

    def test_refresh_token_has_type(self):
        """Test that refresh token has type field."""
        settings = get_settings()
        data = {"sub": "testuser"}
        token = create_refresh_token(data)
        
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )
        assert payload["type"] == "refresh"

    def test_token_expiration(self):
        """Test that token has expiration time."""
        settings = get_settings()
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
        )
        assert "exp" in payload
