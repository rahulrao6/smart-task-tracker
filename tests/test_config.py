"""Tests for configuration validation module."""

import pytest

from app.config import ConfigurationError, Settings, get_settings


class TestSettingsInitialization:
    """Test Settings initialization with default values."""

    def test_default_settings(self, monkeypatch):
        """Test that Settings initializes with default values."""
        monkeypatch.delenv("APP_NAME", raising=False)
        monkeypatch.delenv("APP_VERSION", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
        monkeypatch.delenv("LOG_DIR", raising=False)
        monkeypatch.delenv("LOG_FORMAT", raising=False)

        # Clear the singleton instance
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()

        assert settings.app_name == "Smart Task Tracker"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.database_url == "sqlite+aiosqlite:///./smart_task_tracker.db"
        assert settings.secret_key == "changeme-in-production"
        assert settings.allowed_origins == ["*"]
        assert settings.log_dir == "./logs"
        assert settings.log_format == "text"

    def test_custom_settings_from_env(self, monkeypatch):
        """Test that Settings reads custom values from environment."""
        monkeypatch.setenv("APP_NAME", "Custom Tracker")
        monkeypatch.setenv("APP_VERSION", "2.5.3")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        monkeypatch.setenv("SECRET_KEY", "very-secret-key-12345")
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com,https://app.example.com")
        monkeypatch.setenv("LOG_DIR", "/var/log/app")
        monkeypatch.setenv("LOG_FORMAT", "json")

        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()

        assert settings.app_name == "Custom Tracker"
        assert settings.app_version == "2.5.3"
        assert settings.debug is True
        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost/db"
        assert settings.secret_key == "very-secret-key-12345"
        assert settings.allowed_origins == [
            "https://example.com",
            "https://app.example.com",
        ]
        assert settings.log_dir == "/var/log/app"
        assert settings.log_format == "json"


class TestAppNameValidation:
    """Test APP_NAME validation."""

    def test_valid_app_name(self, monkeypatch):
        """Test that valid app names are accepted."""
        monkeypatch.setenv("APP_NAME", "My Task Tracker")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.app_name == "My Task Tracker"

    def test_empty_app_name(self, monkeypatch):
        """Test that empty app name raises ConfigurationError."""
        monkeypatch.setenv("APP_NAME", "")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(ConfigurationError, match="APP_NAME must be a non-empty string"):
            Settings()

    def test_app_name_too_long(self, monkeypatch):
        """Test that app name exceeding 255 characters raises ConfigurationError."""
        long_name = "A" * 256
        monkeypatch.setenv("APP_NAME", long_name)
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(
            ConfigurationError, match="APP_NAME must be 255 characters or less"
        ):
            Settings()


class TestAppVersionValidation:
    """Test APP_VERSION validation."""

    def test_valid_versions(self, monkeypatch):
        """Test that valid semantic versions are accepted."""
        valid_versions = ["1.0.0", "2.5.3", "0.1.0", "10.20.30"]
        for version in valid_versions:
            monkeypatch.setenv("APP_VERSION", version)
            if hasattr(get_settings, "_instance"):
                delattr(get_settings, "_instance")

            settings = Settings()
            assert settings.app_version == version

    def test_invalid_version_format(self, monkeypatch):
        """Test that invalid version formats raise ConfigurationError."""
        invalid_versions = ["1.0", "1.0.0.0", "1.a.0", "not-a-version"]
        for version in invalid_versions:
            monkeypatch.setenv("APP_VERSION", version)
            if hasattr(get_settings, "_instance"):
                delattr(get_settings, "_instance")

            with pytest.raises(ConfigurationError, match="APP_VERSION"):
                Settings()

    def test_empty_version(self, monkeypatch):
        """Test that empty version raises ConfigurationError."""
        monkeypatch.setenv("APP_VERSION", "")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(ConfigurationError, match="APP_VERSION must be a non-empty string"):
            Settings()


class TestDatabaseURLValidation:
    """Test DATABASE_URL validation."""

    def test_valid_sqlite_url(self, monkeypatch):
        """Test that valid SQLite URLs are accepted."""
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.database_url == "sqlite+aiosqlite:///./test.db"

    def test_valid_postgresql_url(self, monkeypatch):
        """Test that valid PostgreSQL URLs are accepted."""
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost/db"

    def test_valid_mysql_url(self, monkeypatch):
        """Test that valid MySQL URLs are accepted."""
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://user:pass@localhost/db")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.database_url == "mysql+aiomysql://user:pass@localhost/db"

    def test_invalid_database_driver(self, monkeypatch):
        """Test that unsupported database drivers raise ConfigurationError."""
        monkeypatch.setenv("DATABASE_URL", "mysql://localhost/db")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(
            ConfigurationError, match="DATABASE_URL must use a supported async driver"
        ):
            Settings()

    def test_empty_database_url(self, monkeypatch):
        """Test that empty DATABASE_URL raises ConfigurationError."""
        monkeypatch.setenv("DATABASE_URL", "")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(ConfigurationError, match="DATABASE_URL must be a non-empty string"):
            Settings()


class TestSecretKeyValidation:
    """Test SECRET_KEY validation."""

    def test_valid_secret_key_debug_mode(self, monkeypatch):
        """Test that default secret key is allowed in debug mode."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "changeme-in-production")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.secret_key == "changeme-in-production"

    def test_custom_secret_key_production(self, monkeypatch):
        """Test that custom secret key is required in production."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "my-very-secret-key-12345")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.secret_key == "my-very-secret-key-12345"

    def test_default_secret_key_production_raises_error(self, monkeypatch):
        """Test that default secret key in production raises ConfigurationError."""
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("SECRET_KEY", "changeme-in-production")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(
            ConfigurationError,
            match="SECRET_KEY must be changed from default in production mode",
        ):
            Settings()

    def test_secret_key_too_short(self, monkeypatch):
        """Test that secret key less than 8 characters raises ConfigurationError."""
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("SECRET_KEY", "short")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(
            ConfigurationError, match="SECRET_KEY must be at least 8 characters"
        ):
            Settings()

    def test_empty_secret_key(self, monkeypatch):
        """Test that empty SECRET_KEY raises ConfigurationError."""
        monkeypatch.setenv("SECRET_KEY", "")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(ConfigurationError, match="SECRET_KEY must be a non-empty string"):
            Settings()


class TestAllowedOriginsValidation:
    """Test ALLOWED_ORIGINS validation."""

    def test_wildcard_origins(self, monkeypatch):
        """Test that wildcard origins are accepted."""
        monkeypatch.setenv("ALLOWED_ORIGINS", "*")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.allowed_origins == ["*"]

    def test_comma_separated_origins(self, monkeypatch):
        """Test that comma-separated origins are parsed correctly."""
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com,https://app.example.com")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.allowed_origins == [
            "https://example.com",
            "https://app.example.com",
        ]

    def test_origins_with_whitespace(self, monkeypatch):
        """Test that origins with whitespace are stripped correctly."""
        monkeypatch.setenv("ALLOWED_ORIGINS", " https://example.com , https://app.example.com ")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        assert settings.allowed_origins == [
            "https://example.com",
            "https://app.example.com",
        ]

    def test_empty_origins(self, monkeypatch):
        """Test that empty origins raise ConfigurationError."""
        monkeypatch.setenv("ALLOWED_ORIGINS", "")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(ConfigurationError, match="ALLOWED_ORIGINS must not be empty"):
            Settings()


