from fastapi import APIRouter, HTTPException, Body
from services.report_generator import ReportGeneratorService
from services.ats_analysis import ATSAnalysisService
from services.job_match import JobMatchService
from services.resume_structure import ResumeStructureService
from services.ai_model import GlobalAIProvider

router = APIRouter()
provider = GlobalAIProvider()
report_service = ReportGeneratorService(
    ATSAnalysisService(provider),
    JobMatchService(provider),
    ResumeStructureService(provider),
    provider,
)

@router.post("/analyze")
async def analyze(resumeText: str = Body(..., embed=True), jobDescription: str = Body(...)):
    if not resumeText or not jobDescription:
        raise HTTPException(400, "resumeText and jobDescription required")
    report = await report_service.generate_report(resumeText, jobDescription)
    return report