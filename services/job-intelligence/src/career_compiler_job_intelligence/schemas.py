from typing import List, Literal, Optional
from pydantic import BaseModel, Field, HttpUrl
import uuid

class SkillItem(BaseModel):
    name: str = Field(description="The raw name of the skill")
    normalized: str = Field(description="The normalized standard name of the skill (e.g. 'react.js' -> 'react')")
    required: bool = Field(description="Whether this skill is a must-have requirement (true) or a nice-to-have (false)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this extraction (0.0 to 1.0)")

class ResponsibilityItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(description="The raw text of the responsibility")
    category: str = Field(description="Category of the responsibility (e.g., 'technical', 'leadership', 'communication')")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this extraction (0.0 to 1.0)")

class RequirementItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(description="The raw text of the requirement")
    type: Literal["must-have", "nice-to-have", "unknown"] = Field(description="Is this a must-have or nice-to-have?")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this extraction (0.0 to 1.0)")

class ExtractedJobData(BaseModel):
    title: str = Field(description="The job title")
    company: str = Field(description="The company name")
    seniority: Literal["intern", "junior", "mid", "senior", "lead", "principal", "staff", "unknown"] = Field(description="The seniority level")
    domain: str = Field(description="The industry or technical domain (e.g., 'Fintech', 'SaaS', 'E-commerce')")
    location: str = Field(description="The location of the job (or 'Remote')")
    employment_type: Literal["full-time", "part-time", "contract", "internship", "unknown"] = Field(description="The employment type")
    skills: List[SkillItem] = Field(description="List of skills mentioned in the job description")
    responsibilities: List[ResponsibilityItem] = Field(description="List of core responsibilities")
    requirements: List[RequirementItem] = Field(description="List of other requirements (e.g., degree, years of experience)")
