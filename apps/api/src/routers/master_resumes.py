"""
Master Resumes router
Handles upload and retrieval of master resumes (JSON).

Endpoints:
  POST   /api/v1/master-resumes           Upload .pdf resume
  GET    /api/v1/master-resumes           List user's master resumes
  GET    /api/v1/master-resumes/{id}      Get resume + canonical profile
"""

from __future__ import annotations

import logging
import uuid
import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import get_settings
from ..database import get_db
from ..models.audit_log import AuditLog
from ..models.canonical_profile import CanonicalProfile
from ..models.master_resume import MasterResume
from ..models.user import User
from ..routers.auth import get_current_user
from ..schemas.master_resume import (
    MasterResumeDetailResponse,
    MasterResumeUploadResponse,
)
from ..services.file_storage import get_file_storage
from ..celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/master-resumes", tags=["Master Resumes"])


# ── POST /master-resumes ───────────────────────────────────────────────────────


@router.post(
    "",
    response_model=MasterResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a master resume PDF",
    description=(
        "Upload a master .pdf resume file. It will be parsed asynchronously."
    ),
)
async def upload_master_resume(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    pdf_file: UploadFile = File(..., description="Resume .pdf file"),
    display_name: str = Form(default="Master Resume", description="Display name for this resume"),
):
    resume_id = uuid.uuid4()
    storage = get_file_storage()
    user_id_str = str(current_user.id)

    if not (pdf_file.filename or "").endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primary file must be a .pdf file",
        )

    content = await pdf_file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
        )

    # Save primary .pdf file
    pdf_filename = pdf_file.filename or "main.pdf"
    pdf_path, checksum = await storage.save_pdf(
        user_id_str, str(resume_id), content, filename=pdf_filename
    )

    # Create MasterResume record
    master_resume = MasterResume(
        id=resume_id,
        user_id=current_user.id,
        checksum=checksum,
        template_metadata={},
        display_name=display_name,
    )
    db.add(master_resume)

    # Create CanonicalProfile record (pending)
    profile = CanonicalProfile(
        master_resume_id=resume_id,
        status="pending",
        profile_json={}
    )
    db.add(profile)

    await db.flush()

    # Trigger Celery Task
    job = celery_app.send_task(
        "src.tasks.parse_resume",
        args=[str(resume_id), user_id_str, pdf_filename]
    )

    # Audit log
    db.add(
        AuditLog(
            actor_type="user",
            actor_id=str(current_user.id),
            action="upload_master_resume",
            entity_type="master_resume",
            entity_id=str(resume_id),
            diff={"filename": pdf_filename, "size_bytes": len(content)},
        )
    )
    await db.flush()

    return MasterResumeUploadResponse(
        id=master_resume.id,
        display_name=master_resume.display_name,
        status=profile.status,
        profile_id=profile.id,
        job_id=None,
        created_at=master_resume.created_at,
    )


# ── GET /master-resumes ────────────────────────────────────────────────────────


@router.get(
    "",
    summary="List all master resumes for the current user",
)
async def list_master_resumes(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MasterResume)
        .where(MasterResume.user_id == current_user.id)
        .options(selectinload(MasterResume.canonical_profile))
        .order_by(MasterResume.created_at.desc())
    )
    result = await db.execute(stmt)
    resumes = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "display_name": r.display_name,
            "checksum": r.checksum,
            "created_at": r.created_at.isoformat(),
            "profile_status": r.canonical_profile.status if r.canonical_profile else "none",
        }
        for r in resumes
    ]


# ── GET /master-resumes/{id} ───────────────────────────────────────────────────


@router.get(
    "/{resume_id}",
    response_model=MasterResumeDetailResponse,
    summary="Get a master resume with its canonical profile",
)
async def get_master_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MasterResume)
        .where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
        .options(selectinload(MasterResume.canonical_profile))
    )
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Master resume {resume_id} not found",
        )

    profile = resume.canonical_profile
    profile_response = None

    if profile:
        profile_data = profile.profile_json or {}
        profile_response = {
            "id": str(profile.id),
            "master_resume_id": str(profile.master_resume_id),
            "status": profile.status,
            "parser_version": profile.parser_version,
            "contact": profile_data.get("contact"),
            "sections": profile_data.get("sections"),
            "skills": profile_data.get("skills"),
            "template": profile_data.get("template"),
            "metadata": profile_data.get("metadata"),
            "error_message": profile.error_message,
            "updated_at": profile.updated_at.isoformat(),
        }

    return {
        "id": str(resume.id),
        "display_name": resume.display_name,
        "checksum": resume.checksum,
        "template_metadata": resume.template_metadata,
        "created_at": resume.created_at.isoformat(),
        "canonical_profile": profile_response,
    }



