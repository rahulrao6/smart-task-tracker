"""Configuration validation module for Smart Task Tracker."""

import os
from typing import Optional


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""

    pass


class Settings:
    """Application configuration settings with validation."""

    def __init__(self) -> None:
        """Initialize and validate application settings from environment variables."""
        self.app_name = os.getenv("APP_NAME", "Smart Task Tracker")
        self.app_version = os.getenv("APP_VERSION", "0.1.0")
        self.debug = self._parse_bool(os.getenv("DEBUG", "false"))
        self.database_url = os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./smart_task_tracker.db"
        )
        self.secret_key = os.getenv("SECRET_KEY", "changeme-in-production")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.allowed_origins = self._parse_origins(
            os.getenv("ALLOWED_ORIGINS", "*")
        )
        self.log_dir = os.getenv("LOG_DIR", "./logs")
        self.log_format = os.getenv("LOG_FORMAT", "text").lower()
        self.rate_limit_enabled = self._parse_bool(os.getenv("RATE_LIMIT_ENABLED", "true"))
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_period_seconds = int(os.getenv("RATE_LIMIT_PERIOD_SECONDS", "60"))

        self._validate()

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse a string boolean value."""
        return value.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def _parse_origins(origins_str: str) -> list[str]:
        """Parse comma-separated origins string into list."""
        if origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    def _validate(self) -> None:
        """Validate all configuration settings."""
        self._validate_app_name()
        self._validate_app_version()
        self._validate_database_url()
        self._validate_secret_key()
        self._validate_allowed_origins()
        self._validate_log_format()
        self._validate_rate_limiting()

    def _validate_app_name(self) -> None:
        """Validate app name is not empty."""
        if not self.app_name or not isinstance(self.app_name, str):
            raise ConfigurationError(
                f"APP_NAME must be a non-empty string, got: {self.app_name!r}"
            )
        if len(self.app_name) > 255:
            raise ConfigurationError(
                f"APP_NAME must be 255 characters or less, got: {len(self.app_name)}"
            )

    def _validate_app_version(self) -> None:
        """Validate app version format (semantic versioning)."""
        if not self.app_version or not isinstance(self.app_version, str):
            raise ConfigurationError(
                f"APP_VERSION must be a non-empty string, got: {self.app_version!r}"
            )
        parts = self.app_version.split(".")
        if len(parts) != 3:
            raise ConfigurationError(
                f"APP_VERSION must follow semantic versioning (major.minor.patch), "
                f"got: {self.app_version}"
            )
        for part in parts:
            if not part.isdigit():
                raise ConfigurationError(
                    f"APP_VERSION parts must be numeric, got: {self.app_version}"
                )

    def _validate_database_url(self) -> None:
        """Validate database URL is properly formatted."""
        if not self.database_url or not isinstance(self.database_url, str):
            raise ConfigurationError(
                f"DATABASE_URL must be a non-empty string, got: {self.database_url!r}"
            )
        if not (
            self.database_url.startswith("sqlite+aiosqlite://")
            or self.database_url.startswith("postgresql+asyncpg://")
            or self.database_url.startswith("mysql+aiomysql://")
        ):
            raise ConfigurationError(
                f"DATABASE_URL must use a supported async driver "
                f"(sqlite+aiosqlite, postgresql+asyncpg, mysql+aiomysql), "
                f"got: {self.database_url}"
            )

    def _validate_secret_key(self) -> None:
        """Validate secret key is set and not default in production."""
        if not self.secret_key or not isinstance(self.secret_key, str):
            raise ConfigurationError(
                f"SECRET_KEY must be a non-empty string, got: {self.secret_key!r}"
            )
        if len(self.secret_key) < 8:
            raise ConfigurationError(
                f"SECRET_KEY must be at least 8 characters, got: {len(self.secret_key)}"
            )
        if self.secret_key == "changeme-in-production" and os.getenv("DEBUG", "").lower() == "false":  # nosec B105
            raise ConfigurationError(
                "SECRET_KEY must be changed from default in production mode "
                "(DEBUG=false)"
            )

    def _validate_allowed_origins(self) -> None:
        """Validate allowed origins list is not empty."""
        if not self.allowed_origins:
            raise ConfigurationError("ALLOWED_ORIGINS must not be empty")
        if not all(isinstance(origin, str) for origin in self.allowed_origins):
            raise ConfigurationError("All ALLOWED_ORIGINS must be strings")

    def _validate_log_format(self) -> None:
        """Validate log format is supported."""
        valid_formats = ("text", "json")
        if self.log_format not in valid_formats:
            raise ConfigurationError(
                f"LOG_FORMAT must be one of {valid_formats}, got: {self.log_format}"
            )

    def _validate_rate_limiting(self) -> None:
        """Validate rate limiting configuration."""
        if self.rate_limit_requests <= 0:
            raise ConfigurationError(
                f"RATE_LIMIT_REQUESTS must be positive, got: {self.rate_limit_requests}"
            )
        if self.rate_limit_period_seconds <= 0:
            raise ConfigurationError(
                f"RATE_LIMIT_PERIOD_SECONDS must be positive, got: {self.rate_limit_period_seconds}"
            )

    def to_dict(self) -> dict:
        """Return configuration as dictionary."""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "debug": self.debug,
            "database_url": self.database_url,
            "secret_key": "***" if self.secret_key else None,
            "allowed_origins": self.allowed_origins,
            "log_dir": self.log_dir,
            "log_format": self.log_format,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_period_seconds": self.rate_limit_period_seconds,
        }


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    if not hasattr(get_settings, "_instance"):
        try:
            get_settings._instance = Settings()
        except ConfigurationError as e:
            raise RuntimeError(f"Configuration validation failed: {e}") from e
    return get_settings._instance