class TestLogFormatValidation:
    """Test LOG_FORMAT validation."""

    def test_valid_log_formats(self, monkeypatch):
        """Test that valid log formats are accepted."""
        for fmt in ["text", "json", "TEXT", "JSON"]:
            monkeypatch.setenv("LOG_FORMAT", fmt)
            if hasattr(get_settings, "_instance"):
                delattr(get_settings, "_instance")

            settings = Settings()
            assert settings.log_format == fmt.lower()

    def test_invalid_log_format(self, monkeypatch):
        """Test that invalid log format raises ConfigurationError."""
        monkeypatch.setenv("LOG_FORMAT", "invalid-format")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        with pytest.raises(ConfigurationError, match="LOG_FORMAT must be one of"):
            Settings()


class TestSettingsToDict:
    """Test Settings.to_dict() method."""

    def test_to_dict_hides_secret_key(self, monkeypatch):
        """Test that to_dict() hides the secret key."""
        monkeypatch.setenv("SECRET_KEY", "my-secret-key")
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        config_dict = settings.to_dict()

        assert config_dict["secret_key"] == "***"
        assert "my-secret-key" not in str(config_dict)

    def test_to_dict_contains_all_settings(self, monkeypatch):
        """Test that to_dict() contains all settings."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings = Settings()
        config_dict = settings.to_dict()

        assert "app_name" in config_dict
        assert "app_version" in config_dict
        assert "debug" in config_dict
        assert "database_url" in config_dict
        assert "secret_key" in config_dict
        assert "allowed_origins" in config_dict
        assert "log_dir" in config_dict
        assert "log_format" in config_dict


class TestGetSettingsSingleton:
    """Test get_settings() singleton behavior."""

    def test_get_settings_returns_same_instance(self, monkeypatch):
        """Test that get_settings() returns the same instance on multiple calls."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_raises_runtime_error_on_validation_failure(self, monkeypatch):
        """Test that get_settings() raises RuntimeError on configuration error."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        monkeypatch.setenv("APP_NAME", "")

        with pytest.raises(RuntimeError, match="Configuration validation failed"):
            get_settings()

    def test_get_settings_creates_instance_once(self, monkeypatch):
        """Test that get_settings() creates instance only once."""
        if hasattr(get_settings, "_instance"):
            delattr(get_settings, "_instance")

        settings1 = get_settings()
        monkeypatch.setenv("APP_NAME", "Changed Name")
        settings2 = get_settings()

        assert settings1.app_name == settings2.app_name
