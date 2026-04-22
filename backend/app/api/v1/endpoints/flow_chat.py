# app/api/v1/endpoints/flow_chat.py
# WhatsApp-identical flow for the web chat interface.
# Accepts a session_id (browser-side UUID) instead of phone number.

import re
import json
import time
import uuid
import hashlib
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional, Tuple

from app.core.bot_config import BOT_CONFIG
from app.services.whatsapp_flow import handle_flow, get_state
from app.services.rag_service import hybrid_search
from app.services.llm_service import stream_llama, format_rag_answer
from app.services.memory_service import get_memory, add_to_memory
from app.services.lead_service import detect_buying_signals, save_lead
from app.services.log_service import save_log
from app.db.session import SessionLocal

router = APIRouter()

CFG             = BOT_CONFIG
WEBSITE_SESSION = "swaransoft_website"
CONTACT         = f"{CFG['phone_india']} | {CFG['phone_uae']} | {CFG['email']}"

CALENDLY_LINK = "https://calendly.com/gignaati/discovery-call"
SESSION_COOKIE_KEY = "swaran_session_id"

# Direct Calendly nudge — appended after 3rd QA answer (no yes/no question)
def _meet_nudge(name: str) -> str:
    return (
        f"\n\n📅 *Want to talk to our team?*\n"
        f"Book a free 15-min discovery call: {CALENDLY_LINK}"
    )

# ── Interest regex ────────────────────────────────────────────────────────────
_INTEREST_RE = re.compile(
    r"(i('m|\s+am)\s+interested"
    r"|we\s+are\s+interested"
    r"|i\s+need\s+this"
    r"|we\s+need\s+this"
    r"|i\s+need\s+it"
    r"|we\s+need\s+it"
    r"|get\s+in\s+touch"
    r"|contact\s+you"
    r"|book\s+a\s+call"
    r"|book\s+a\s+meeting"
    r"|book\s+meeting"
    r"|book\s+now"
    r"|schedule\s+a\s+call"
    r"|schedule\s+a\s+meeting"
    r"|i\s+want\s+to\s+meet"
    r"|connect\s+with\s+team"
    r"|reach\s+out"
    r"|i\s+want\s+to\s+buy"
    r"|ready\s+to\s+start)",
    re.IGNORECASE,
)

# ── Blocked keywords ──────────────────────────────────────────────────────────
BLOCKED_KEYWORDS = [
    "cricket", "football", "sports", "movie", "film", "song", "music",
    "recipe", "cooking", "food", "weather", "news", "politics", "religion",
    "joke", "meme", "girlfriend", "boyfriend", "love", "marriage", "dating",
    "astrology", "horoscope", "lottery", "gambling", "casino", "sex",
    "president", "minister", "prime minister", "modi", "trump",
    "hacking", "porn", "actor", "actress", "bird", "malicious", "hacker",
    "amit shah", "narendre modi", "yogi", "saini", "joshi", "singh",
    "yadav", "thakur", "bollywood", "hollywood", "obama", "joe", "lunch", "masala",
    "chicken", "mutton", "alcohol", "daaru", "daru", "milk", "chai", "tea", "coffee", "animal",
    "cow", "drink", "buffallo", "light", "electricity", "tiffin", "tv", "television", "breakfast",
    "house", "hote", "road", "building", "clothes", "shoes", "chair", "bag", "table", "resturant", "cup",
    "plastic", "rubber", "notebook", "pen", "charger", "water", "rajnikant", "amitabh", "burger", "pizza",
    "chinese", "italian", "earphone", "ear", "nose", "hair", "hat", "summer", "winter", "rain", "chasma",
    "bottle", "coke", "pencil", "box", "camera", "parking", "color", "rupees", "dollar", "$", "ring", "gold", "silver",
    "diamond", "school", "dinner", "paint", "bulb", "juice", "fruit", "apple", "banana", "orange", "mango", "beers", "beer",
    "salt", "oil", "petrol", "diesel", "grapes", "kela", "shakes", "pani puri", "pani", "bell", "AC", "air conditioner",
    "toilet", "biscuit", "chocolate", "namkeen", "tissue", "male", "female", "men", "man", "gender", "calculator",
    "calculation", "umbrella", "god", "shiv", "hanuman", "bhagwan", "money", "paisa", "energy", "jim", "zim", "tatoo",
    "paps", "pops", "beared", "pant", "shirt", "elon musk", "ambani", "adani", "cm", "reliance",
    "tata", "kolkata", "mumbai", "delhi", "gujarat", "pm", "bihar", "up", "uttar pradesh",
    "chatgpt", "openai", "gemini", "copilot", "bard", "bus", "truck", "train", "airplane", "flight",
]

