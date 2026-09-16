"""
Master Resumes router
Handles upload, retrieval, and re-parsing of master LaTeX resumes.

Endpoints:
  POST   /api/v1/master-resumes           Upload .tex + assets
  GET    /api/v1/master-resumes           List user's master resumes
  GET    /api/v1/master-resumes/{id}      Get resume + canonical profile
  POST   /api/v1/master-resumes/{id}/reparse  Re-run parser
"""

from __future__ import annotations

import logging
import uuid
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
from ..models.parse_job import ParseJob
from ..models.user import User
from ..routers.auth import get_current_user
from ..schemas.master_resume import (
    MasterResumeDetailResponse,
    MasterResumeUploadResponse,
    ReparseResponse,
)
from ..services.file_storage import get_file_storage
from ..services.parser_service import run_parse_pipeline

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/master-resumes", tags=["Master Resumes"])


# ── POST /master-resumes ───────────────────────────────────────────────────────


@router.post(
    "",
    response_model=MasterResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a master LaTeX resume",
    description=(
        "Upload a master .tex file along with optional assets (.cls, .sty, .bib, images). "
        "The file is stored immutably and parsed immediately (Phase 1 synchronous). "
        "Returns the resume ID and initial parsing status."
    ),
)
async def upload_master_resume(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    tex_file: UploadFile = File(..., description="Primary .tex file"),
    display_name: str = Form(default="Master Resume", description="Display name for this resume"),
    assets: list[UploadFile] = File(default=[], description="Asset files (.cls, .sty, .bib, images)"),
):
    storage = get_file_storage()
    resume_id = uuid.uuid4()
    user_id_str = str(current_user.id)

    # Validate file type
    if not (tex_file.filename or "").endswith(".tex"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Primary file must be a .tex file",
        )

    # Validate file size
    tex_content = await tex_file.read()
    if len(tex_content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
        )

    if len(tex_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded .tex file is empty",
        )

    # Save primary .tex file
    tex_filename = tex_file.filename or "main.tex"
    tex_path, checksum = await storage.save_tex(
        user_id_str, str(resume_id), tex_content, filename=tex_filename
    )

    # Save asset files
    asset_paths: list[str] = []
    for asset in assets:
        if asset.filename and asset.size and asset.size > 0:
            asset_content = await asset.read()
            asset_path = await storage.save_asset(
                user_id_str, str(resume_id), asset_content, asset.filename
            )
            asset_paths.append(asset_path)

    # Create MasterResume record
    master_resume = MasterResume(
        id=resume_id,
        user_id=current_user.id,
        original_tex_path=tex_path,
        assets_paths=asset_paths,
        checksum=checksum,
        template_metadata={},
        display_name=display_name,
    )
    db.add(master_resume)

    # Create ParseJob record
    parse_job = ParseJob(master_resume_id=resume_id)
    db.add(parse_job)

    # Create pending CanonicalProfile placeholder
    profile = CanonicalProfile(master_resume_id=resume_id, status="pending")
    db.add(profile)

    await db.flush()

    # ── Phase 1: Run parser synchronously ──────────────────────────────────
    # Phase 3+: dispatch to Celery task instead
    try:
        profile = await run_parse_pipeline(
            session=db,
            resume_id=str(resume_id),
            user_id=user_id_str,
            tex_content=tex_content,
            filename=tex_filename,
            job=parse_job,
        )
        # Update template metadata from parsed result
        if profile.profile_json:
            master_resume.template_metadata = profile.profile_json.get("template", {})
        await db.flush()
    except Exception as exc:
        logger.error("Parse failed for resume %s: %s", resume_id, exc)
        # Don't fail the upload — profile.status=failed, user can reparse

    # Audit log
    db.add(
        AuditLog(
            actor_type="user",
            actor_id=str(current_user.id),
            action="upload_master_resume",
            entity_type="master_resume",
            entity_id=str(resume_id),
            diff={"filename": tex_filename, "size_bytes": len(tex_content)},
        )
    )
    await db.flush()

    return MasterResumeUploadResponse(
        id=master_resume.id,
        display_name=master_resume.display_name,
        status=profile.status,
        profile_id=profile.id,
        job_id=parse_job.id,
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
        "assets_paths": resume.assets_paths,
        "created_at": resume.created_at.isoformat(),
        "canonical_profile": profile_response,
    }


# ── POST /master-resumes/{id}/reparse ─────────────────────────────────────────


@router.post(
    "/{resume_id}/reparse",
    response_model=ReparseResponse,
    summary="Re-run the parser on an existing master resume",
    description="Useful when the parser is updated or after fixing an asset issue.",
)
async def reparse_master_resume(
    resume_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    # Fetch resume
    stmt = select(MasterResume).where(
        MasterResume.id == resume_id,
        MasterResume.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()

    if resume is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Master resume {resume_id} not found",
        )

    storage = get_file_storage()
    tex_content = await storage.read_tex(
        str(current_user.id), str(resume_id)
    )

    # New parse job
    parse_job = ParseJob(master_resume_id=resume_id)
    db.add(parse_job)
    await db.flush()

    # Run parser
    try:
        profile = await run_parse_pipeline(
            session=db,
            resume_id=str(resume_id),
            user_id=str(current_user.id),
            tex_content=tex_content,
            filename="main.tex",
            job=parse_job,
        )
        status_msg = profile.status
    except Exception as exc:
        status_msg = "failed"

    # Audit
    db.add(
        AuditLog(
            actor_type="user",
            actor_id=str(current_user.id),
            action="reparse_master_resume",
            entity_type="master_resume",
            entity_id=str(resume_id),
        )
    )
    await db.flush()

    return ReparseResponse(
        resume_id=resume_id,
        job_id=parse_job.id,
        status=status_msg,
        message=f"Re-parse completed with status: {status_msg}",
    )
