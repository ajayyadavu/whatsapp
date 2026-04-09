# app/models/chat_session.py
# Tracks per-session state and conversation memory in the database.
# Replaces the JSON-file approach (session_state.json / session_memory.json).

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from datetime import datetime
import json

from app.db.base_class import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id     = Column(String(120), unique=True, index=True, nullable=False)

    # ── State flags ──────────────────────────────────────────────────────────
    greeted        = Column(Boolean, default=False, nullable=False)
    name_asked     = Column(Boolean, default=False, nullable=False)
    name_abandoned = Column(Boolean, default=False, nullable=False)
    name_attempts  = Column(Integer, default=0,     nullable=False)
    services_shown = Column(Boolean, default=False, nullable=False)
    user_name      = Column(String(120), nullable=True)
    chat_count     = Column(Integer, default=0,     nullable=False)

    # ── Conversation memory (stored as JSON array) ───────────────────────────
    memory_json    = Column(Text, default="[]", nullable=False)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at     = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at     = Column(DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow, nullable=False)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def get_memory(self) -> list:
        try:
            return json.loads(self.memory_json or "[]")
        except Exception:
            return []

    def set_memory(self, messages: list) -> None:
        self.memory_json = json.dumps(messages[-20:], ensure_ascii=False)

    def __repr__(self):
        return (
            f"<ChatSession id={self.id} session_id={self.session_id!r} "
            f"user_name={self.user_name!r} chat_count={self.chat_count}>"
        )
