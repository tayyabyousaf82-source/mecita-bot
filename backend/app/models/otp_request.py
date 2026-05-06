"""OTPRequest model."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.session import Base


class OTPStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    EXPIRED = "expired"


class OTPRequest(Base):
    __tablename__ = "otp_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("monitoring_jobs.id", ondelete="CASCADE"), index=True)

    status: Mapped[OTPStatus] = mapped_column(SAEnum(OTPStatus), default=OTPStatus.PENDING, index=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    context_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    otp_value: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Admin-provided OTP
    resolved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="otp_requests")
    job: Mapped["MonitoringJob"] = relationship("MonitoringJob", back_populates="otp_requests")


class LogLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("monitoring_jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    level: Mapped[LogLevel] = mapped_column(SAEnum(LogLevel), default=LogLevel.INFO, index=True)
    source: Mapped[str] = mapped_column(String(100))  # 'playwright', 'bot', 'system', 'worker'
    message: Mapped[str] = mapped_column(Text)
    extra: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    job: Mapped[Optional["MonitoringJob"]] = relationship("MonitoringJob", back_populates="logs")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    job_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("monitoring_jobs.id", ondelete="SET NULL"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50))  # 'telegram', 'websocket', 'firebase'
    event_type: Mapped[str] = mapped_column(String(100))  # 'appointment_found', 'otp_required', etc.
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
