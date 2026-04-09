# app/api/v1/endpoints/ingest.py
# NEW FILE — trigger website re-scrape via API call (useful for manual refresh)

from fastapi import APIRouter, BackgroundTasks
from app.services.scraper_service import load_website_to_chromadb

router = APIRouter()

@router.post("/website")
def ingest_website(background_tasks: BackgroundTasks):
    """
    Trigger a fresh scrape of swaransoft.com into ChromaDB.
    Runs in background so the API returns immediately.
    """
    background_tasks.add_task(load_website_to_chromadb)
    return {"message": "Website ingestion started in background. Check terminal for progress."}
