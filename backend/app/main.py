from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import logging
from pathlib import Path

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine

# Import base AFTER engine — registers all models (User, WhatsAppUser, ChatLog ...)
from app.db import base  # noqa: F401 — side-effect: registers all models
from app.db.base_class import Base

app = FastAPI()

# ✅ Auto-create all tables (including whatsapp_users) on startup
Base.metadata.create_all(bind=engine)

# ✅ CORS
origins = [
    "https://rag.gignaati.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://localhost:3000",        # ADD THIS
    "http://127.0.0.1:3000",       # ADD THIS (optional)
    "http://localhost:5173",        # Vite dev server
    "http://127.0.0.1:5173",       # Vite dev server (optional)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ✅ Static files
app.mount("/static",   StaticFiles(directory="static"),   name="static")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ✅ Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ✅ Home route
@app.get("/", response_class=FileResponse)
def home():
    logger.info("Home page accessed")
    return FileResponse(Path("frontend/index.html"), media_type="text/html")


# ✅ Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Something went wrong"}
    )


# ✅ Routes
app.include_router(api_router, prefix="/api/v1")
