"""OTP management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.otp_request import OTPRequest, OTPStatus
from app.api.routes.auth import get_current_admin
from app.core.redis import publish_event

router = APIRouter()


class OTPOut(BaseModel):
    id: int
    user_id: int
    job_id: int
    status: OTPStatus
    screenshot_path: Optional[str]
    context_data: Optional[str]
    otp_value: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OTPResolveRequest(BaseModel):
    otp_value: str


@router.get("/", response_model=List[OTPOut])
async def list_otp_requests(
    status: Optional[OTPStatus] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_admin),
):
    query = select(OTPRequest).order_by(desc(OTPRequest.created_at)).offset(skip).limit(limit)
    if status:
        query = query.where(OTPRequest.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/pending/count")
async def pending_otp_count(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    res = await db.execute(
        select(func.count()).where(OTPRequest.status == OTPStatus.PENDING)
    )
    return {"count": res.scalar()}


@router.post("/{otp_id}/resolve")
async def resolve_otp(
    otp_id: int,
    body: OTPResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_admin),
):
    result = await db.execute(select(OTPRequest).where(OTPRequest.id == otp_id))
    otp = result.scalar_one_or_none()
    if not otp:
        raise HTTPException(status_code=404, detail="OTP request not found")
    if otp.status != OTPStatus.PENDING:
        raise HTTPException(status_code=400, detail="OTP already resolved or expired")

    otp.otp_value = body.otp_value
    otp.status = OTPStatus.RESOLVED
    otp.resolved_by = current_user
    otp.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    # Notify the worker to resume
    await publish_event(
        f"otp:{otp.job_id}",
        "otp_resolved",
        {"otp_id": otp_id, "job_id": otp.job_id, "otp_value": body.otp_value}
    )

    return {"otp_id": otp_id, "status": "resolved"}
