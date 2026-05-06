"""
CitaMonitor Telegram Bot — Railway-compatible entry point
"""
import asyncio
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

REDIS_URL = os.environ.get("REDIS_URL", "")
if REDIS_URL:
    from aiogram.fsm.storage.redis import RedisStorage
    storage = RedisStorage.from_url(REDIS_URL)
    logger.info("Using Redis storage")
else:
    from aiogram.fsm.storage.memory import MemoryStorage
    storage = MemoryStorage()
    logger.info("Using Memory storage")

from handlers import common, nueva_cita, profile, admin
from middlewares.database import DatabaseMiddleware, UserMiddleware


async def main():
    BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=storage)

    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(UserMiddleware())

    dp.include_router(common.router)
    dp.include_router(nueva_cita.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)

    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
