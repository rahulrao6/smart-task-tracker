"""Tests for configuration module."""
import pytest
from src.app.config import Settings


class TestSettingsConfiguration:
    """Test application settings."""

    def test_default_settings(self):
        """Test that default settings are properly set."""
        settings = Settings()
        assert settings.APP_NAME == "Smart Task Tracker"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.DEBUG is False

    def test_database_url_default(self):
        """Test default database URL."""
        settings = Settings()
        assert "sqlite" in settings.DATABASE_URL

    def test_security_settings(self):
        """Test security-related settings."""
        settings = Settings()
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0
        assert settings.ALGORITHM == "HS256"

    def test_rate_limiting_settings(self):
        """Test rate limiting configuration."""
        settings = Settings()
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.RATE_LIMIT_REQUESTS > 0
        assert settings.RATE_LIMIT_PERIOD_SECONDS > 0

    def test_cors_settings(self):
        """Test CORS configuration."""
        settings = Settings()
        # CORS can be "*" or comma-separated origins
        assert settings.ALLOWED_ORIGINS is not None

    def test_logging_settings(self):
        """Test logging configuration."""
        settings = Settings()
        assert settings.LOG_DIR is not None
        assert settings.LOG_FORMAT in ["text", "json"]
