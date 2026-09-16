"""AuditLog ORM model — immutable record of every action"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # user | agent
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # user_id or agent name
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g. "upload_master_resume", "parse_resume", "approve_change"
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Optional diff / payload
    diff: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} entity={self.entity_type}:{self.entity_id}>"
