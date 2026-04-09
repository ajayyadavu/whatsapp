# app/services/log_service.py
# Saves and retrieves chat logs from the database.

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.chat_log import ChatLog


def save_log(
    db: Session,
    session_id: str,
    query: str,
    response: str,
    intent: str,
    username: str = None,
    ip_address: str = None,
) -> ChatLog:
    """Insert one chat log row. Silently swallows errors so it never breaks chat."""
    try:
        log = ChatLog(
            session_id = session_id,
            username   = username,
            ip_address = ip_address,
            query      = query[:4000],       # guard against huge inputs
            response   = response[:8000],    # guard against huge responses
            intent     = intent,
            timestamp  = datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except Exception as e:
        db.rollback()
        print(f"[LOG ERROR] {e}")
        return None


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    session_id: str = None,
    username: str = None,
) -> list[ChatLog]:
    """Retrieve logs with optional filters, newest first."""
    q = db.query(ChatLog)
    if session_id:
        q = q.filter(ChatLog.session_id == session_id)
    if username:
        q = q.filter(ChatLog.username == username)
    return q.order_by(ChatLog.timestamp.desc()).offset(skip).limit(limit).all()
