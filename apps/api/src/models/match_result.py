import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.database import Base

class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False, index=True)
    master_resume_id = Column(UUID(as_uuid=True), ForeignKey("master_resumes.id"), nullable=False, index=True)
    
    requirement_id = Column(String, nullable=False)
    requirement_text = Column(String, nullable=False)
    
    evidence_id = Column(String, nullable=True)
    evidence_text = Column(String, nullable=True)
    evidence_source_ref = Column(JSONB, nullable=True)
    
    category = Column(String, nullable=False)  # Direct, Transferable, Gap
    confidence = Column(Float, nullable=False)
    explanation = Column(String, nullable=True)
    
    matched_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    job_description = relationship("JobDescription", backref="match_results")
    master_resume = relationship("MasterResume", backref="match_results")