GUARDRAIL_MSG = (
    "That sounds interesting! However, my expertise is limited to SwaranSoft. "
    "Please ask me something related to our platform so I can give you the best information."
)

def _has_meeting_link(text: str) -> bool:
    tl = (text or "").lower()
    return ("calendly.com/" in tl) or ("calendar.google.com/" in tl)


def is_same_topic(current: str, history: list) -> bool:
    if not history:
        return True
    last = next(
        (m["content"] for m in reversed(history) if m["role"] == "user"),
        ""
    )
    if not last:
        return True
    curr_words = set(current.lower().split())
    last_words = set(last.lower().split())
    common = curr_words & last_words
    return len(common) >= 2


def _is_blocked(query: str) -> bool:
    q = query.lower()
    return any(
        re.search(r'(?<![\w])' + re.escape(kw) + r'(?![\w])', q)
        for kw in BLOCKED_KEYWORDS
    )


def _rewrite_query(query: str, history: list) -> str:
    if not history:
        return query
    last_msgs = [
        m["content"] for m in reversed(history)
        if m["role"] == "user"
    ][:2]
    combined = " ".join(reversed(last_msgs)) + " " + query
    return combined.lower()


def _is_relevant(doc: str, query: str) -> bool:
    stop = {"the", "a", "an", "is", "in", "of", "to", "and", "for", "on", "with", "me", "about", "tell"}
    q_words = set(query.lower().split()) - stop
    d_words = set(doc.lower().split())
    return len(q_words & d_words) >= 1


def _is_clean(doc: str) -> bool:
    bad_phrases = ["unsubscribe", "click here to opt out", "this email was sent"]
    return not any(p in doc.lower() for p in bad_phrases)

def _rag_fallback_answer(query: str, docs: list[str]) -> str:
    """Return a short, context-grounded fallback when LLM times out/returns empty."""
    raw = format_rag_answer(query, docs).strip()
    if not raw:
        return ""

    # Remove common bullet prefixes and keep it short/readable.
    lines = []
    for ln in raw.splitlines():
        stripped = ln.strip().lstrip(" -*").strip()
        if stripped:
            lines.append(stripped)
    if not lines:
        return ""

    summary = " ".join(lines[:2]).strip()
    return summary[:420].strip()


def _ensure_name_in_reply(reply: str, name: Optional[str]) -> str:
    text = (reply or "").strip()
    nm = (name or "").strip()
    if not text or not nm or nm.lower() == "there":
        return reply
    if nm.lower() in text.lower():
        return reply
    return f"{nm}, {text}"


# ── Request schema ────────────────────────────────────────────────────────────

class FlowChatRequest(BaseModel):
    message:    str
    session_id: Optional[str] = None


def _resolve_session_id(raw_session_id: Optional[str], request: Optional[Request] = None) -> Tuple[str, bool]:
    """
    Resolve a safe per-user session id.
    Returns (session_id, generated_now).
    """
    invalid_session_values = {
        "", "default", "web_default", "undefined", "null", "none", "nan", "-",
    }

    if raw_session_id and raw_session_id.strip():
        cleaned = raw_session_id.strip()
        if cleaned.lower() not in invalid_session_values:
            return cleaned, False

    if request is not None:
        cookie_sid = request.cookies.get(SESSION_COOKIE_KEY)
        if cookie_sid and cookie_sid.strip() and cookie_sid.strip().lower() not in invalid_session_values:
            return cookie_sid.strip(), False

        # Deterministic fallback when client doesn't send session_id/cookie.
        # Keeps the same visitor stable across requests even without cookies.
        ua = request.headers.get("user-agent", "").strip().lower()
        xfwd = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        host = request.client.host if request.client else ""
        fingerprint = f"{host}|{xfwd}|{ua}"
        if fingerprint.strip("|"):
            digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:12]
            return f"web_fp_{digest}", False

    return f"web_{uuid.uuid4().hex[:12]}", True


def _state_key(session_id: str) -> str:
    """
    Convert any web session id into a fixed 20-char key for whatsapp_users.phone.
    """
    digest = hashlib.sha1(session_id.encode("utf-8")).hexdigest()[:16]
    return f"web_{digest}"


# ── Main endpoint ─────────────────────────────────────────────────────────────

