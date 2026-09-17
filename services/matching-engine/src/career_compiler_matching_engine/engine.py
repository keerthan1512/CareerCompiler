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

def _compact_job_description(jd: Any) -> str:
    if not jd:
        return "No job description provided."
    if isinstance(jd, dict) and "extracted_data" in jd and jd["extracted_data"]:
        jd = jd["extracted_data"]
    if isinstance(jd, dict):
        parts = []
        if jd.get("title"):
            parts.append(f"Title: {jd['title']}")
        if jd.get("company"):
            parts.append(f"Company: {jd['company']}")
        if jd.get("requirements"):
            reqs = jd["requirements"]
            if isinstance(reqs, list):
                parts.append("Requirements:\n" + "\n".join(f"- {r}" for r in reqs[:15]))
            else:
                parts.append(f"Requirements: {reqs}")
        if jd.get("skills"):
            skills = jd["skills"]
            if isinstance(skills, list):
                parts.append("Required Skills: " + ", ".join(str(s) for s in skills[:20]))
            else:
                parts.append(f"Required Skills: {skills}")
        if jd.get("responsibilities"):
            resps = jd["responsibilities"]
            if isinstance(resps, list):
                parts.append("Responsibilities:\n" + "\n".join(f"- {r}" for r in resps[:10]))
        if parts:
            return "\n".join(parts)
        if jd.get("raw_text"):
            return str(jd["raw_text"])[:2000]
    return str(jd)[:2000]


def _compact_canonical_profile(profile: Any) -> str:
    if not profile or not isinstance(profile, dict):
        return str(profile)[:2500]

    parts = []
    contact = profile.get("contact") or {}
    if contact.get("name"):
        parts.append(f"Candidate: {contact.get('name')}")

    skills = profile.get("skills") or []
    if skills:
        if isinstance(skills, list):
            skills_str = ", ".join(s if isinstance(s, str) else s.get("name", "") for s in skills[:30])
            parts.append(f"Skills: {skills_str}")

    sections = profile.get("sections") or []
    for sec in sections:
        title = sec.get("title") or sec.get("name") or "Section"
        items = sec.get("items") or []
        sec_lines = [f"\n### {title}"]
        for item in items[:5]:
            if isinstance(item, str):
                sec_lines.append(f"- {item}")
            elif isinstance(item, dict):
                heading = item.get("title") or item.get("role") or item.get("company") or ""
                sub = item.get("subtitle") or item.get("organization") or ""
                bullets = item.get("bullets") or item.get("description") or []
                if heading or sub:
                    sec_lines.append(f"**{heading}** ({sub})" if sub else f"**{heading}**")
                if isinstance(bullets, list):
                    for b in bullets[:6]:
                        sec_lines.append(f"  - {b}")
                elif isinstance(bullets, str):
                    sec_lines.append(f"  - {bullets}")
        parts.append("\n".join(sec_lines))

    return "\n".join(parts) if parts else str(profile)[:3000]


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
        jd_text = _compact_job_description(job_description)
        profile_text = _compact_canonical_profile(canonical_profile)

        prompt = f"""
        You are an expert technical resume writer.
        Your task is to analyze a candidate's resume (Canonical Profile) and a Job Description.
        Generate a list of proposed changes to the resume to better match the job requirements.

        CRITICAL RULES:
        1. NEVER invent or hallucinate facts, skills, or experiences.
        2. EVERY proposed change MUST be grounded in existing evidence from the Canonical Profile.
        3. Provide clear rationale for each change.

        ## Job Description
        {jd_text}

        ## Candidate Resume (Canonical Profile)
        {profile_text}
        """

        system_prompt = "You are an AI resume tailoring assistant. You only output valid JSON strictly conforming to the requested schema."

        result = await self.llm.astructured_chat(
            prompt=prompt,
            schema=TailoringPlanOutput,
            system_prompt=system_prompt
        )

        return result
