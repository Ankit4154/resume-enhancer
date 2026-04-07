from services.ai_model import AIModelProvider
from typing import Dict
import json

class JobMatchService:
    def __init__(self, model_provider: AIModelProvider):
        self.model_provider = model_provider

    async def analyze(self, resume_text: str, job_description: str) -> Dict:
        # simple heuristics first; deep model optional
        with open('prompts//job_match_prompt.md', 'r', encoding='utf-8') as file:
            content =  file.read()
        # optional rich JSON feedback via LLM
        prompt = content.format(resume_text=resume_text, job_description=job_description)
        detailed_json = await self.model_provider.get_completion(prompt)

        if isinstance(detailed_json, str):
            try:
                detailed_json = json.loads(detailed_json)
            except json.JSONDecodeError:
                detailed_json = {}

        if not isinstance(detailed_json, dict):
            detailed_json = {}

        score = detailed_json.get("score", 0)
        matching_skills = detailed_json.get("matching_skills") or detailed_json.get("matching_skills") or []
        missing_skills = detailed_json.get("missing_skills") or detailed_json.get("missing_skills") or []
        recommendations = detailed_json.get("recommendations") or []
        relevance = detailed_json.get("relevance", 0)

        return {
            "score": score,
            "matchingSkills": matching_skills,
            "missingSkills": missing_skills,
            "recommendations": recommendations,
            "relevance": relevance,
        }