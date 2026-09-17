"""
Templater for Document Engineering
Applies TailoringPlan changes to a CanonicalProfile JSON and renders HTML via Jinja2.
"""
from jinja2 import Environment, FileSystemLoader
import copy
from pathlib import Path

def apply_tailoring_plan(profile_data: dict, plan_items: list[dict]) -> dict:
    """
    Mutates a copy of the canonical profile JSON with approved TailoringPlan changes.
    """
    modified_profile = copy.deepcopy(profile_data)
    
    # Very basic mutation logic for MVP
    # In reality, this would search the JSON tree matching `requirement_id` or `original_text`
    # and update the respective node.
    
    # Find the experience section
    experiences_entries = []
    sections = modified_profile.get("sections", [])
    if isinstance(sections, list):
        for sec in sections:
            if sec.get("normalized_name") == "experience":
                experiences_entries = sec.get("entries", [])
                break
    
    for item in plan_items:
        new_text = item.get("user_edited_text") or item.get("proposed_text", "")
        change_type = item.get("change_type")
        
        if change_type == "add_bullet" and experiences_entries:
            # Just append to the first job for MVP demonstration
            if "bullets" not in experiences_entries[0]:
                experiences_entries[0]["bullets"] = []
            experiences_entries[0]["bullets"].append(new_text)
            
    return modified_profile

def render_html(profile_data: dict) -> str:
    """
    Renders the JSON profile using a Jinja2 template.
    """
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = env.get_template("default_resume.html")
    
    return template.render(profile=profile_data)
