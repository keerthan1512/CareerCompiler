"""
Jobs router — poll async job status.
Returns current status of a parse/matching/compilation job.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.parse_job import ParseJob
from ..models.master_resume import MasterResume
from ..models.user import User
from ..routers.auth import get_current_user

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get(
    "/{job_id}",
    summary="Poll the status of an async job",
    description=(
        "Returns the current status of a parse, match, compile, or evaluation job. "
        "Clients should poll this endpoint after receiving a 202 response from any async operation."
    ),
)
async def get_job_status(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    # Look up ParseJob
    stmt = (
        select(ParseJob)
        .join(MasterResume, ParseJob.master_resume_id == MasterResume.id)
        .where(
            ParseJob.id == job_id,
            MasterResume.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    return {
        "job_id": str(job.id),
        "type": "parse_resume",
        "status": job.status,
        "master_resume_id": str(job.master_resume_id),
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error_message": job.error_message,
    }
