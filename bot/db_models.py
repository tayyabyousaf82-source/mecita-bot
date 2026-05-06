"""
Lightweight SQLAlchemy models for the bot service.
Mirrors the backend models without the full backend dependencies.
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, Text, Date, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(200))
    last_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    profiles: Mapped[List["Profile"]] = relationship("Profile", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200), default="Mi cita")
    province_code: Mapped[str] = mapped_column(String(10))
    province_name: Mapped[str] = mapped_column(String(200))
    tramite_code: Mapped[str] = mapped_column(String(50))
    tramite_name: Mapped[str] = mapped_column(String(500))
    oficina_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oficina_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    date_from: Mapped[datetime] = mapped_column(Date)
    date_to: Mapped[datetime] = mapped_column(Date)
    phones: Mapped[List] = mapped_column(JSON, default=list)
    emails: Mapped[List] = mapped_column(JSON, default=list)
    certificates: Mapped[List] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="profiles")
