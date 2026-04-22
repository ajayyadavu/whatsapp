# app/api/v1/endpoints/whatsapp.py
# CRITICAL: Meta webhook must get HTTP 200 within 5s.
# All LLM/RAG work runs in a background thread after instant ACK.

import time
import re
import json
import threading
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse

from app.core.bot_config import BOT_CONFIG
from app.services.rag_service import hybrid_search
from app.services.llm_service import stream_llama, format_rag_answer
from app.services.memory_service import get_memory, add_to_memory
from app.services.lead_service import detect_buying_signals, save_lead
from app.services.log_service import save_log
from app.services.whatsapp_service import send_whatsapp_message
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.whatsapp_flow import handle_flow, get_state

router = APIRouter()

CFG             = BOT_CONFIG
WEBSITE_SESSION = "swaransoft_website"
CONTACT         = f"{CFG['phone_india']} | {CFG['phone_uae']} | {CFG['email']}"
CONTACT_WEB     = f"{CFG['website']} | {CFG['email']}"
CALENDLY_LINK   = "https://calendly.com/gignaati/discovery-call"

# ══════════════════════════════════════════════════════════════════════════════
# ── Interest / buying-intent regex (same as chat.py) ─────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
# NOTE: Only strong buying-intent — generic info phrases like "tell me more", "know more"
# are normal questions and should NOT trigger the meet link.
_INTEREST_RE = re.compile(
    r"(i('m|\s+am)\s+interested"
    r"|we\s+are\s+interested"
    r"|i\s+need\s+this"
    r"|we\s+need\s+this"
    r"|i\s+need\s+it"
    r"|we\s+need\s+it"
    r"|get\s+in\s+touch"
    r"|contact\s+you"
    r"|book\s+a\s+meeting"
    r"|book\s+meeting"
    r"|schedule\s+a\s+meeting"
    r"|reach\s+out"
    r"|i\s+want\s+to\s+buy"
    r"|i\s+want\s+to\s+purchase"
    r"|ready\s+to\s+start)",
    re.IGNORECASE,
)

# ── Google Calendar meet link builder (same as chat.py) ──────────────────────
def _build_calendar_link() -> str:
    tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=4, minute=30, second=0, microsecond=0
    )
    end = tomorrow + timedelta(minutes=15)
    fmt = "%Y%m%dT%H%M%SZ"
    params = {
        "action":  "TEMPLATE",
        "text":    f"Discovery Call with {CFG['company_name']}",
        "details": f"15-minute discovery call with {CFG['company_name']}.\nContact: {CONTACT_WEB}",
        "dates":   f"{tomorrow.strftime(fmt)}/{end.strftime(fmt)}",
        "add":     CFG["email"],
        "sf":      "true",
        "output":  "xml",
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params)

MEET_FOOTER_TEMPLATE = (
    "\n\n📅 Want to know more? Book a free 15-min call with our team: {calendar_link}"
)


def _meet_nudge(name: str) -> str:
    return (
        f"\n\n📅 *Want to talk to our team?*\n"
        f"Book a free 15-min discovery call: {CALENDLY_LINK}"
    )

# ══════════════════════════════════════════════════════════════════════════════
# ── Guardrail: blocked off-topic keywords (same as chat.py) ──────────────────
# ══════════════════════════════════════════════════════════════════════════════
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

def _is_blocked(query: str) -> bool:
    q = query.lower()
    return any(
        re.search(r'(?<![\w])' + re.escape(kw) + r'(?![\w])', q)
        for kw in BLOCKED_KEYWORDS
    )


def _has_meeting_link(text: str) -> bool:
    tl = (text or "").lower()
    return ("calendly.com/" in tl) or ("calendar.google.com/" in tl)

# ══════════════════════════════════════════════════════════════════════════════
# ── RAG helpers (same as chat.py) ────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _rewrite_query(query: str, history: list) -> str:
    """Expand vague short queries using last user message."""
    if len(query.split()) <= 3 and history:
        last = next(
            (m["content"] for m in reversed(history) if m["role"] == "user"),
            ""
        )
        if last and last != query:
            return f"{last} {query}"
    return query


