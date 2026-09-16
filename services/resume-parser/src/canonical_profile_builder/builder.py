"""
Canonical Profile Builder
Converts a RawAST (from LaTeXParser) into the canonical profile JSON structure.
Every field includes a source_ref linking back to the original .tex file.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from latex_ast_parser.parser import (
    RawAST,
    RawBullet,
    RawContact,
    RawEntry,
    RawSection,
    SourceRef,
)
from latex_ast_parser.section_detector import normalize_section_name

PARSER_VERSION = "1.0.0"

# ─── Date normalization ───────────────────────────────────────────────────────

_DATE_VARIANTS = {
    "present": "Present",
    "current": "Present",
    "now": "Present",
    "ongoing": "Present",
}

_MONTH_ABBREVS = {
    "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
    "may": "May", "jun": "Jun", "jul": "Jul", "aug": "Aug",
    "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dec",
}


def _normalize_date(raw: str) -> str:
    """Normalize a date string: 'September 2020' → 'Sep 2020', 'present' → 'Present'."""
    raw = raw.strip()
    lower = raw.lower()
    if lower in _DATE_VARIANTS:
        return _DATE_VARIANTS[lower]
    # Try to shorten month names
    for full, abbrev in {
        "january": "Jan", "february": "Feb", "march": "Mar",
        "april": "Apr", "june": "Jun", "july": "Jul",
        "august": "Aug", "september": "Sep", "october": "Oct",
        "november": "Nov", "december": "Dec",
    }.items():
        raw = re.sub(full, abbrev, raw, flags=re.IGNORECASE)
    return raw.strip()


def _parse_date_range(raw: str) -> dict:
    """
    Parse a date range string like 'Jan 2022 – Present' or '2019 - 2022'.
    Returns {"start": "...", "end": "...", "raw": "..."}.
    """
    raw = raw.strip()
    if not raw:
        return {"start": "", "end": "", "raw": ""}

    # Try to split on common separators
    parts = re.split(r"\s*[–—\-–\/]\s*|\s+to\s+", raw, maxsplit=1)
    if len(parts) == 2:
        start = _normalize_date(parts[0])
        end = _normalize_date(parts[1])
    else:
        start = _normalize_date(raw)
        end = ""

    return {"start": start, "end": end, "raw": raw}


# ─── Skill normalization (Phase 1 basic map) ──────────────────────────────────

SKILL_ALIASES: dict[str, str] = {
    "react.js": "React",
    "reactjs": "React",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "amazon web services": "AWS",
    "google cloud platform": "GCP",
    "microsoft azure": "Azure",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python3": "Python",
    "golang": "Go",
    "c++": "C++",
    "cpp": "C++",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "dl": "Deep Learning",
    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "ci/cd": "CI/CD",
    "rest api": "REST API",
    "restful": "REST API",
}


def normalize_skill(raw: str) -> str:
    """Normalize a skill name using the alias map."""
    cleaned = raw.strip().rstrip(".,;")
    normalized = SKILL_ALIASES.get(cleaned.lower(), cleaned)
    return normalized


# ─── Builder ─────────────────────────────────────────────────────────────────


def _sourced(value: str, source_ref: SourceRef) -> dict:
    """Create a sourced field dict."""
    return {"value": value, "source_ref": source_ref.to_dict()}


class CanonicalProfileBuilder:
    """
    Converts a RawAST produced by LaTeXParser into the canonical profile JSON.
    """

    def build(self, ast: RawAST, resume_id: str) -> dict:
        """
        Build and return the canonical profile as a dict (JSON-serializable).

        Args:
            ast: RawAST from LaTeXParser
            resume_id: UUID of the MasterResume record

        Returns:
            Canonical profile dict matching canonical_profile.schema.json
        """
        profile = {
            "resume_id": resume_id,
            "parser_version": PARSER_VERSION,
            "contact": self._build_contact(ast.contact, ast.filename),
            "sections": self._build_sections(ast.sections, ast.filename),
            "skills": [],  # populated below from skill sections
            "template": {
                "document_class": ast.document_class,
                "packages": ast.packages,
                "detected_format": ast.detected_format,
            },
            "metadata": {
                "parsed_at": datetime.now(timezone.utc).isoformat(),
                "source_file": ast.filename,
                "total_sections": len(ast.sections),
                "total_bullets": 0,
                "total_skills": 0,
                "parse_errors": ast.parse_errors,
            },
        }

        # Extract skill groups from skills sections and move to top-level
        skill_sections = [s for s in profile["sections"] if s["normalized_name"] == "skills"]
        profile["skills"] = self._extract_skill_groups(skill_sections, ast)
        profile["metadata"]["total_skills"] = sum(
            len(sg["items"]) for sg in profile["skills"]
        )

        # Count total bullets
        total_bullets = sum(
            len(entry["bullets"])
            for section in profile["sections"]
            for entry in section.get("entries", [])
        )
        profile["metadata"]["total_bullets"] = total_bullets

        return profile

    # ─── Contact ─────────────────────────────────────────────────────────────

    def _build_contact(self, contact: RawContact, filename: str) -> dict:
        result = {}
        fields = [
            ("name", contact.name, contact.name_line),
            ("email", contact.email, contact.email_line),
            ("phone", contact.phone, contact.phone_line),
            ("linkedin", contact.linkedin, contact.linkedin_line),
            ("github", contact.github, contact.github_line),
            ("website", contact.website, contact.website_line),
            ("location", contact.location, contact.location_line),
        ]
        for key, value, line_num in fields:
            if value:
                result[key] = _sourced(
                    value, SourceRef(filename, line_num or 1, line_num or 1)
                )
        return result

    # ─── Sections ────────────────────────────────────────────────────────────

    def _build_sections(self, raw_sections: list[RawSection], filename: str) -> list[dict]:
        sections = []
        for raw_sec in raw_sections:
            normalized = normalize_section_name(raw_sec.name)
            section = {
                "id": raw_sec.id,
                "name": raw_sec.name,
                "normalized_name": normalized,
                "source_ref": raw_sec.source_ref.to_dict(),
                "entries": self._build_entries(raw_sec.entries, filename),
            }
            sections.append(section)
        return sections

    def _build_entries(self, raw_entries: list[RawEntry], filename: str) -> list[dict]:
        entries = []
        for raw_entry in raw_entries:
            entry = {
                "id": raw_entry.id,
                "title": raw_entry.title,
                "organization": raw_entry.organization,
                "location": raw_entry.location,
                "dates": _parse_date_range(raw_entry.date_raw),
                "source_ref": raw_entry.source_ref.to_dict(),
                "bullets": self._build_bullets(raw_entry.bullets, filename),
            }
            entries.append(entry)
        return entries

    def _build_bullets(self, raw_bullets: list[RawBullet], filename: str) -> list[dict]:
        return [
            {
                "id": b.id,
                "text": b.text,
                "source_ref": b.source_ref.to_dict(),
            }
            for b in raw_bullets
            if b.text.strip()
        ]

    # ─── Skills ──────────────────────────────────────────────────────────────

    def _extract_skill_groups(
        self, skill_sections: list[dict], ast: RawAST
    ) -> list[dict]:
        """
        Convert skill section entries into structured SkillGroup dicts.
        Handles: 'Languages: Python, Java' style, comma-separated lists,
        and cvitem-style rows (label=category, org=skill list).
        """
        groups = []

        for section in skill_sections:
            for entry in section.get("entries", []):
                category = entry.get("title", "").strip()
                org = entry.get("organization", "").strip()

                if category and org:
                    # cvitem style: label=category, org=skill list
                    items = self._parse_skill_list(org, entry["source_ref"])
                    if items:
                        groups.append({
                            "id": str(uuid.uuid4()),
                            "category": category,
                            "items": items,
                            "source_ref": entry["source_ref"],
                        })
                elif org:
                    # Plain skill list without category
                    items = self._parse_skill_list(org, entry["source_ref"])
                    if items:
                        groups.append({
                            "id": str(uuid.uuid4()),
                            "category": "Skills",
                            "items": items,
                            "source_ref": entry["source_ref"],
                        })

        return groups

    def _parse_skill_list(self, text: str, source_ref: dict) -> list[dict]:
        """
        Parse a comma/semicolon/pipe-separated skill list.
        Returns list of SkillItem dicts.
        """
        items = []
        # Split on common delimiters
        parts = re.split(r"[,;|•·]+", text)
        for part in parts:
            skill_name = part.strip().rstrip(".")
            if not skill_name or len(skill_name) < 2:
                continue
            items.append({
                "name": skill_name,
                "normalized": normalize_skill(skill_name),
                "source_ref": source_ref,
            })
        return items
