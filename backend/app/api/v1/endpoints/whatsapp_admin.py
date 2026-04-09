# app/api/v1/endpoints/whatsapp_admin.py
# Admin endpoints for WhatsApp user management
# Register / lookup / list users stored in whatsapp_users table

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.whatsapp_user_service import get_name, save_name, name_known
from app.db.session import SessionLocal
from app.models.whatsapp_user import WhatsAppUser

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    phone: str    # international format, digits only e.g. "919220313650"
    name:  str    # e.g. "Ajay Kumar"

class RegisterResponse(BaseModel):
    success: bool
    message: str
    phone:   str
    name:    str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse)
def register_user(req: RegisterRequest):
    """
    Pre-register a WhatsApp number + name in the DB.
    When this person messages the bot, they will be greeted by name
    and skip the name-capture step entirely.

    Phone must be in international format WITHOUT '+' or spaces:
      India example : 919220313650   (91 + 10-digit mobile)
      UAE example   : 971509292650   (971 + 9-digit mobile)
    """
    phone = req.phone.strip().replace("+", "").replace(" ", "").replace("-", "")
    name  = req.name.strip().title()

    if not phone.isdigit():
        raise HTTPException(status_code=400, detail="Phone must contain digits only (no +, spaces, or dashes).")
    if len(phone) < 10 or len(phone) > 15:
        raise HTTPException(status_code=400, detail="Phone length must be 10–15 digits.")
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty.")

    already_existed = name_known(phone)
    save_name(phone, name)   # upsert — safe to call multiple times

    msg = (
        f"Updated existing record for {phone}."
        if already_existed
        else f"Registered new user {phone}."
    )

    return RegisterResponse(success=True, message=msg, phone=phone, name=name)


@router.get("/lookup/{phone}")
def lookup_user(phone: str):
    """
    Check if a phone number is already registered and what name is stored.
    """
    phone = phone.strip().replace("+", "").replace(" ", "")
    name  = get_name(phone)

    if name:
        return {"registered": True, "phone": phone, "name": name}
    return {"registered": False, "phone": phone, "name": None}


@router.get("/users")
def list_users(limit: int = 50, offset: int = 0):
    """
    List all registered WhatsApp users (paginated).
    Default: first 50 users.
    """
    db = SessionLocal()
    try:
        total = db.query(WhatsAppUser).count()
        rows  = (
            db.query(WhatsAppUser)
            .order_by(WhatsAppUser.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        users = [
            {
                "phone":      r.phone,
                "name":       r.name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
        return {"total": total, "offset": offset, "limit": limit, "users": users}
    finally:
        db.close()


@router.delete("/users/{phone}")
def delete_user(phone: str):
    """
    Remove a WhatsApp user from the DB.
    Next message from this number will ask for their name again.
    """
    phone = phone.strip().replace("+", "").replace(" ", "")
    db    = SessionLocal()
    try:
        row = db.query(WhatsAppUser).filter(WhatsAppUser.phone == phone).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Phone {phone} not found.")
        db.delete(row)
        db.commit()
        return {"success": True, "message": f"Deleted {phone} ({row.name}) from registry."}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
