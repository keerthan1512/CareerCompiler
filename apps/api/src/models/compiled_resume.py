from datetime import datetime
from typing import Optional
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from ..database import Base

class CompiledResume(Base):
    __tablename__ = "compiled_resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tailoring_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tailoring_plans.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    
    latex_content: Mapped[str] = mapped_column(String, nullable=False)
    pdf_file_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    status: Mapped[str] = mapped_column(String, default="pending")  # pending, running, complete, failed
    validation_results: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
