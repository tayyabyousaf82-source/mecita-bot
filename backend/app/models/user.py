"""User model."""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Boolean, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(200))
    last_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    profiles: Mapped[List["Profile"]] = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    jobs: Mapped[List["MonitoringJob"]] = relationship("MonitoringJob", back_populates="user", cascade="all, delete-orphan")
    otp_requests: Mapped[List["OTPRequest"]] = relationship("OTPRequest", back_populates="user", cascade="all, delete-orphan")