def _is_relevant(doc: str, query: str) -> bool:
    """Relaxed relevance — at least 1 meaningful word overlap."""
    stop = {"the", "a", "an", "is", "in", "of", "to", "and", "for", "on", "with", "me", "about", "tell"}
    q_words = set(query.lower().split()) - stop
    d_words = set(doc.lower().split())
    return len(q_words & d_words) >= 1


def _is_clean(doc: str) -> bool:
    """Only filter truly junk/spam content — not business info."""
    bad_phrases = ["unsubscribe", "click here to opt out", "this email was sent"]
    return not any(p in doc.lower() for p in bad_phrases)


def _ensure_name_in_reply(reply: str, name: str | None) -> str:
    text = (reply or "").strip()
    nm = (name or "").strip()
    if not text or not nm or nm.lower() == "there":
        return reply
    if nm.lower() in text.lower():
        return reply
    return f"*{nm}*, {text}"


# ══════════════════════════════════════════════════════════════════════════════
# ── Webhook GET — Meta verification ──────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/")
def verify_webhook(
    hub_mode:         str = Query(None, alias="hub.mode"),
    hub_challenge:    str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        print("WhatsApp webhook verified.")
        return PlainTextResponse(content=hub_challenge)
    return PlainTextResponse(content="Forbidden", status_code=403)


# ══════════════════════════════════════════════════════════════════════════════
# ── Webhook POST — incoming messages ─────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/")
async def receive_message(request: Request):
    """Instantly ACK to Meta, then process in background thread."""
    body = await request.json()

    try:
        entry   = body["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        if "messages" not in value:
            return {"status": "ignored"}

        msg = value["messages"][0]

        if msg.get("type") != "text":
            return {"status": "ignored"}

        from_no = msg["from"]
        text    = msg["text"]["body"].strip()

        print(f"WhatsApp from {from_no}: {text}")

        threading.Thread(
            target=_process_message,
            args=(from_no, text),
            daemon=True,
        ).start()

    except Exception as e:
        print(f"WhatsApp webhook parse error: {e}")

    return {"status": "ok"}


# ══════════════════════════════════════════════════════════════════════════════
# ── Background processor ──────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# def _process_message(from_no: str, text: str):
#     session_id = f"wa_{from_no}"
#     db = SessionLocal()
#     _t0 = time.time()
#     print(f"\n{'='*50}")
#     print(f"[LATENCY START] query={text!r}")

#     try:
#         # ── Step 1: Conversational flow (greeting / name / menu) ──────────────
#         flow_reply = handle_flow(from_no, text)

#         if flow_reply is not None:
#             send_whatsapp_message(from_no, flow_reply)
#             add_to_memory(session_id, "user",      text)
#             add_to_memory(session_id, "assistant", flow_reply)
#             save_log(
#                 db=db, session_id=session_id, query=text,
#                 response=flow_reply, intent="flow",
#                 username=from_no, ip_address=None,
#             )
#             state = get_state(from_no)
#             if state["stage"] in ["done", "qa"] and state.get("name") and state.get("service"):
#                 _auto_capture_lead(from_no, session_id, state, detect_buying_signals(text), db)
#             return

#         # ── Step 2: Guardrail — block off-topic questions (same as chat.py) ───
#         if _is_blocked(text):
#             print(f"[GUARDRAIL BLOCKED] {text!r}")
#             guardrail_reply = _ensure_name_in_reply(GUARDRAIL_MSG, get_state(from_no).get("name"))
#             send_whatsapp_message(from_no, guardrail_reply)
#             add_to_memory(session_id, "user",      text)
#             add_to_memory(session_id, "assistant", GUARDRAIL_MSG)
#             save_log(
#                 db=db, session_id=session_id, query=text,
#                 response=GUARDRAIL_MSG, intent="guardrail",
#                 username=from_no, ip_address=None,
#             )
#             return

#         # ── Step 3: Interest detection → Google Calendar Meet link (chat.py logic)
#         user_interested = bool(_INTEREST_RE.search(text))
#         append_meet     = user_interested
#         print(f"[INTEREST] {user_interested}  query={text!r}")

#         # ── Step 4: State info ────────────────────────────────────────────────
#         state   = get_state(from_no)
#         name    = state.get("name") or "there"
#         service = state.get("service") or f"{CFG['company_name']} AI services"

#         # ── Step 5: Query rewriting (same as chat.py) ─────────────────────────
#         history      = get_memory(session_id)
#         search_query = _rewrite_query(text, history).lower()
#         print(f"[SMART QUERY] {search_query!r}")

#         # ── Step 6: RAG search ────────────────────────────────────────────────
#         docs = hybrid_search(search_query, WEBSITE_SESSION)
#         if not docs:
#             docs = hybrid_search(search_query, session_id)
#         print(f"[RAG] got {len(docs)} docs")

#         # ── Step 7: Filter + Rerank ────────────────────────────────────────────
#         filtered = [d for d in docs if _is_relevant(d, text) and _is_clean(d)]
#         if not filtered:
#             filtered = docs  # fallback: use all docs, don't drop everything

#         stop = {"the", "a", "an", "is", "in", "of", "to", "and", "for", "on", "with", "me", "about", "tell"}
#         q_words = set(text.lower().split()) - stop
#         scored   = [(d, sum(w in d.lower() for w in q_words)) for d in filtered]
#         scored.sort(key=lambda x: x[1], reverse=True)
#         top_docs = [d for d, _ in scored[:5]]

#         context = "".join(f"\n[Chunk {i+1}]\n{d}\n" for i, d in enumerate(top_docs))
#         print(f"[CONTEXT] {len(context)} chars")

#         # ── Step 8: No context fallback ───────────────────────────────────────
#         if len(context.strip()) < 30:
#             msg = f"I don't have enough information on that. Contact us: {CONTACT}"
#             if append_meet:
#                 msg += MEET_FOOTER_TEMPLATE.format(calendar_link=_build_calendar_link())
#             add_to_memory(session_id, "user",      text)
#             add_to_memory(session_id, "assistant", msg)
#             send_whatsapp_message(from_no, msg)
#             save_log(
#                 db=db, session_id=session_id, query=text,
#                 response=msg, intent="fallback",
#                 username=from_no, ip_address=None,
#             )
#             return

#         # ── Step 9: Build conversation history block ───────────────────────────
#         history_recent = get_memory(session_id)[-8:]
#         history_text   = ""
#         if history_recent:
#             lines = []
#             for m in history_recent:
#                 role = "User" if m["role"] == "user" else "Bot"
#                 lines.append(f"{role}: {m['content'][:200]}")
#             history_text = "\n".join(lines)
#         history_block = f"\nCONVERSATION SO FAR:\n{history_text}\n" if history_text else ""

#         # ── Step 10: Build prompt (strict 2-sentence, same as chat.py) ────────
#         prompt = (
#             f"You are a strict AI assistant for {CFG['company_name']} on WhatsApp.\n"
#             f"User: {name} | Topic: {service}\n"
#             f"{history_block}\n"
#             f"RULES:\n"
#             f"- Answer ONLY from the CONTEXT below.\n"
#             f"- Write EXACTLY 2 sentences. Not 3, not 4. Just 2.\n"
#             f"- No bullet points, no lists, no markdown.\n"
#             f"- Do NOT start with 'Here is the answer:' or any preamble.\n"
#             f"- If you include any URL, keep it on a single line with no spaces inside it.\n"
#             f"- If answer not in context → say only: Not found. Contact: {CONTACT}\n\n"
#             f"CONTEXT:\n{context}\n\n"
#             f"QUESTION: {text}\n\n"
#             f"2-SENTENCE ANSWER:"
#         )
#         print("MODE: RAG answer")

#         # ── Step 11: Save user message ─────────────────────────────────────────
#         add_to_memory(session_id, "user", text)

#         # ── Step 12: LLM call ─────────────────────────────────────────────────
#         full_response = ""
#         for chunk in stream_llama(prompt):
#             if chunk in ("[LLM_UNAVAILABLE]", "[LLM_TIMEOUT]", "[LLM_ERROR]"):
#                 full_response = format_rag_answer(text, top_docs) if top_docs else ""
#                 if not full_response:
#                     full_response = f"I don't have that detail right now. Contact us: {CONTACT}"
#                 break
#             full_response += chunk

#         # ── Step 13: Strip JSON wrapper if LLM returned JSON ──────────────────
#         try:
#             parsed = json.loads(full_response.strip())
#             if isinstance(parsed, dict) and "response" in parsed:
#                 full_response = parsed["response"]
#         except Exception:
#             pass
#         json_match = re.search(r'\{\s*"response"\s*:\s*"(.*?)"\s*\}', full_response, re.DOTALL)
#         if json_match:
#             full_response = json_match.group(1)

#         # ── Step 14: Strip LLM preamble phrases ───────────────────────────────
#         full_response = re.sub(
#             r'^(here\s+is\s+(the|my|an)?\s*answer\s*:|answer\s*:|response\s*:|'
#             r'sure[,!]?\s*here\s+is\s*:|certainly!?|of\s+course!?|'
#             r'great\s+question!?|sure[,!])\s*',
#             '', full_response.strip(), flags=re.IGNORECASE
#         ).strip()

#         if not full_response.strip():
#             full_response = f"I don't have that info right now. Contact us: {CONTACT}"

#         # ── Step 15: Append Google Calendar Meet link if user is interested ────
#         if append_meet:
#             calendar_link = _build_calendar_link()
#             full_response += MEET_FOOTER_TEMPLATE.format(calendar_link=calendar_link)
#             print(f"[MEET LINK APPENDED] calendar link added")

#         # ── Step 15b: Team connect prompt (2-3 questions ke baad) ─────────────
#         state = get_state(from_no)
#         if state.get("append_team_prompt") and not append_meet:
#             service = state.get("service") or f"{CFG['company_name']} AI services"
#             full_response += "\n\n" + _connect_team_prompt(
#                 state.get("name") or "there", service
#             )
#             state["append_team_prompt"] = False
#             print(f"[TEAM PROMPT APPENDED] qa_count={state.get('qa_count')}")



#         # ── Step 16: Save + send ───────────────────────────────────────────────
#         add_to_memory(session_id, "assistant", full_response)
#         send_whatsapp_message(from_no, full_response)
#         save_log(
#             db=db, session_id=session_id, query=text,
#             response=full_response, intent="answer",
#             username=from_no, ip_address=None,
#         )

#     except Exception as e:
#         print(f"[_process_message ERROR] {e}")
#     finally:
#         db.close()


# def _process_message(from_no: str, text: str):
#     session_id = f"wa_{from_no}"
#     db = SessionLocal()

#     # 🔹 Total latency start
#     _t0 = time.time()

#     print(f"\n{'='*50}")
#     print(f"[LATENCY START] query={text!r}")

#     try:
#         # ── Step 1: Conversational flow ───────────────────────────────
#         flow_reply = handle_flow(from_no, text)

#         if flow_reply is not None:
#             send_whatsapp_message(from_no, flow_reply)

#             add_to_memory(session_id, "user", text)
#             add_to_memory(session_id, "assistant", flow_reply)

#             save_log(
#                 db=db,
#                 session_id=session_id,
#                 query=text,
#                 response=flow_reply,
#                 intent="flow",
#                 username=from_no,
#                 ip_address=None,
#             )
#             return

#         # ── Step 2: Guardrail ─────────────────────────────────────────
#         if _is_blocked(text):
#             send_whatsapp_message(from_no, GUARDRAIL_MSG)
#             return

#         # ── Step 3: Interest detection ────────────────────────────────
#         user_interested = bool(_INTEREST_RE.search(text))
#         append_meet = user_interested

#         # ── Step 4: State ─────────────────────────────────────────────
#         state = get_state(from_no)
#         name = state.get("name") or "there"
#         service = state.get("service") or f"{CFG['company_name']} AI services"

#         # ── Step 5: Query rewrite ─────────────────────────────────────
#         history = get_memory(session_id)
#         search_query = _rewrite_query(text, history).lower()

#         # ── Step 6: 🔥 RAG LATENCY START ─────────────────────────────
#         t_rag = time.time()

#         docs = hybrid_search(search_query, WEBSITE_SESSION)
#         if not docs:
#             docs = hybrid_search(search_query, session_id)

#         print(f"[RAG TIME] {round((time.time() - t_rag)*1000, 2)} ms")

#         # ── Step 7: Filter + rank ────────────────────────────────────
#         filtered = [d for d in docs if _is_relevant(d, text) and _is_clean(d)]
#         if not filtered:
#             filtered = docs

#         top_docs = filtered[:5]
#         context = "".join(f"\n{d}\n" for d in top_docs)

#         if len(context.strip()) < 30:
#             msg = f"I don't have enough information. Contact: {CONTACT}"
#             msg = _ensure_name_in_reply(msg, name)
#             send_whatsapp_message(from_no, msg)
#             return

#         # ── Step 8: Prompt ───────────────────────────────────────────
#         prompt = f"""
# You are AI assistant for {CFG['company_name']}.
# Answer in 2 sentences only.

# CONTEXT:
# {context}

# QUESTION: {text}
# """

#         add_to_memory(session_id, "user", text)

#         # ── Step 9: 🔥 LLM LATENCY START ─────────────────────────────
#         t_llm = time.time()

#         full_response = ""
#         for chunk in stream_llama(prompt):
#             full_response += chunk

#         print(f"[LLM TIME] {round((time.time() - t_llm)*1000, 2)} ms")

#         if not full_response.strip():
#             full_response = f"No data found. Contact: {CONTACT}"

#         # ── Step 10: Append meet link ────────────────────────────────
#         if append_meet:
#             calendar_link = _build_calendar_link()
#             full_response += f"\n\nBook call: {calendar_link}"

#         # ── Step 11: Send response ───────────────────────────────────
#         send_whatsapp_message(from_no, full_response)

#         add_to_memory(session_id, "assistant", full_response)

#         save_log(
#             db=db,
#             session_id=session_id,
#             query=text,
#             response=full_response,
#             intent="answer",
#             username=from_no,
#             ip_address=None,
#         )

#     except Exception as e:
#         print(f"[ERROR] {e}")

#     finally:
#         # 🔥 TOTAL LATENCY
#         total_latency = round((time.time() - _t0) * 1000, 2)
#         print(f"[TOTAL LATENCY] {total_latency} ms")

#         db.close()



def _process_message(from_no: str, text: str):
    session_id = f"wa_{from_no}"
    db = SessionLocal()

    # 🔹 Total latency start
    _t0 = time.time()

    print(f"\n{'='*50}")
    print(f"[LATENCY START] query={text!r}")

    try:
        # ── Step 1: Conversational flow ───────────────────────────────
        flow_reply = handle_flow(from_no, text)

        if flow_reply is not None:
            flow_state = get_state(from_no)
            flow_reply = _ensure_name_in_reply(flow_reply, flow_state.get("name"))
            print("⚡ FLOW RESPONSE")
            try:
                send_whatsapp_message(from_no, flow_reply)
                print("✅ Flow message sent")
            except Exception as e:
                print("❌ Flow send error:", e)

            add_to_memory(session_id, "user", text)
            add_to_memory(session_id, "assistant", flow_reply)

            save_log(
                db=db,
                session_id=session_id,
                query=text,
                response=flow_reply,
                intent="flow",
                username=from_no,
                ip_address=None,
            )
            return

        # ── Step 2: Guardrail ─────────────────────────────────────────
        if _is_blocked(text):
            print("🚫 BLOCKED QUERY")
            try:
                guardrail_reply = _ensure_name_in_reply(GUARDRAIL_MSG, get_state(from_no).get("name"))
                send_whatsapp_message(from_no, guardrail_reply)
            except Exception as e:
                print("❌ Guardrail send error:", e)
            return

        # ── Step 3: Interest detection ────────────────────────────────
        user_interested = bool(_INTEREST_RE.search(text))
        append_meet = user_interested

        # ── Step 4: State ─────────────────────────────────────────────
        state = get_state(from_no)
        name = state.get("name") or "there"
        service = state.get("service") or f"{CFG['company_name']} AI services"

        # ── Step 5: Query rewrite ─────────────────────────────────────
        history = get_memory(session_id)
        search_query = _rewrite_query(text, history).lower()

        # ── Step 6: 🔥 RAG LATENCY ────────────────────────────────────
        t_rag = time.time()

        docs = hybrid_search(search_query, WEBSITE_SESSION)
        if not docs:
            docs = hybrid_search(search_query, session_id)

        print(f"[RAG TIME] {round((time.time() - t_rag)*1000, 2)} ms")
        print(f"[RAG DOCS] {len(docs)}")

        # ── Step 7: Filter + rank ────────────────────────────────────
        filtered = [d for d in docs if _is_relevant(d, text) and _is_clean(d)]
        if not filtered:
            filtered = docs

        top_docs = filtered[:5]
        context = "".join(f"\n{d}\n" for d in top_docs)

        print(f"[CONTEXT LENGTH] {len(context)}")

        if len(context.strip()) < 30:
            msg = f"I don't have enough information. Contact: {CONTACT}"
            msg = _ensure_name_in_reply(msg, name)
            state = get_state(from_no)
            if state.get("append_meet_link") and not _has_meeting_link(msg):
                msg += _meet_nudge(state.get("name") or "there")
                state["append_meet_link"] = False
            try:
                send_whatsapp_message(from_no, msg)
            except Exception as e:
                print("❌ Fallback send error:", e)
            return

        # ── Step 8: Prompt ───────────────────────────────────────────
        prompt = f"""
You are AI assistant for {CFG['company_name']}.
Answer in 2 sentences only.

CONTEXT:
{context}

QUESTION: {text}
"""

        add_to_memory(session_id, "user", text)

        # ── Step 9: 🔥 LLM CALL ───────────────────────────────────────
        print("🚀 LLM CALL START")

        t_llm = time.time()
        full_response = ""

        try:
            for chunk in stream_llama(prompt):
                full_response += chunk

            print("✅ LLM RESPONSE RECEIVED")

        except Exception as e:
            print("❌ LLM ERROR:", e)
            full_response = "Sorry, AI service is temporarily unavailable."

        print(f"[LLM TIME] {round((time.time() - t_llm)*1000, 2)} ms")

        if not full_response.strip():
            full_response = f"No data found. Contact: {CONTACT}"

        # ── Step 10: Append meet link ────────────────────────────────
        if append_meet:
            calendar_link = _build_calendar_link()
            full_response += f"\n\n📅 Book call: {calendar_link}"
            print("📅 Meet link appended")

        state = get_state(from_no)
        if state.get("append_meet_link") and not _has_meeting_link(full_response):
            full_response += _meet_nudge(state.get("name") or "there")
            state["append_meet_link"] = False

        # ── Step 11: Send response ───────────────────────────────────
        full_response = _ensure_name_in_reply(full_response, name)
        print("📤 Sending WhatsApp message...")
        print("📝 Response Preview:", full_response[:200])

        try:
            send_whatsapp_message(from_no, full_response)
            print("✅ Message sent successfully")
        except Exception as e:
            print("❌ WhatsApp send error:", e)

        add_to_memory(session_id, "assistant", full_response)

        save_log(
            db=db,
            session_id=session_id,
            query=text,
            response=full_response,
            intent="answer",
            username=from_no,
            ip_address=None,
        )

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        # 🔥 TOTAL LATENCY
        total_latency = round((time.time() - _t0) * 1000, 2)
        print(f"[TOTAL LATENCY] {total_latency} ms")

        db.close()

# ══════════════════════════════════════════════════════════════════════════════
# ── Lead capture helper ───────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

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
        print(f"Lead captured: {state.get('name')} - {state.get('service')}")
    except Exception as e:
        print(f"Lead capture error (non-fatal): {e}")
