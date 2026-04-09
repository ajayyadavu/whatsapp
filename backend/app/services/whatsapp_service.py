# app/services/whatsapp_service.py
# NEW FILE — handles sending messages back via WhatsApp Cloud API

import httpx
from app.core.config import settings

def send_whatsapp_message(to: str, message: str):
    """
    Send a text message to a WhatsApp number via Meta Cloud API.
    'to' must be in international format e.g. 919220313650
    """
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_ID:
        print("WhatsApp not configured — skipping send.")
        return

    url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        res = httpx.post(url, json=payload, headers=headers, timeout=10)
        res.raise_for_status()
        print(f"✅ WhatsApp message sent to {to}")
    except Exception as e:
        print(f"WhatsApp send error: {e}")
