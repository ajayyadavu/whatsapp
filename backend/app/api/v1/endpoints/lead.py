# app/api/v1/endpoints/lead.py
# NEW FILE — add this to your existing endpoints folder

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.lead_service import save_lead
from app.services.memory_service import get_memory

router = APIRouter()


class LeadRequest(BaseModel):
    name:            str
    email:           str
    company:         str
    role:            Optional[str] = ""
    industry:        str
    phone:           Optional[str] = ""
    session_id:      str
    buying_signals:  Optional[list[str]] = []
    utm_source:      Optional[str] = ""
    utm_medium:      Optional[str] = ""
    utm_campaign:    Optional[str] = ""


@router.post("/")
def capture_lead(req: LeadRequest):
    transcript = get_memory(req.session_id)

    lead = save_lead(
        name            = req.name,
        email           = req.email,
        company         = req.company,
        role            = req.role,
        industry        = req.industry,
        phone           = req.phone,
        chat_transcript = transcript,
        buying_signals  = req.buying_signals,
        session_id      = req.session_id,
        utm_source      = req.utm_source,
        utm_medium      = req.utm_medium,
        utm_campaign    = req.utm_campaign,
    )

    return {
        "success":  True,
        "lead_id":  lead["id"],
        "message":  "Thank you! Our team will reach out within 24 hours."
    }
