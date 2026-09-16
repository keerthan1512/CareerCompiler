import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from ..database import Base

class JobDescription(Base):
    """
    SQLAlchemy model for ingested Job Descriptions.
    """
    __tablename__ = "job_descriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    display_name = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    raw_text = Column(Text, nullable=False)
    
    # Store the ExtractedJobData JSON
    extracted_data = Column(JSONB, nullable=True)
    
    status = Column(String, default="pending", nullable=False) # pending, complete, failed
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", backref="job_descriptions")
