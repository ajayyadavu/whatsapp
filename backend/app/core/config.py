from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
from app.core.bot_config import BOT_CONFIG

load_dotenv()


class Settings(BaseSettings):

    BASE_URL: str = "http://localhost:8000"

    # ── Ollama ────────────────────────────────────────────────
    OLLAMA_URL: str = "http://localhost:11434/api/generate"
    OLLAMA_API_KEY: Optional[str] = None

    # ── LLM Model (change here to switch models) ──────────────
    LLM_MODEL: str = "llama3"

    # ── PostgreSQL ────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/workbench"

    # ── JWT ───────────────────────────────────────────────────
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Supabase ──────────────────────────────────────────────
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    N8N_LEAD_WEBHOOK_URL: Optional[str] = None

    # ── WhatsApp ──────────────────────────────────────────────
    WHATSAPP_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_ID: Optional[str] = None
    # Default comes from bot_config — override in .env if needed
    WHATSAPP_VERIFY_TOKEN: str = BOT_CONFIG["whatsapp_verify_token"]
    

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
