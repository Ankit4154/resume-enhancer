from services.ai_model import AIModelProvider
from typing import Dict
import json

class ResumeStructureService:
    def __init__(self, model_provider: AIModelProvider):
        self.model_provider = model_provider

    async def analyze(self, resume_text: str) -> Dict:
        with open('prompts//resume_structure_prompt.md', 'r', encoding='utf-8') as file:
            content =  file.read()
        # optional rich JSON feedback via LLM
        prompt = content.format(resume_text=resume_text)
        detailed_json = await self.model_provider.get_completion(prompt)

        if isinstance(detailed_json, str):
            try:
                detailed_json = json.loads(detailed_json)
            except json.JSONDecodeError:
                detailed_json = {}

        if not isinstance(detailed_json, dict):
            detailed_json = {}

        completeness = detailed_json.get("completeness", 0)
        sections_present = detailed_json.get("sections_present") or detailed_json.get("sections_present") or []
        sections_missing = detailed_json.get("sections_missing") or detailed_json.get("sections_missing") or []
        suggestions = detailed_json.get("suggestions") or detailed_json.get("suggestions") or []
        readability = detailed_json.get("readability", 0)

        return {
            "completeness": completeness,
            "sectionsPresent": sections_present,
            "sectionsMissing": sections_missing,
            "suggestions": suggestions,
            "readability": readability
        }