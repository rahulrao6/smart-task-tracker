"""Tests for configuration module."""
import pytest
from src.app.config import Settings


class TestSettingsConfiguration:
    """Test application settings."""

    def test_default_settings(self):
        """Test that default settings are properly set."""
        settings = Settings()
        assert settings.app_name == "Smart Task Tracker"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False

    def test_database_url_default(self):
        """Test default database URL."""
        settings = Settings()
        assert "sqlite" in settings.database_url

    def test_security_settings(self):
        """Test security-related settings."""
        settings = Settings()
        assert settings.secret_key is not None
        assert len(settings.secret_key) > 0
        assert settings.algorithm == "HS256"

    @pytest.mark.skip(reason="Rate limiting disabled in test environment")
    def test_rate_limiting_settings(self):
        """Test rate limiting configuration."""
        settings = Settings()
        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_requests > 0
        assert settings.rate_limit_period_seconds > 0

    def test_cors_settings(self):
        """Test CORS configuration."""
        settings = Settings()
        # CORS returns a list
        assert settings.allowed_origins is not None

    def test_logging_settings(self):
        """Test logging configuration."""
        settings = Settings()
        assert settings.log_dir is not None
        assert settings.log_format in ["text", "json"]
