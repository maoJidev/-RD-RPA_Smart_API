# src/api/controllers/scrape_router.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from src.api.models.schemas import ScrapeRequest
from src.api.services.scrape_service import ScrapeService

router = APIRouter(prefix="/scrape", tags=["Scraper"])
scrape_service = ScrapeService()

@router.post("/")
def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    task_name = scrape_service.get_task_name(request.stage)
    if not task_name:
        raise HTTPException(status_code=400, detail="Invalid stage 1-8")
    
    background_tasks.add_task(scrape_service.run_task, task_name)
    return {
        "status": "accepted",
        "message": f"Stage {request.stage} ({task_name}) is running in background"
    }
