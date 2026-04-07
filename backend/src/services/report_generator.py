from services.ats_analysis import ATSAnalysisService
from services.job_match import JobMatchService
from services.resume_structure import ResumeStructureService
from services.ai_model import AIModelProvider
import json

class ReportGeneratorService:
    def __init__(self, ats, job_match, structure, model_provider):
        self.ats = ats
        self.job_match = job_match
        self.structure = structure
        self.model_provider = model_provider

    async def generate_report(self, resume_text, job_description):
        ats_score = await self.ats.analyze(resume_text)
        job_match = await self.job_match.analyze(resume_text, job_description)
        structure = await self.structure.analyze(resume_text)
        suggestions = (
            [f"Add keyword: {k}" for k in ats_score["missingKeywords"]]
            + job_match["recommendations"]
            + structure["suggestions"]
        )

        detailed_feedback = await self.generateDetailedFeedback(ats_score, job_match, structure, resume_text, job_description)
        
        return {
            "atsScore": ats_score,
            "jobMatch": job_match,
            "structure": structure,
            "detailedFeedback": detailed_feedback,
            "suggestions": suggestions,
        }
    
    async def generateDetailedFeedback(self, ats_score, job_match, structure, resume_text, job_description):
        with open('prompts//report_generator_prompt.md', 'r', encoding='utf-8') as file:
            content =  file.read()
        # optional rich JSON feedback via LLM
        ats_score_score = ats_score.get("overall", 0)
        job_match_score = job_match.get("score", 0)
        structure_completeness = structure.get("completeness", 0)
        ats_keywords = ", ".join(ats_score["keywords"])
        ats_missing_keywords = ", ".join(ats_score["missingKeywords"])
        job_match_matching_skills = ", ".join(job_match["matchingSkills"])
        job_match_missing_skills = ", ".join(job_match["missingSkills"])
        structure_sections_present = ", ".join(structure["sectionsPresent"])
        structure_sections_missing = ", ".join(structure["sectionsMissing"])
        
        prompt = content.format(resume_text=resume_text, 
                                job_description=job_description,
                                ats_score_score=ats_score_score,
                                job_match_score=job_match_score,
                                structure_completeness=structure_completeness,
                                ats_keywords=ats_keywords,
                                ats_missing_keywords=ats_missing_keywords,
                                job_match_matching_skills=job_match_matching_skills,
                                job_match_missing_skills=job_match_missing_skills,
                                structure_sections_present=structure_sections_present,
                                structure_sections_missing=structure_sections_missing)
        detailed_json = await self.model_provider.get_completion(prompt)
        if isinstance(detailed_json, str):
            try:
                detailed_json = json.loads(detailed_json)
            except json.JSONDecodeError:
                detailed_json = {}

        if not isinstance(detailed_json, dict):
            detailed_json = {}


        overall_score = detailed_json.get("overall_score", 0)
        summary = detailed_json.get("summary") or detailed_json.get("summary") or []
        strengths = detailed_json.get("strengths") or detailed_json.get("strengths") or []
        weaknesses = detailed_json.get("weaknesses") or detailed_json.get("weaknesses") or []
        action_items = detailed_json.get("action_items") or detailed_json.get("action_items") or []
        improvement_plan = detailed_json.get("improvement_plan") or detailed_json.get("improvement_plan") or ""

        return {
            "overallScore": overall_score,
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "actionItems": action_items,
            "improvementPlan": improvement_plan
        }