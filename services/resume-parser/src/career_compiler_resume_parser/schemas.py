from typing import List, Optional
from pydantic import BaseModel, Field

class ParsedContact(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    website: Optional[str] = Field(None, description="Personal website URL")
    location: Optional[str] = Field(None, description="City, State, or Country")

class ParsedBullet(BaseModel):
    text: str = Field(description="A single bullet point describing an achievement or responsibility")

class ParsedDateRange(BaseModel):
    start: str = Field(description="Start date (e.g., 'Jan 2020')")
    end: str = Field(description="End date (e.g., 'Present' or 'Dec 2022')")
    raw: str = Field(description="The raw date string from the resume")

class ParsedEntry(BaseModel):
    title: str = Field(description="Job title, degree, or project name")
    organization: str = Field(description="Company, university, or organization name")
    location: str = Field(description="Location of the entry")
    dates: ParsedDateRange
    bullets: List[ParsedBullet] = Field(default_factory=list)

class ParsedSection(BaseModel):
    name: str = Field(description="Original section name (e.g., 'Professional Experience', 'Education')")
    normalized_name: str = Field(description="Normalized section name (one of: experience, education, projects, certifications, summary)")
    entries: List[ParsedEntry] = Field(default_factory=list)

class ParsedSkillItem(BaseModel):
    name: str = Field(description="Name of the skill")
    normalized: str = Field(description="Lowercase, standardized name of the skill")

class ParsedSkillGroup(BaseModel):
    category: str = Field(description="Category of skills (e.g., 'Languages', 'Frameworks')")
    items: List[ParsedSkillItem] = Field(default_factory=list)

class ParsedProfile(BaseModel):
    contact: Optional[ParsedContact] = None
    sections: List[ParsedSection] = Field(default_factory=list)
    skills: List[ParsedSkillGroup] = Field(default_factory=list)
