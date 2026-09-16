import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.job_description import JobDescription
from ..models.user import User
from ..routers.auth import get_current_user
from ..schemas.job_description import JobDescriptionCreate, JobDescriptionResponse
from ..celery_app import task_analyze_job

router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])

@router.post(
    "",
    response_model=JobDescriptionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and analyze a Job Description",
)
async def analyze_job_description(
    payload: JobDescriptionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    # Create the job in the DB
    job_desc = JobDescription(
        user_id=current_user.id,
        display_name=payload.display_name,
        source_url=str(payload.source_url) if payload.source_url else None,
        raw_text=payload.raw_text,
        status="pending",
    )
    db.add(job_desc)
    await db.commit()
    await db.refresh(job_desc)
    
    # Send to Celery worker
    task_analyze_job.delay(job_id=str(job_desc.id), user_id=str(current_user.id))
    
    return job_desc

@router.get(
    "",
    response_model=List[JobDescriptionResponse],
    summary="List all Job Descriptions",
)
async def list_job_descriptions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    stmt = select(JobDescription).where(JobDescription.user_id == current_user.id).order_by(JobDescription.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get(
    "/{job_id}",
    response_model=JobDescriptionResponse,
    summary="Get a Job Description",
)
async def get_job_description(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    stmt = select(JobDescription).where(
        JobDescription.id == job_id,
        JobDescription.user_id == current_user.id
    )
    result = await db.execute(stmt)
    job_desc = result.scalar_one_or_none()
    
    if not job_desc:
        raise HTTPException(status_code=404, detail="Job Description not found")
        
    return job_desc
