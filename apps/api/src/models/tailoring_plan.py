import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.database import Base

class TailoringPlan(Base):
    __tablename__ = "tailoring_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False, index=True)
    master_resume_id = Column(UUID(as_uuid=True), ForeignKey("master_resumes.id"), nullable=False, index=True)
    
    mode = Column(String, default="review", nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, complete, failed
    
    iteration = Column(Integer, default=1, nullable=False)
    
    items = Column(JSONB, nullable=True) # The list of ProposedChanges
    metadata_obj = Column("metadata", JSONB, nullable=True) # renamed because metadata is reserved by declarative_base
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    job_description = relationship("JobDescription", backref="tailoring_plans")
    master_resume = relationship("MasterResume", backref="tailoring_plans")
