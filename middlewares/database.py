"""Bot middlewares — Database session + User auto-creation."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from datetime import datetime, timezone
import os, logging

logger = logging.getLogger(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL", "")
engine = None
AsyncSessionLocal = None

if DATABASE_URL:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5)
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("Database connected")
else:
    logger.warning("DATABASE_URL not set — running without database")


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if AsyncSessionLocal:
            async with AsyncSessionLocal() as session:
                data["db"] = session
                return await handler(event, data)
        else:
            data["db"] = None
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        telegram_user = data.get("event_from_user")
        db = data.get("db")

        if not telegram_user:
            return await handler(event, data)

        if db is None:
            class MockUser:
                id = telegram_user.id
                telegram_id = telegram_user.id
                first_name = telegram_user.first_name or ""
                username = telegram_user.username
                is_banned = False
                is_active = True
            data["user"] = MockUser()
            return await handler(event, data)

        from sqlalchemy import select
        from db_models import User

        result = await db.execute(select(User).where(User.telegram_id == telegram_user.id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name or "",
                last_name=telegram_user.last_name,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user.last_seen = datetime.now(timezone.utc)
            if telegram_user.username:
                user.username = telegram_user.username
            await db.commit()

        data["user"] = user
        if user.is_banned:
            return
        return await handler(event, data)
