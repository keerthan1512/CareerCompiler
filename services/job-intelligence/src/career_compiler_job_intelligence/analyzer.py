import json
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from groq_client import get_llm_client
from .schemas import ExtractedJobData

class JobAnalyzer:
    def __init__(self):
        self.llm_client = get_llm_client()
    
    async def analyze(self, raw_text: str) -> ExtractedJobData:
        """
        Analyzes a raw job description text and extracts structured data.
        Returns a validated ExtractedJobData Pydantic object.
        """
        prompt = f"Extract structured information from the following Job Description:\n\n{raw_text}"
        system_prompt = "You are an expert technical recruiter and HR analyst. Your task is to carefully read the provided job description and extract the required information accurately. Categorize skills, responsibilities, and requirements explicitly."
        
        result = await self.llm_client.astructured_chat(
            prompt=prompt,
            schema=ExtractedJobData,
            system_prompt=system_prompt
        )
        return result
