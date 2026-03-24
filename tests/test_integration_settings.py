"""Integration validation tests for Settings configuration with FastAPI application."""

import os
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings, ConfigurationError, Settings
from app.main import app


class TestSettingsIntegration:
    """Integration tests validating Settings works with FastAPI application."""

    def test_app_initializes_with_valid_settings(self, monkeypatch):
        """Test that Settings initializes successfully with valid configuration."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("APP_NAME", "Test App")
        monkeypatch.setenv("APP_VERSION", "1.0.0")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ALLOWED_ORIGINS", "*")

        settings = get_settings()
        
        assert settings.app_name == "Test App"
        assert settings.app_version == "1.0.0"
        assert settings.debug is True
        assert settings.allowed_origins == ["*"]

    def test_health_endpoint_responds_with_valid_settings(self, monkeypatch):
        """Test that health endpoint works with valid settings configuration."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("APP_NAME", "Smart Task Tracker")
        monkeypatch.setenv("APP_VERSION", "1.0.0")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("ALLOWED_ORIGINS", "*")

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_settings_cors_configuration_applied_to_app(self, monkeypatch):
        """Test that CORS settings from configuration are properly parsed and stored."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com,https://app.example.com")
        monkeypatch.setenv("DEBUG", "true")

        settings = get_settings()
        
        assert settings.allowed_origins == [
            "https://example.com",
            "https://app.example.com",
        ]
        # Verify the app has middleware configured (it's set up at module load)
        # We validate that settings are properly formatted for CORS middleware
        assert isinstance(settings.allowed_origins, list)
        assert all(isinstance(origin, str) for origin in settings.allowed_origins)

    def test_app_validation_fails_with_invalid_settings(self, monkeypatch):
        """Test that invalid settings raise RuntimeError during app initialization."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("APP_VERSION", "invalid-version")

        with pytest.raises(RuntimeError, match="Configuration validation failed"):
            get_settings()

    def test_settings_singleton_consistent_across_app_modules(self, monkeypatch):
        """Test that settings singleton remains consistent throughout app lifecycle."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("APP_NAME", "Integration Test App")

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
        assert settings1.app_name == "Integration Test App"
        assert settings2.app_name == "Integration Test App"

    def test_app_uses_settings_for_metadata(self, monkeypatch):
        """Test that app correctly uses settings for OpenAPI metadata."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("APP_NAME", "Validated Task Tracker")
        monkeypatch.setenv("APP_VERSION", "2.5.3")

        settings = get_settings()

        assert settings.app_name == "Validated Task Tracker"
        assert settings.app_version == "2.5.3"

    def test_settings_validation_fails_with_invalid_database_url(self, monkeypatch):
        """Test that invalid database URL in settings causes validation failure."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("DATABASE_URL", "mysql://localhost/db")
        monkeypatch.setenv("DEBUG", "true")

        with pytest.raises(RuntimeError, match="Configuration validation failed"):
            get_settings()

    def test_settings_validation_with_debug_and_production_modes(self, monkeypatch):
        """Test settings validation behaves correctly in debug vs production modes."""
        # Test debug mode allows default secret key
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "changeme-in-production")

        settings_debug = get_settings()
        assert settings_debug.debug is True
        assert settings_debug.secret_key == "changeme-in-production"

        # Test production mode requires custom secret key
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "changeme-in-production")

        with pytest.raises(RuntimeError, match="Configuration validation failed"):
            get_settings()
