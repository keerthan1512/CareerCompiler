"""Pydantic schemas for MasterResume requests and responses"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MasterResumeUploadResponse(BaseModel):
    """Response after uploading a master resume."""
    id: uuid.UUID
    display_name: str
    status: str  # "parsing" in Phase 1 (synchronous), "pending" for async
    profile_id: Optional[uuid.UUID] = None
    job_id: Optional[uuid.UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceRef(BaseModel):
    file: str
    line_start: int
    line_end: int


class SourcedField(BaseModel):
    value: str
    source_ref: SourceRef


class Contact(BaseModel):
    name: Optional[SourcedField] = None
    email: Optional[SourcedField] = None
    phone: Optional[SourcedField] = None
    linkedin: Optional[SourcedField] = None
    github: Optional[SourcedField] = None
    website: Optional[SourcedField] = None
    location: Optional[SourcedField] = None


class Bullet(BaseModel):
    id: uuid.UUID
    text: str
    source_ref: SourceRef


class DateRange(BaseModel):
    start: str
    end: str
    raw: str


class Entry(BaseModel):
    id: uuid.UUID
    title: str = ""
    organization: str = ""
    location: str = ""
    dates: DateRange
    source_ref: SourceRef
    bullets: list[Bullet]


class Section(BaseModel):
    id: uuid.UUID
    name: str
    normalized_name: str
    source_ref: SourceRef
    entries: list[Entry]


class SkillItem(BaseModel):
    name: str
    normalized: str
    source_ref: Optional[SourceRef] = None


class SkillGroup(BaseModel):
    id: uuid.UUID
    category: str
    items: list[SkillItem]
    source_ref: Optional[SourceRef] = None


class Template(BaseModel):
    document_class: str
    packages: list[str]
    detected_format: str


class ProfileMetadata(BaseModel):
    parsed_at: str
    source_file: str
    total_sections: int
    total_bullets: int
    total_skills: int
    parse_errors: list[str] = []


class CanonicalProfileResponse(BaseModel):
    """Full canonical profile, embedded in the resume detail response."""
    id: uuid.UUID
    master_resume_id: uuid.UUID
    status: str
    parser_version: str
    contact: Optional[Contact] = None
    sections: Optional[list[Section]] = None
    skills: Optional[list[SkillGroup]] = None
    template: Optional[Template] = None
    metadata: Optional[ProfileMetadata] = None
    error_message: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class MasterResumeDetailResponse(BaseModel):
    """Full resume detail including canonical profile."""
    id: uuid.UUID
    display_name: str
    checksum: str
    template_metadata: dict
    created_at: datetime
    canonical_profile: Optional[CanonicalProfileResponse] = None

    model_config = {"from_attributes": True}



