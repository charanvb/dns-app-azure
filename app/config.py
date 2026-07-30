"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Immutable application settings sourced exclusively from environment variables."""

    app_name: str = "Azure DNS Self Service Portal"
    app_version: str = "1.0.0"
    environment: str = "development"
    port: int = 8000
    dns_subscription_id: str = ""
    dns_resource_group: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
