"""CanonicalProfile ORM model"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .master_resume import MasterResume


class CanonicalProfile(Base):
    __tablename__ = "canonical_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    master_resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("master_resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # Full canonical profile JSON (matches canonical_profile.schema.json)
    profile_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Flat evidence list JSON (from EvidenceExtractor)
    evidence_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    parser_version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)
    # pending | running | complete | failed
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    master_resume: Mapped["MasterResume"] = relationship(
        "MasterResume", back_populates="canonical_profile"
    )

    def __repr__(self) -> str:
        return f"<CanonicalProfile id={self.id} status={self.status}>"
