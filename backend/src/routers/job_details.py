from fastapi import APIRouter, HTTPException, Body

from services.job_details_fetcher import JobDetailsFetcherService

router = APIRouter()
fetcher_service = JobDetailsFetcherService()


@router.post("/fetch-job-details")
async def fetch_job_details(url: str = Body(..., embed=True)):
    """
    Fetch job details from a URL and return combined job description
    
    Args:
        url: The job posting URL
        
    Returns:
        Job details including combined formatted text
    """
    if not url or not url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    result = await fetcher_service.fetch_job_details(url.strip())

    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to fetch job details"))

    return result
