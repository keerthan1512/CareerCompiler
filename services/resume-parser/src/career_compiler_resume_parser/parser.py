import io
import uuid
import logging
from typing import Dict, Any

from PyPDF2 import PdfReader

from groq_client import get_llm_client
from .schemas import ParsedProfile

logger = logging.getLogger(__name__)

class PdfParser:
    def __init__(self):
        self.llm_client = get_llm_client()
    
    async def parse(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses a PDF file bytes, extracts text, and uses LLM to structure into Canonical Profile JSON.
        Injects UUIDs and source_refs into the LLM output.
        """
        raw_text = self._extract_text(pdf_bytes)
        
        system_prompt = (
            "You are an expert ATS parser. Your job is to extract the applicant's profile from "
            "the provided resume text and structure it precisely into the provided schema. "
            "Be incredibly accurate with dates, bullets, and section classification."
        )
        
        prompt = f"Please parse this resume text:\n\n{raw_text}"
        
        # Structure the text using Groq
        parsed_profile: ParsedProfile = await self.llm_client.astructured_chat(
            prompt=prompt,
            schema=ParsedProfile,
            system_prompt=system_prompt
        )
        
        return self._hydrate_with_ids(parsed_profile, filename)
    
    def _extract_text(self, pdf_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise Exception("Invalid PDF or failed to extract text")
    
    def _hydrate_with_ids(self, profile: ParsedProfile, filename: str) -> Dict[str, Any]:
        """Convert ParsedProfile to CanonicalProfile JSON with UUIDs and source refs."""
        data = profile.model_dump()
        
        def _dummy_ref():
            return {"file": filename, "line_start": 0, "line_end": 0}
            
        def _sourced(value):
            if value is None:
                return None
            return {"value": value, "source_ref": _dummy_ref()}

        hydrated = {
            "contact": {},
            "sections": [],
            "skills": [],
            "template": {
                "document_class": "article",
                "packages": [],
                "detected_format": "pdf_upload"
            },
            "metadata": {
                "parsed_at": "now",
                "source_file": filename,
                "total_sections": len(data.get("sections", [])),
                "total_bullets": sum(len(e.get("bullets", [])) for s in data.get("sections", []) for e in s.get("entries", [])),
                "total_skills": sum(len(g.get("items", [])) for g in data.get("skills", [])),
                "parse_errors": []
            }
        }
        
        # Hydrate Contact
        contact = data.get("contact") or {}
        for k, v in contact.items():
            hydrated["contact"][k] = _sourced(v)
            
        # Hydrate Sections
        for sec in data.get("sections", []):
            hydrated_sec = {
                "id": str(uuid.uuid4()),
                "name": sec.get("name"),
                "normalized_name": sec.get("normalized_name"),
                "source_ref": _dummy_ref(),
                "entries": []
            }
            
            for ent in sec.get("entries", []):
                hydrated_ent = {
                    "id": str(uuid.uuid4()),
                    "title": ent.get("title", ""),
                    "organization": ent.get("organization", ""),
                    "location": ent.get("location", ""),
                    "dates": ent.get("dates", {}),
                    "source_ref": _dummy_ref(),
                    "bullets": []
                }
                
                for b in ent.get("bullets", []):
                    hydrated_ent["bullets"].append({
                        "id": str(uuid.uuid4()),
                        "text": b.get("text"),
                        "source_ref": _dummy_ref()
                    })
                
                hydrated_sec["entries"].append(hydrated_ent)
                
            hydrated["sections"].append(hydrated_sec)
            
        # Hydrate Skills
        for grp in data.get("skills", []):
            hydrated_grp = {
                "id": str(uuid.uuid4()),
                "category": grp.get("category"),
                "source_ref": _dummy_ref(),
                "items": []
            }
            
            for item in grp.get("items", []):
                hydrated_grp["items"].append({
                    "name": item.get("name"),
                    "normalized": item.get("normalized"),
                    "source_ref": _dummy_ref()
                })
                
            hydrated["skills"].append(hydrated_grp)
            
        return hydrated
