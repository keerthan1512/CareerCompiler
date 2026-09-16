"""
Evidence Extractor
Extracts discrete evidence items (skills, experience bullets, claims) from
a canonical profile. Evidence items are the atomic units used by the
Matching Engine (Phase 3) to link JD requirements to resume content.

Phase 1: builds evidence list from canonical profile.
Phase 3: adds embedding vectors to each evidence item.
"""

from __future__ import annotations

import re
import uuid
from typing import Optional


# ─── Evidence item types ──────────────────────────────────────────────────────

EVIDENCE_TYPES = {
    "skill": "A specific skill or technology mentioned",
    "bullet": "An experience bullet point describing an achievement or responsibility",
    "education": "An educational qualification or degree",
    "project": "A project or initiative",
    "certification": "A certification or credential",
    "summary": "A summary or objective statement",
}


def _make_evidence(
    ev_type: str,
    text: str,
    source_section: str,
    source_ref: dict,
    metadata: Optional[dict] = None,
) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "type": ev_type,
        "text": text,
        "source_section": source_section,
        "source_ref": source_ref,
        "metadata": metadata or {},
        "embedding": None,  # populated in Phase 3
    }


class EvidenceExtractor:
    """
    Extracts an Evidence list from a canonical profile dict.
    Evidence items are used by the Matching Engine to link JD requirements.
    """

    def extract(self, profile: dict) -> list[dict]:
        """
        Extract all evidence items from a canonical profile.

        Args:
            profile: Canonical profile dict (from CanonicalProfileBuilder)

        Returns:
            List of Evidence dicts, each with id, type, text, source_ref
        """
        evidence_list: list[dict] = []

        # Extract from sections
        for section in profile.get("sections", []):
            section_name = section.get("normalized_name", "other")
            raw_section_name = section.get("name", "")

            for entry in section.get("entries", []):
                # Extract entry header as evidence (experience/education/project titles)
                if section_name in ("experience", "education", "projects"):
                    header_text = self._entry_header_text(entry)
                    if header_text:
                        ev_type = {
                            "experience": "bullet",
                            "education": "education",
                            "projects": "project",
                        }.get(section_name, "bullet")
                        evidence_list.append(
                            _make_evidence(
                                ev_type=ev_type,
                                text=header_text,
                                source_section=raw_section_name,
                                source_ref=entry.get("source_ref", {}),
                                metadata={
                                    "title": entry.get("title", ""),
                                    "organization": entry.get("organization", ""),
                                    "dates": entry.get("dates", {}),
                                },
                            )
                        )

                # Extract bullets as individual evidence items
                for bullet in entry.get("bullets", []):
                    text = bullet.get("text", "").strip()
                    if text and len(text) > 5:
                        evidence_list.append(
                            _make_evidence(
                                ev_type="bullet",
                                text=text,
                                source_section=raw_section_name,
                                source_ref=bullet.get("source_ref", {}),
                                metadata={
                                    "parent_title": entry.get("title", ""),
                                    "parent_org": entry.get("organization", ""),
                                    "dates": entry.get("dates", {}),
                                },
                            )
                        )

            # Summary sections → summary evidence
            if section_name == "summary":
                for entry in section.get("entries", []):
                    summary_text = (
                        entry.get("raw_text", "")
                        or entry.get("organization", "")
                        or entry.get("title", "")
                    ).strip()
                    if summary_text:
                        evidence_list.append(
                            _make_evidence(
                                ev_type="summary",
                                text=summary_text,
                                source_section=raw_section_name,
                                source_ref=entry.get("source_ref", {}),
                            )
                        )

        # Extract skills as evidence
        for skill_group in profile.get("skills", []):
            for item in skill_group.get("items", []):
                skill_name = item.get("normalized") or item.get("name", "")
                if skill_name:
                    evidence_list.append(
                        _make_evidence(
                            ev_type="skill",
                            text=skill_name,
                            source_section="Skills",
                            source_ref=item.get("source_ref", {}),
                            metadata={
                                "category": skill_group.get("category", ""),
                                "raw_name": item.get("name", skill_name),
                            },
                        )
                    )

        return evidence_list

    def _entry_header_text(self, entry: dict) -> str:
        """Build a human-readable header string from an entry."""
        parts = []
        if entry.get("title"):
            parts.append(entry["title"])
        if entry.get("organization"):
            parts.append(f"at {entry['organization']}")
        if entry.get("dates", {}).get("raw"):
            parts.append(f"({entry['dates']['raw']})")
        return " ".join(parts)

    def extract_skills_flat(self, profile: dict) -> list[str]:
        """Return a flat list of normalized skill names from the profile."""
        skills = []
        for group in profile.get("skills", []):
            for item in group.get("items", []):
                normalized = item.get("normalized") or item.get("name", "")
                if normalized:
                    skills.append(normalized)
        return list(set(skills))
