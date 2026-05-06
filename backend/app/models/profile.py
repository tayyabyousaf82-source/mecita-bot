"""Monitoring profile model."""
from datetime import datetime, timezone, date
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, Text, Date, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))

    # Location filters
    province_code: Mapped[str] = mapped_column(String(10))
    province_name: Mapped[str] = mapped_column(String(200))
    tramite_code: Mapped[str] = mapped_column(String(50))
    tramite_name: Mapped[str] = mapped_column(String(500))
    oficina_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oficina_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Date range
    date_from: Mapped[date] = mapped_column(Date)
    date_to: Mapped[date] = mapped_column(Date)

    # Contact info (encrypted at application level)
    phones: Mapped[List] = mapped_column(JSON, default=list)       # encrypted list
    emails: Mapped[List] = mapped_column(JSON, default=list)       # encrypted list
    certificates: Mapped[List] = mapped_column(JSON, default=list) # metadata only

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profiles")
    jobs: Mapped[List["MonitoringJob"]] = relationship("MonitoringJob", back_populates="profile")
