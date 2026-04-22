# app/services/whatsapp_service.py
# NEW FILE — handles sending messages back via WhatsApp Cloud API

import json
import httpx
from app.core.config import settings

def _normalize_message_text(message: str) -> str:
    """Convert accidentally JSON-encoded text into plain WhatsApp text."""
    if message is None:
        return ""

    text = str(message).strip()

    # Handle text wrapped as JSON string, e.g. "\"Hi\\n\\nWelcome\""
    for _ in range(2):
        if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
            try:
                parsed = json.loads(text)
                if isinstance(parsed, str):
                    text = parsed.strip()
                    continue
            except Exception:
                pass
        break

    # Fallback cleanup if escapes still remain.
    if "\\n" in text and "\n" not in text:
        text = text.replace("\\n", "\n")
    if "\\t" in text and "\t" not in text:
        text = text.replace("\\t", "\t")
    if '\\"' in text:
        text = text.replace('\\"', '"')

    return text

def send_whatsapp_message(to: str, message: str):
    """
    Send a text message to a WhatsApp number via Meta Cloud API.
    'to' must be in international format e.g. 919220313650
    """
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_ID:
        print("WhatsApp not configured — skipping send.")
        return

    url = f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_ID}/messages"

    body = _normalize_message_text(message)

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
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
