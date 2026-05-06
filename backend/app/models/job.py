"""MonitoringJob model."""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.session import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    SEARCHING = "searching"
    FOUND = "found"
    STOPPED = "stopped"
    ERROR = "error"
    PAUSED = "paused"


class MonitoringJob(Base):
    __tablename__ = "monitoring_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), index=True)

    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.QUEUED, index=True)
    worker_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Runtime data
    check_count: Mapped[int] = mapped_column(Integer, default=0)
    last_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    found_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="jobs")
    profile: Mapped["Profile"] = relationship("Profile", back_populates="jobs")
    otp_requests: Mapped[List["OTPRequest"]] = relationship("OTPRequest", back_populates="job")
    logs: Mapped[List["Log"]] = relationship("Log", back_populates="job")
