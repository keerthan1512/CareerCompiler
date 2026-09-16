"""MasterResume ORM model"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .canonical_profile import CanonicalProfile
    from .parse_job import ParseJob


class MasterResume(Base):
    __tablename__ = "master_resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Path to the primary .tex file in local storage (./uploads/{user_id}/{resume_id}/main.tex)
    original_tex_path: Mapped[str] = mapped_column(String(500), nullable=False)
    # List of asset paths (images, .cls, .sty, .bib) as JSON array
    assets_paths: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    # SHA-256 checksum of the primary .tex content
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    # Extracted metadata: {document_class, packages, detected_format}
    template_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # Display name / title for the resume
    display_name: Mapped[str] = mapped_column(String(255), default="Master Resume", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="master_resumes")
    canonical_profile: Mapped["CanonicalProfile | None"] = relationship(
        "CanonicalProfile",
        back_populates="master_resume",
        uselist=False,
        cascade="all, delete-orphan",
    )
    parse_jobs: Mapped[list["ParseJob"]] = relationship(
        "ParseJob", back_populates="master_resume", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MasterResume id={self.id} user_id={self.user_id}>"
