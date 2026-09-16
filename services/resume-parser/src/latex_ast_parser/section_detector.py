"""
Section Detector
Maps raw section names to normalized canonical categories.
"""

from __future__ import annotations

# Canonical section names → list of recognized raw names (lowercase)
SECTION_MAP: dict[str, list[str]] = {
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "career history",
        "professional background", "employment",
    ],
    "education": [
        "education", "academic background", "qualifications",
        "academic qualifications", "academic history", "educational background",
        "degrees",
    ],
    "skills": [
        "skills", "technical skills", "core competencies", "competencies",
        "technical expertise", "technologies", "tools & technologies",
        "technical proficiencies", "tools", "languages & technologies",
        "technical stack",
    ],
    "projects": [
        "projects", "personal projects", "academic projects", "side projects",
        "selected projects", "key projects", "notable projects",
        "open source", "portfolio",
    ],
    "publications": [
        "publications", "research", "papers", "journal articles",
        "conference papers", "preprints",
    ],
    "awards": [
        "awards", "honors", "achievements", "recognition", "accomplishments",
        "honors & awards", "distinctions",
    ],
    "summary": [
        "summary", "profile", "about", "objective", "professional summary",
        "executive summary", "career objective", "about me", "professional profile",
        "overview",
    ],
    "certifications": [
        "certifications", "certificates", "licenses", "credentials",
        "professional certifications",
    ],
    "languages": [
        "languages", "language skills", "spoken languages",
        "human languages",
    ],
    "volunteering": [
        "volunteering", "volunteer experience", "community involvement",
        "community service", "social work",
    ],
    "interests": [
        "interests", "hobbies", "extracurricular", "extracurricular activities",
        "activities",
    ],
}


def normalize_section_name(raw_name: str) -> str:
    """
    Map a raw section heading to a canonical normalized name.

    Args:
        raw_name: The section name as it appears in the LaTeX source

    Returns:
        One of the canonical section keys, or "other" if unrecognized
    """
    cleaned = raw_name.lower().strip().rstrip(":")

    for normalized, variants in SECTION_MAP.items():
        for variant in variants:
            if cleaned == variant or cleaned.startswith(variant) or variant in cleaned:
                return normalized

    return "other"


def is_resume_section(raw_name: str) -> bool:
    """Return True if the section name looks like a resume section."""
    return normalize_section_name(raw_name) != "other"
