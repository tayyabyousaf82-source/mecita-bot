"""
CitaMonitor Telegram Bot
Main entry point
"""
import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.handlers import common, nueva_cita, profile, admin
from bot.middlewares import DatabaseMiddleware, UserMiddleware

logger = structlog.get_logger()


async def main():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
    )

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(UserMiddleware())

    # Routers
    dp.include_router(common.router)
    dp.include_router(nueva_cita.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)

    logger.info("Starting CitaMonitor bot")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
