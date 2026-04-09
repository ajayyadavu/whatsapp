# app/services/memory_service.py
# State aur memory ab SQLite DB mein store hoti hai — JSON files nahi.
# Session filter: naya question aane par purani session delete hoti hai,
# nayi session_id se fresh session banti hai.

from datetime import datetime
from sqlalchemy.orm import Session as DBSession

from app.db.session import SessionLocal
from app.models.chat_session import ChatSession


def _get_or_create(session_id: str, db: DBSession = None):
    """Returns (ChatSession, db, own_db). Caller must close db if own_db=True."""
    _own_db = db is None
    if _own_db:
        db = SessionLocal()
    row = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not row:
        row = ChatSession(session_id=session_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row, db, _own_db


def _save(row: ChatSession, db: DBSession):
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)


# ─────────────────────────────────────────────
# SESSION FILTER: naya question = purani delete, nayi banao
# ─────────────────────────────────────────────

def reset_session(session_id: str) -> None:
    db = SessionLocal()
    try:
        old = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if old:
            db.delete(old)
            db.commit()
        new_row = ChatSession(session_id=session_id)
        db.add(new_row)
        db.commit()
    except Exception as e:
        print(f"[RESET SESSION ERROR] {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────
# Getters
# ─────────────────────────────────────────────

def get_user_name(session_id: str):
    row, db, own = _get_or_create(session_id)
    val = row.user_name
    if own: db.close()
    return val

def has_greeted(session_id: str) -> bool:
    row, db, own = _get_or_create(session_id)
    val = row.greeted
    if own: db.close()
    return val

def name_asked(session_id: str) -> bool:
    row, db, own = _get_or_create(session_id)
    val = row.name_asked
    if own: db.close()
    return val

def services_shown(session_id: str) -> bool:
    row, db, own = _get_or_create(session_id)
    val = row.services_shown
    if own: db.close()
    return val

def get_name_attempts(session_id: str) -> int:
    row, db, own = _get_or_create(session_id)
    val = row.name_attempts
    if own: db.close()
    return val

def is_name_abandoned(session_id: str) -> bool:
    row, db, own = _get_or_create(session_id)
    val = row.name_abandoned
    if own: db.close()
    return val

def get_chat_count(session_id: str) -> int:
    row, db, own = _get_or_create(session_id)
    val = row.chat_count
    if own: db.close()
    return val


# ─────────────────────────────────────────────
# Setters
# ─────────────────────────────────────────────

def set_user_name(session_id: str, name: str) -> None:
    row, db, own = _get_or_create(session_id)
    row.user_name = name
    _save(row, db)
    if own: db.close()

def mark_greeted(session_id: str) -> None:
    row, db, own = _get_or_create(session_id)
    row.greeted = True
    _save(row, db)
    if own: db.close()

def mark_name_asked(session_id: str) -> None:
    row, db, own = _get_or_create(session_id)
    row.name_asked = True
    _save(row, db)
    if own: db.close()

def mark_services_shown(session_id: str) -> None:
    row, db, own = _get_or_create(session_id)
    row.services_shown = True
    _save(row, db)
    if own: db.close()

def increment_name_attempts(session_id: str) -> int:
    row, db, own = _get_or_create(session_id)
    row.name_attempts += 1
    _save(row, db)
    val = row.name_attempts
    if own: db.close()
    return val

def abandon_name_collection(session_id: str) -> None:
    row, db, own = _get_or_create(session_id)
    row.name_abandoned = True
    _save(row, db)
    if own: db.close()

def increment_chat_count(session_id: str) -> int:
    row, db, own = _get_or_create(session_id)
    row.chat_count += 1
    _save(row, db)
    val = row.chat_count
    if own: db.close()
    return val


# ─────────────────────────────────────────────
# Memory
# ─────────────────────────────────────────────

def get_memory(session_id: str) -> list:
    row, db, own = _get_or_create(session_id)
    mem = row.get_memory()
    if own: db.close()
    return mem

def add_to_memory(session_id: str, role: str, message: str) -> None:
    row, db, own = _get_or_create(session_id)
    messages = row.get_memory()
    messages.append({"role": role, "content": message})
    row.set_memory(messages)
    _save(row, db)
    if own: db.close()
