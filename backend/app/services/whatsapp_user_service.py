# app/services/whatsapp_user_service.py
# Handles persistent read/write of WhatsApp user names in PostgreSQL.
# In-memory cache layer on top so DB is not hit on every message.

from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.whatsapp_user import WhatsAppUser

# ── In-memory cache (phone → name) ────────────────────────────────────────────
# Populated on first lookup, so repeated messages never hit the DB.
_name_cache: dict[str, str] = {}


def _get_db() -> Session:
    return SessionLocal()


# ── Public API ─────────────────────────────────────────────────────────────────

def get_name(phone: str) -> Optional[str]:
    """
    Return the stored name for this phone number, or None if unknown.
    Checks in-memory cache first; falls back to PostgreSQL.
    """
    if phone in _name_cache:
        return _name_cache[phone]

    db = _get_db()
    try:
        row = db.query(WhatsAppUser).filter(WhatsAppUser.phone == phone).first()
        if row:
            _name_cache[phone] = row.name   # warm the cache
            return row.name
        return None
    except Exception as e:
        print(f"[WA_USER_SERVICE] get_name error: {e}")
        return None
    finally:
        db.close()


def save_name(phone: str, name: str) -> None:
    """
    Persist the user's name permanently in PostgreSQL.
    Updates the record if the phone already exists (upsert).
    Also updates the in-memory cache immediately.
    """
    _name_cache[phone] = name   # update cache instantly

    db = _get_db()
    try:
        row = db.query(WhatsAppUser).filter(WhatsAppUser.phone == phone).first()
        if row:
            row.name = name     # update existing
        else:
            row = WhatsAppUser(phone=phone, name=name)
            db.add(row)         # insert new
        db.commit()
        print(f"[WA_USER_SERVICE] ✅ Saved name '{name}' for phone {phone}")
    except Exception as e:
        db.rollback()
        print(f"[WA_USER_SERVICE] save_name error: {e}")
    finally:
        db.close()


def name_known(phone: str) -> bool:
    """Returns True if we have a stored name for this phone."""
    return get_name(phone) is not None
