"""Bot middlewares."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime, timezone

import os

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            data["db"] = session
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        from sqlalchemy import select
        # Import here to avoid circular
        from bot.db_models import User

        telegram_user = data.get("event_from_user")
        if not telegram_user:
            return await handler(event, data)

        db: AsyncSession = data["db"]
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_user.id)
        )
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
            return  # Silently ignore banned users

        return await handler(event, data)
