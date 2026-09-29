from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SERVICE_NAME: str = "jocky-backend"
    VERSION: str = "0.1.0"
    
    # Network
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-prod"
    ALLOWED_ORIGINS: str = "*"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./jocky_dev.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Agent Security
    AGENT_REGISTRATION_TOKEN: str = "jocky-agent-insecure-dev-token"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
