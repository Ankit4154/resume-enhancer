from typing import Dict, List
from services.ai_model import AIModelProvider
import json

class ATSAnalysisService:
    def __init__(self, model_provider: AIModelProvider):
        self.model_provider = model_provider

    async def analyze(self, resume_text: str) -> Dict:
        with open('prompts//ats_analysis_prompt.md', 'r', encoding='utf-8') as file:
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

        overall = detailed_json.get("overall", 0)
        keywords = detailed_json.get("keywords") or detailed_json.get("keywords") or []
        missing_keywords = detailed_json.get("missing_keywords") or detailed_json.get("missing_keywords") or []
        format_score = detailed_json.get("format_score", 0)
        return {
            "overall": overall,
            "keywords": keywords,
            "missingKeywords": missing_keywords,
            "formatScore" : format_score
        }