@router.post("/")
def flow_chat(req: FlowChatRequest, request: Request):
    """
    Unified chat endpoint that mirrors WhatsApp flow exactly.
    Returns plain text (not JSON-encoded string).
    """
    text       = req.message.strip()
    session_id, generated_session = _resolve_session_id(req.session_id, request)
    phone = _state_key(session_id)

    db = SessionLocal()

    # ── Detect interest FIRST (before any flow logic) ─────────────────────────
    user_interested = bool(_INTEREST_RE.search(text))

    def generate():
        try:
            # ── Step 1: Conversational flow (greeting / name / menu) ──────────
            flow_reply = handle_flow(phone, text)

            if flow_reply is not None:
                flow_state = get_state(phone)
                flow_reply = _ensure_name_in_reply(flow_reply, flow_state.get("name"))
                add_to_memory(session_id, "user",      text)
                # Append Calendly link if interest keyword detected
                if user_interested and not _has_meeting_link(flow_reply):
                    flow_reply += f"\n\n📅 Book a free 15-min call: {CALENDLY_LINK}"
                add_to_memory(session_id, "assistant", flow_reply)
                save_log(
                    db=db, session_id=session_id, query=text,
                    response=flow_reply, intent="flow",
                    username=phone, ip_address=None,
                )
                state = get_state(phone)
                if state["stage"] in ["done", "qa"] and state.get("name") and state.get("service"):
                    _auto_capture_lead(phone, session_id, state, detect_buying_signals(text), db)
                yield flow_reply
                return

            # ── Step 2: Guardrail ─────────────────────────────────────────────
            if _is_blocked(text):
                add_to_memory(session_id, "user",      text)
                add_to_memory(session_id, "assistant", GUARDRAIL_MSG)
                save_log(
                    db=db, session_id=session_id, query=text,
                    response=GUARDRAIL_MSG, intent="guardrail",
                    username=phone, ip_address=None,
                )
                yield GUARDRAIL_MSG
                return

            # ── Step 3: State info ────────────────────────────────────────────
            state   = get_state(phone)
            name    = state.get("name") or "there"
            service = state.get("service") or f"{CFG['company_name']} AI services"

            # ── Step 4: Query rewriting ───────────────────────────────────────
            history = get_memory(session_id)
            if not is_same_topic(text, history):
                print("🔄 NEW TOPIC DETECTED → RESET CONTEXT")
                history = []
            search_query = _rewrite_query(text, history)
            print("🧠 FINAL SEARCH QUERY:", search_query)

            # ── Step 5: RAG search ────────────────────────────────────────────
            docs = hybrid_search(search_query, WEBSITE_SESSION)
            if not docs:
                docs = hybrid_search(search_query, session_id)

            # ── Step 6: Filter + Rerank ───────────────────────────────────────
            filtered = [d for d in docs if _is_relevant(d, text) and _is_clean(d)]
            if not filtered:
                filtered = docs[:10]
            scored   = [(d, sum(w in d.lower() for w in text.lower().split())) for d in filtered]
            scored.sort(key=lambda x: x[1], reverse=True)
            top_docs = [d for d, _ in scored[:4]]
            context  = "".join(f"\n[Chunk {i+1}]\n{d}\n" for i, d in enumerate(top_docs))
            context  = context[:4000]
            print("[CONTEXT LENGTH]", len(context))

            # ── Step 7: No context fallback ───────────────────────────────────
            if len(context.strip()) < 50:
                msg = f"I don't have enough information on that. Contact us: {CONTACT}"
                if user_interested and not _has_meeting_link(msg):
                    msg += f"\n\n📅 Book a free 15-min call: {CALENDLY_LINK}"
                add_to_memory(session_id, "user",      text)
                add_to_memory(session_id, "assistant", msg)
                save_log(db=db, session_id=session_id, query=text,
                         response=msg, intent="fallback", username=phone, ip_address=None)
                yield msg
                return

            # ── Step 8: History block ─────────────────────────────────────────
            history_recent = get_memory(session_id)[-8:]
            history_text   = ""
            if history_recent:
                lines = []
                for m in history_recent:
                    role = "User" if m["role"] == "user" else "Bot"
                    lines.append(f"{role}: {m['content'][:200]}")
                history_text = "\n".join(lines)
            history_block = f"\nCONVERSATION SO FAR:\n{history_text}\n" if history_text else ""

            # ── Step 9: Prompt ────────────────────────────────────────────────
            prompt = (
                f"You are a strict AI assistant for {CFG['company_name']} on Web Chat.\n"
                f"User: {name} | Topic: {service}\n"
                f"{history_block}\n"
                f"RULES:\n"
                f"- Answer ONLY from the CONTEXT below.\n"
                f"- Write EXACTLY 2 sentences. Not 3, not 4. Just 2.\n"
                f"- No bullet points, no lists, no markdown.\n"
                f"- Do NOT start with 'Here is the answer:' or any preamble.\n"
                f"- If answer not in context → say only: Not found. Contact: {CONTACT}\n\n"
                f"CONTEXT:\n{context}\n\n"
                f"QUESTION: {text}\n\n"
                f"2-SENTENCE ANSWER:"
            )

            # ── Step 10: Save user message ────────────────────────────────────
            add_to_memory(session_id, "user", text)

            # ── Step 11: LLM call ─────────────────────────────────────────────
            print("\n🚀 LLM CALL START")
            t_llm = time.time()
            from app.services.llm_service import call_llama
            try:
                full_response = call_llama(prompt, timeout_s=300)
                if not full_response or len(full_response.strip()) == 0:
                    print("⚠️ LLM returned empty response (likely timeout or backend issue)")
                    rag_fallback = _rag_fallback_answer(text, top_docs)
                    full_response = rag_fallback or f"I don't have that info right now. Contact us: {CONTACT}"
                else:
                    print("✅ LLM RESPONSE RECEIVED")
            except Exception as e:
                print("❌ LLM ERROR:", e)
                rag_fallback = _rag_fallback_answer(text, top_docs)
                full_response = rag_fallback or f"I don't have that info right now. Contact us: {CONTACT}"
            print(f"[LLM TIME] {round((time.time() - t_llm) * 1000, 2)} ms")

            # ── Step 12: Strip JSON wrapper ───────────────────────────────────
            try:
                parsed = json.loads(full_response.strip())
                if isinstance(parsed, dict) and "response" in parsed:
                    full_response = parsed["response"]
            except Exception:
                pass
            json_match = re.search(r'\{\s*"response"\s*:\s*"(.*?)"\s*\}', full_response, re.DOTALL)
            if json_match:
                full_response = json_match.group(1)

            # ── Step 13: Strip preamble ───────────────────────────────────────
            full_response = re.sub(
                r'^(here\s+is\s+(the|my|an)?\s*answer\s*:|answer\s*:|response\s*:|'
                r'sure[,!]?\s*here\s+is\s*:|certainly!?|of\s+course!?|'
                r'great\s+question!?|sure[,!])\s*',
                '', full_response.strip(), flags=re.IGNORECASE
            ).strip()

            if not full_response.strip():
                full_response = f"I don't have that info right now. Contact us: {CONTACT}"

            # ── Step 14: Interest → Calendly link ────────────────────────────
            if user_interested and not _has_meeting_link(full_response):
                full_response += f"\n\n📅 Want to know more? Book a free 15-min call: {CALENDLY_LINK}"

            # ── Step 15: After 3rd QA answer → direct Calendly nudge (no yes/no) ──
            state = get_state(phone)
            if state.get("append_meet_link") and not _has_meeting_link(full_response):
                full_response += _meet_nudge(state.get("name") or "there")
                state["append_meet_link"] = False
            full_response = _ensure_name_in_reply(full_response, state.get("name"))
                

            # ── Step 16: Save + yield ─────────────────────────────────────────
            add_to_memory(session_id, "assistant", full_response)
            save_log(db=db, session_id=session_id, query=text,
                     response=full_response, intent="answer", username=phone, ip_address=None)
            yield full_response

        except Exception as e:
            print(f"[flow_chat ERROR] {e}")
            yield f"Something went wrong. Please try again or contact us: {CONTACT}"
        finally:
            db.close()

    response_text = ""
    for chunk in generate():
        response_text += chunk
    response = PlainTextResponse(content=response_text)
    if generated_session:
        response.set_cookie(
            key=SESSION_COOKIE_KEY,
            value=session_id,
            max_age=60 * 60 * 24 * 365,
            httponly=False,
            samesite="lax",
            path="/",
        )
    return response


# ── Lead capture helper ───────────────────────────────────────────────────────

def _auto_capture_lead(phone: str, session_id: str, state: dict, signals: list, db):
    try:
        transcript = get_memory(session_id)
        save_lead(
            name            = state.get("name", ""),
            email           = "",
            company         = "",
            role            = "",
            industry        = "",
            phone           = phone,
            chat_transcript = transcript,
            buying_signals  = signals + ([state["service"]] if state.get("service") else []),
            session_id      = session_id,
        )
    except Exception as e:
        print("❌ AUTO LEAD CAPTURE ERROR:", e)
