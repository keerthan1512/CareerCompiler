"""
Tests for the LaTeX resume parser pipeline.
Run: cd services/resume-parser && python -m pytest tests/ -v
"""

from pathlib import Path
import pytest

from src.latex_ast_parser.parser import LaTeXParser
from src.latex_ast_parser.section_detector import normalize_section_name
from src.canonical_profile_builder.builder import CanonicalProfileBuilder
from src.evidence_extractor.extractor import EvidenceExtractor

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE_MODERNCV = FIXTURE_DIR / "sample_moderncv.tex"

RESUME_ID = "11111111-1111-1111-1111-111111111111"


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def moderncv_content() -> str:
    return SAMPLE_MODERNCV.read_text()


@pytest.fixture
def parsed_ast(moderncv_content):
    parser = LaTeXParser()
    return parser.parse(moderncv_content, filename="sample_moderncv.tex")


@pytest.fixture
def canonical_profile(parsed_ast):
    builder = CanonicalProfileBuilder()
    return builder.build(parsed_ast, resume_id=RESUME_ID)


# ─── Parser Tests ─────────────────────────────────────────────────────────────


class TestLaTeXParser:
    def test_parses_without_error(self, moderncv_content):
        parser = LaTeXParser()
        ast = parser.parse(moderncv_content)
        assert ast is not None

    def test_detects_moderncv_format(self, parsed_ast):
        assert parsed_ast.detected_format == "moderncv"

    def test_document_class_extracted(self, parsed_ast):
        assert "moderncv" in parsed_ast.document_class

    def test_packages_extracted(self, parsed_ast):
        assert len(parsed_ast.packages) > 0

    def test_contact_name_extracted(self, parsed_ast):
        assert parsed_ast.contact.name != ""
        assert "Jane" in parsed_ast.contact.name or "Doe" in parsed_ast.contact.name

    def test_contact_email_extracted(self, parsed_ast):
        assert "@" in (parsed_ast.contact.email or "")

    def test_contact_phone_extracted(self, parsed_ast):
        assert parsed_ast.contact.phone != ""

    def test_contact_github_extracted(self, parsed_ast):
        assert "github.com" in (parsed_ast.contact.github or "")

    def test_contact_linkedin_extracted(self, parsed_ast):
        assert "linkedin.com" in (parsed_ast.contact.linkedin or "")

    def test_sections_found(self, parsed_ast):
        assert len(parsed_ast.sections) >= 3

    def test_experience_section_found(self, parsed_ast):
        section_names = [s.name.lower() for s in parsed_ast.sections]
        assert any("experience" in n for n in section_names)

    def test_sections_have_source_refs(self, parsed_ast):
        for section in parsed_ast.sections:
            assert section.source_ref.line_start > 0


# ─── Section Detector Tests ───────────────────────────────────────────────────


class TestSectionDetector:
    @pytest.mark.parametrize("raw,expected", [
        ("Experience", "experience"),
        ("Work Experience", "experience"),
        ("Professional Experience", "experience"),
        ("Education", "education"),
        ("Technical Skills", "skills"),
        ("Skills & Technologies", "skills"),
        ("Projects", "projects"),
        ("Personal Projects", "projects"),
        ("Summary", "summary"),
        ("Professional Summary", "summary"),
        ("Certifications", "certifications"),
        ("Awards & Honors", "awards"),
        ("random section name xyz", "other"),
    ])
    def test_normalize_section_name(self, raw, expected):
        assert normalize_section_name(raw) == expected


# ─── Canonical Profile Builder Tests ──────────────────────────────────────────


class TestCanonicalProfileBuilder:
    def test_profile_has_required_keys(self, canonical_profile):
        for key in ["resume_id", "parser_version", "contact", "sections", "skills", "template", "metadata"]:
            assert key in canonical_profile

    def test_resume_id_preserved(self, canonical_profile):
        assert canonical_profile["resume_id"] == RESUME_ID

    def test_parser_version_set(self, canonical_profile):
        assert canonical_profile["parser_version"] == "1.0.0"

    def test_contact_has_name(self, canonical_profile):
        contact = canonical_profile["contact"]
        assert "name" in contact
        assert contact["name"]["value"] != ""

    def test_contact_has_source_ref(self, canonical_profile):
        contact = canonical_profile["contact"]
        if "name" in contact:
            ref = contact["name"]["source_ref"]
            assert "file" in ref
            assert "line_start" in ref
            assert ref["line_start"] > 0

    def test_sections_normalized(self, canonical_profile):
        normalized_names = {s["normalized_name"] for s in canonical_profile["sections"]}
        assert "experience" in normalized_names

    def test_bullets_extracted(self, canonical_profile):
        total_bullets = 0
        for section in canonical_profile["sections"]:
            for entry in section.get("entries", []):
                total_bullets += len(entry.get("bullets", []))
        assert total_bullets > 0

    def test_bullets_have_source_refs(self, canonical_profile):
        for section in canonical_profile["sections"]:
            for entry in section.get("entries", []):
                for bullet in entry.get("bullets", []):
                    ref = bullet.get("source_ref", {})
                    assert "file" in ref
                    assert "line_start" in ref

    def test_skills_extracted(self, canonical_profile):
        assert len(canonical_profile["skills"]) > 0

    def test_skill_items_normalized(self, canonical_profile):
        for group in canonical_profile["skills"]:
            for item in group["items"]:
                assert "normalized" in item
                assert item["normalized"] != ""

    def test_metadata_counts(self, canonical_profile):
        meta = canonical_profile["metadata"]
        assert meta["total_sections"] > 0
        assert meta["total_bullets"] > 0
        assert meta["total_skills"] > 0


# ─── Evidence Extractor Tests ─────────────────────────────────────────────────


class TestEvidenceExtractor:
    def test_extracts_evidence(self, canonical_profile):
        extractor = EvidenceExtractor()
        evidence = extractor.extract(canonical_profile)
        assert len(evidence) > 0

    def test_evidence_has_required_fields(self, canonical_profile):
        extractor = EvidenceExtractor()
        evidence = extractor.extract(canonical_profile)
        for ev in evidence:
            assert "id" in ev
            assert "type" in ev
            assert "text" in ev
            assert "source_ref" in ev

    def test_extracts_skill_evidence(self, canonical_profile):
        extractor = EvidenceExtractor()
        evidence = extractor.extract(canonical_profile)
        skill_evidence = [e for e in evidence if e["type"] == "skill"]
        assert len(skill_evidence) > 0

    def test_extracts_bullet_evidence(self, canonical_profile):
        extractor = EvidenceExtractor()
        evidence = extractor.extract(canonical_profile)
        bullet_evidence = [e for e in evidence if e["type"] == "bullet"]
        assert len(bullet_evidence) > 0

    def test_evidence_texts_non_empty(self, canonical_profile):
        extractor = EvidenceExtractor()
        evidence = extractor.extract(canonical_profile)
        for ev in evidence:
            assert ev["text"].strip() != ""

    def test_flat_skills_list(self, canonical_profile):
        extractor = EvidenceExtractor()
        skills = extractor.extract_skills_flat(canonical_profile)
        assert isinstance(skills, list)
        assert len(skills) > 0
        assert all(isinstance(s, str) for s in skills)
