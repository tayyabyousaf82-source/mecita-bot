"""Bot configuration from environment variables."""
import os

class Settings:
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    ADMIN_TELEGRAM_ID: int = int(os.environ.get("ADMIN_TELEGRAM_ID", "0"))
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    REDIS_URL: str = os.environ.get("REDIS_URL", "")
    BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000")

settings = Settings()
