# app/services/lead_service.py
# NEW FILE — add this to your existing project

# from supabase import create_client
# import httpx
# from datetime import datetime
# import uuid
# from app.core.config import settings

# supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# # Buying signal keywords (architecture doc Section 3.1)
# BUYING_SIGNALS = {
#     "pricing":     ["cost", "price", "₹", "lakh", "budget", "how much", "roi"],
#     "demo":        ["pilot", "demo", "poc", "trial", "proof of concept"],
#     "timeline":    ["when", "timeline", "how long", "start", "launch"],
#     "integration": ["whatsapp", "teams", "crm", "integrate", "connect"],
#     "decision":    ["next steps", "contact", "speak", "meeting", "call"],
# }

# def detect_buying_signals(message: str) -> list[str]:
#     message_lower = message.lower()
#     return [
#         category for category, keywords in BUYING_SIGNALS.items()
#         if any(kw in message_lower for kw in keywords)
#     ]

# def save_lead(
#     name: str,
#     email: str,
#     company: str,
#     role: str,
#     industry: str,
#     phone: str,
#     chat_transcript: list,
#     buying_signals: list[str],
#     session_id: str,
#     utm_source: str = "",
#     utm_medium: str = "",
#     utm_campaign: str = "",
# ) -> dict:
#     lead_id   = str(uuid.uuid4())
#     lead_data = {
#         "id":               lead_id,
#         "name":             name,
#         "email":            email,
#         "company":          company,
#         "role":             role,
#         "industry":         industry,
#         "phone":            phone,
#         "chat_transcript":  chat_transcript,
#         "buying_signals":   buying_signals,
#         "session_id":       session_id,
#         "utm_source":       utm_source,
#         "utm_medium":       utm_medium,
#         "utm_campaign":     utm_campaign,
#         "status":           "new",
#         "created_at":       datetime.utcnow().isoformat(),
#     }

#     # Save to Supabase
#     try:
#         supabase.table("chat_leads").insert(lead_data).execute()
#         print(f"Lead saved: {lead_id}")
#     except Exception as e:
#         print(f"Supabase lead save error: {e}")

#     # Fire n8n webhook → Zoho CRM + Slack + Gmail
#     try:
#         httpx.post(settings.N8N_LEAD_WEBHOOK_URL, json=lead_data, timeout=10)
#         print(f"n8n webhook triggered for lead: {lead_id}")
#     except Exception as e:
#         print(f"n8n webhook error (non-fatal): {e}")

#     return lead_data


# app/services/lead_service.py

import httpx
from datetime import datetime
import uuid
from app.core.config import settings

supabase = None
if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    from supabase import create_client
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    print("Supabase client initialized.")
else:
    print("WARNING: SUPABASE_URL/KEY not set.")

BUYING_SIGNALS = {
    "pricing":     ["cost", "price", "₹", "lakh", "budget", "how much", "roi"],
    "demo":        ["pilot", "demo", "poc", "trial", "proof of concept"],
    "timeline":    ["when", "timeline", "how long", "start", "launch"],
    "integration": ["whatsapp", "teams", "crm", "integrate", "connect"],
    "decision":    ["next steps", "contact", "speak", "meeting", "call"],
}

def detect_buying_signals(message: str) -> list[str]:
    message_lower = message.lower()
    return [
        category for category, keywords in BUYING_SIGNALS.items()
        if any(kw in message_lower for kw in keywords)
    ]

def save_lead(
    name: str, email: str, company: str, role: str,
    industry: str, phone: str, chat_transcript: list,
    buying_signals: list[str], session_id: str,
    utm_source: str = "", utm_medium: str = "", utm_campaign: str = "",
) -> dict:
    lead_id   = str(uuid.uuid4())
    lead_data = {
        "id": lead_id, "name": name, "email": email,
        "company": company, "role": role, "industry": industry,
        "phone": phone, "chat_transcript": chat_transcript,
        "buying_signals": buying_signals, "session_id": session_id,
        "utm_source": utm_source, "utm_medium": utm_medium,
        "utm_campaign": utm_campaign, "status": "new",
        "created_at": datetime.utcnow().isoformat(),
    }

    if supabase:
        try:
            supabase.table("chat_leads").insert(lead_data).execute()
            print(f"✅ Lead saved to Supabase: {lead_id}")
        except Exception as e:
            print(f"Supabase lead save error: {e}")
    else:
        print(f"Lead captured (Supabase not configured): {lead_data}")

    # Only fire n8n if it's a real HTTP URL
    webhook = settings.N8N_LEAD_WEBHOOK_URL
    if webhook and webhook.startswith("http"):
        try:
            httpx.post(webhook, json=lead_data, timeout=10)
            print(f"✅ n8n webhook triggered: {lead_id}")
        except Exception as e:
            print(f"n8n webhook error (non-fatal): {e}")
    else:
        print("n8n webhook not configured — skipping.")

    return lead_data
