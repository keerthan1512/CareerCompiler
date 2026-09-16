import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, HttpUrl

class JobDescriptionCreate(BaseModel):
    display_name: Optional[str] = Field(None, description="Optional name for this JD")
    source_url: Optional[HttpUrl] = Field(None, description="Optional source URL")
    raw_text: str = Field(..., description="The raw job description text")

class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    display_name: Optional[str] = None
    source_url: Optional[str] = None
    status: str
    extracted_data: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
