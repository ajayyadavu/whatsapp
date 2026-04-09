# app/models/chat_log.py
# Stores every user query + bot response for audit and analytics.

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db.base_class import Base


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(120), index=True, nullable=False)
    username   = Column(String(120), nullable=True)   # from auth token if present
    ip_address = Column(String(60),  nullable=True)
    query      = Column(Text,        nullable=False)
    response   = Column(Text,        nullable=True)    # filled after streaming ends
    intent     = Column(String(60),  nullable=True)    # e.g. "greeting", "rag", "meet"
    timestamp  = Column(DateTime,    default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (
            f"<ChatLog id={self.id} session={self.session_id!r} "
            f"intent={self.intent!r} ts={self.timestamp}>"
        )
