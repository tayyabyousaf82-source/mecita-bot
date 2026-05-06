"""Bot configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    TELEGRAM_BOT_TOKEN: str
    ADMIN_TELEGRAM_ID: int
    DATABASE_URL: str
    REDIS_URL: str
    BACKEND_URL: str = "http://backend:8000"


settings = BotSettings()
