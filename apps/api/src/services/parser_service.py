"""
Parser Service
Orchestrates the full parsing pipeline:
  LaTeXParser → CanonicalProfileBuilder → EvidenceExtractor → DB save

Called synchronously in Phase 1.
In Phase 3+, this is dispatched as a Celery task.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from latex_ast_parser.parser import LaTeXParser
from canonical_profile_builder.builder import CanonicalProfileBuilder
from evidence_extractor.extractor import EvidenceExtractor

from ..models.canonical_profile import CanonicalProfile
from ..models.parse_job import ParseJob

logger = logging.getLogger(__name__)

_latex_parser = LaTeXParser()
_profile_builder = CanonicalProfileBuilder()
_evidence_extractor = EvidenceExtractor()


async def run_parse_pipeline(
    session: AsyncSession,
    resume_id: str,
    user_id: str,
    tex_content: bytes,
    filename: str,
    job: ParseJob,
) -> CanonicalProfile:
    """
    Run the full parse pipeline for a master resume.

    Steps:
        1. Parse LaTeX → RawAST
        2. Build CanonicalProfile JSON
        3. Extract Evidence list
        4. Save CanonicalProfile to DB
        5. Update ParseJob status

    Args:
        session: Active async DB session
        resume_id: UUID of the MasterResume
        user_id: UUID of the User
        tex_content: Raw bytes of the .tex file
        filename: Filename for source refs
        job: ParseJob record to update

    Returns:
        CanonicalProfile ORM record (status=complete)
    """
    # Mark job as running
    job.status = "running"
    await session.flush()

    try:
        tex_str = tex_content.decode("utf-8", errors="replace")

        logger.info("Parsing resume %s (%d chars)", resume_id, len(tex_str))

        # Step 1: LaTeX → RawAST
        raw_ast = _latex_parser.parse(tex_str, filename=filename)

        # Step 2: RawAST → CanonicalProfile JSON
        profile_json = _profile_builder.build(raw_ast, resume_id=str(resume_id))

        # Step 3: Extract evidence list
        evidence_list = _evidence_extractor.extract(profile_json)

        logger.info(
            "Resume %s parsed: %d sections, %d bullets, %d skills, %d evidence items",
            resume_id,
            profile_json["metadata"]["total_sections"],
            profile_json["metadata"]["total_bullets"],
            profile_json["metadata"]["total_skills"],
            len(evidence_list),
        )

        # Step 4: Save or update CanonicalProfile
        profile_record = await _get_or_create_profile(session, resume_id)
        profile_record.profile_json = profile_json
        profile_record.evidence_json = evidence_list
        profile_record.status = "complete"
        profile_record.error_message = None
        await session.flush()

        # Step 5: Mark job complete
        job.status = "complete"
        job.completed_at = datetime.now(timezone.utc)
        await session.flush()

        return profile_record

    except Exception as exc:
        logger.error("Parse pipeline failed for resume %s: %s", resume_id, exc)

        # Update profile record with failure
        profile_record = await _get_or_create_profile(session, resume_id)
        profile_record.status = "failed"
        profile_record.error_message = str(exc)
        await session.flush()

        # Mark job as failed
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        await session.flush()

        raise


async def _get_or_create_profile(
    session: AsyncSession, resume_id: str
) -> CanonicalProfile:
    """Get existing CanonicalProfile or create a new one."""
    from sqlalchemy import select

    stmt = select(CanonicalProfile).where(
        CanonicalProfile.master_resume_id == resume_id
    )
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if profile is None:
        profile = CanonicalProfile(master_resume_id=resume_id)
        session.add(profile)
        await session.flush()

    return profile
