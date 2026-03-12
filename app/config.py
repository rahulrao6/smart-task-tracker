from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Smart Task Tracker"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "sqlite:///./tasks.db"
    secret_key: str = "changeme-in-production"
    allowed_origins: str = "*"

    model_config = {"env_file": ".env"}


settings = Settings()
