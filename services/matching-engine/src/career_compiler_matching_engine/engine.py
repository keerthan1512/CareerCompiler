import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from groq_client import get_llm_client

logger = logging.getLogger(__name__)

class ProposedChange(BaseModel):
    requirement_id: str = Field(description="ID of the job requirement this change addresses")
    evidence_id: str = Field(description="ID of the resume evidence supporting this change")
    change_type: str = Field(description="Type of change: reword_bullet, reorder_bullet, add_keyword, add_bullet, remove_bullet")
    original_text: str = Field(description="Original resume text being changed (or empty if adding new)")
    proposed_text: str = Field(description="The new proposed text")
    rationale: str = Field(description="Human-readable explanation of why this change is proposed based on evidence")
    evidence_text: str = Field(description="The actual evidence text from the resume used to ground this change")

class TailoringPlanOutput(BaseModel):
    items: List[ProposedChange] = Field(description="List of proposed changes to the resume")

class MatchingEngine:
    """
    Core business logic for Phase 3:
    1. Matches Job Requirements to Canonical Profile Evidence.
    2. Generates a Tailoring Plan based on matches.
    """
    
    def __init__(self):
        self.llm = get_llm_client()

    async def generate_tailoring_plan(self, canonical_profile: dict, job_description: dict) -> TailoringPlanOutput:
        """
        Generate a set of proposed resume changes by matching job requirements against the canonical profile.
        """
        prompt = f"""
        You are an expert technical resume writer.
        Your task is to analyze a candidate's resume (Canonical Profile) and a Job Description.
        Generate a list of proposed changes to the resume to better match the job requirements.
        
        CRITICAL RULES:
        1. NEVER invent or hallucinate facts, skills, or experiences.
        2. EVERY proposed change MUST be grounded in existing evidence from the Canonical Profile.
        3. Provide clear rationale for each change.
        
        ## Job Description
        {job_description}
        
        ## Candidate Resume (Canonical Profile)
        {canonical_profile}
        """
        
        system_prompt = "You are an AI resume tailoring assistant. You only output valid JSON strictly conforming to the requested schema."
        
        result = await self.llm.astructured_chat(
            prompt=prompt,
            schema=TailoringPlanOutput,
            system_prompt=system_prompt
        )
        
        return result
