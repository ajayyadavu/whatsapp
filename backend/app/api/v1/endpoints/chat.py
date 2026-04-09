import json
import re
import time
import random
import requests as _requests
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.bot_config import BOT_CONFIG
from app.core.config import settings
from app.db.session import get_db
from app.services.rag_service import hybrid_search, WEBSITE_SESSION
from app.services.memory_service import (
    add_to_memory,
    get_memory,
    reset_session,
    increment_chat_count,
)

router = APIRouter()

CFG     = BOT_CONFIG
CONTACT = f"{CFG['website']} | {CFG['email']}"

# ── Greeting regex ────────────────────────────────────────────────────────────
_GREETING_RE = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|hiya|namaste|namaskar|yo+|sup|greetings?|helo+|hii+|helloo+|heyyy+)"
    r"[\s!?.]*$",
    re.IGNORECASE,
)
GREETING_REPLY = "Hi, welcome to Swarnsoft AI. We are happy to help you."

# ── Interest / buying-intent keywords — triggers Meet link ───────────────────
# "more details" bhi include hai
_INTEREST_RE = re.compile(
    r"(i('m|\s+am)\s+interested"
    r"|want\s+to\s+know\s+more"
    r"|tell\s+me\s+more"
    r"|more\s+info(rmation)?"
    r"|more\s+details?"
    r"|in\s+more\s+det"
    r"|i\s+want\s+more"
    r"|sounds?\s+good"
    r"|sounds?\s+interesting"
    r"|interested"
    r"|know\s+more"
    r"|learn\s+more"
    r"|get\s+in\s+touch"
    r"|contact\s+you"
    r"|reach\s+out)",
    re.IGNORECASE,
)

# ── 4-question tracker (in-memory per server run) ─────────────────────────────
_question_num: dict = {}


class ChatRequest(BaseModel):
    message:    str
    session_id: Optional[str] = "default"


# ── Google Calendar link ──────────────────────────────────────────────────────

def _build_calendar_link() -> str:
    tomorrow = (datetime.utcnow() + timedelta(days=1)).replace(
        hour=4, minute=30, second=0, microsecond=0
    )
    end = tomorrow + timedelta(minutes=15)
    fmt = "%Y%m%dT%H%M%SZ"
    params = {
        "action":  "TEMPLATE",
        "text":    f"Discovery Call with {CFG['company_name']}",
        "details": f"15-minute discovery call with {CFG['company_name']}.\nContact: {CONTACT}",
        "dates":   f"{tomorrow.strftime(fmt)}/{end.strftime(fmt)}",
        "add":     CFG["email"],
        "sf":      "true",
        "output":  "xml",
    }
    return "https://calendar.google.com/calendar/render?" + urlencode(params)


MEET_FOOTER_TEMPLATE = (
    "\n\n📅 Want to know more? Book a free 15-min call with our team: {calendar_link}"
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def rewrite_query(query: str, history: list) -> str:
    if len(query.split()) <= 3 and history:
        last = next(
            (m["content"] for m in reversed(history) if m["role"] == "user"),
            ""
        )
        if last and last != query:
            return f"{last} {query}"
    return query


def is_relevant(doc: str, query: str) -> bool:
    q_words = set(query.lower().split())
    d_words = set(doc.lower().split())
    return len(q_words & d_words) >= 2


def is_clean(doc: str) -> bool:
    bad_words = ["contact", "email", "phone", "iso", "+91", "visit"]
    return not any(w in doc.lower() for w in bad_words)


# ── Streaming: greeting (5-10 sec delay) ─────────────────────────────────────

def _stream_greeting(session_id: str):
    def gen():
        time.sleep(random.uniform(0.5, 1))
        full  = ""
        words = GREETING_REPLY.split(" ")
        for i, word in enumerate(words):
            chunk  = word + (" " if i < len(words) - 1 else "")
            full  += chunk
            yield chunk
            time.sleep(0.05)
        add_to_memory(session_id, "assistant", full.strip())

    return StreamingResponse(
        gen(), media_type="text/plain",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Streaming: RAG + LLM ──────────────────────────────────────────────────────

def _stream(prompt, session_id, docs, query, append_meet_link: bool = False):
    def gen():
        full = ""
        try:
            resp = _requests.post(
                settings.OLLAMA_URL,
                json={
                    "model":   settings.LLM_MODEL,
                    "prompt":  prompt,
                    "stream":  True,
                    "options": {
                        "temperature": 0.2,
                        "num_ctx":     4096,
                        "num_predict": 80,   # ← max ~2 sentences worth of tokens
                    },
                },
                stream=True,
            )
            for line in resp.iter_lines():
                if not line:
                    continue
                data  = json.loads(line.decode())
                token = data.get("response", "")
                if token:
                    full += token
                    yield token
        except Exception:
            from app.services.llm_service import format_rag_answer
            fallback = format_rag_answer(query, docs)
            full    += fallback
            yield fallback

        if append_meet_link:
            calendar_link = _build_calendar_link()
            meet_footer   = MEET_FOOTER_TEMPLATE.format(calendar_link=calendar_link)
            full         += meet_footer
            yield meet_footer

        if full:
            add_to_memory(session_id, "assistant", full)

    return StreamingResponse(gen(), media_type="text/plain")


# ── MAIN ROUTE ────────────────────────────────────────────────────────────────

@router.post("/")
def chat(req: ChatRequest, request: Request, db: Session = Depends(get_db)):

    query      = req.message.strip()
    session_id = req.session_id or "default"

    # YES → meeting link
    if query.lower() in ["yes", "ok", "sure"]:
        meet_url = "https://meet.google.com/new"
        def _stream_meet():
            yield meet_url
        return StreamingResponse(
            _stream_meet(), media_type="text/plain",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ── Greeting ──────────────────────────────────────────────────────────────
    if _GREETING_RE.match(query):
        print(f"[GREETING] {query!r}")
        add_to_memory(session_id, "user", query)
        return _stream_greeting(session_id)

    # ── 4-question session cycle ──────────────────────────────────────────────
    current_q = _question_num.get(session_id, 0)
    if current_q >= 4:
        reset_session(session_id)
        _question_num[session_id] = 1
    else:
        _question_num[session_id] = current_q + 1

    print(f"[SESSION] question #{_question_num[session_id]}  session_id={session_id}")

    add_to_memory(session_id, "user", query)
    count = increment_chat_count(session_id)

    # ── Interest detection → append meet link (ONLY on explicit interest keywords) ──
    user_interested = bool(_INTEREST_RE.search(query))
    append_meet     = user_interested
    print(f"[INTEREST] {user_interested}  append_meet={append_meet}  query={query!r}")

    # ── Query enrichment ──────────────────────────────────────────────────────
    history      = get_memory(session_id)
    search_query = rewrite_query(query, history).lower()
    print(f"[SMART QUERY] {search_query!r}")

    # ── RAG search ────────────────────────────────────────────────────────────
    docs = hybrid_search(search_query, session_id)
    print(f"[RAG] got {len(docs)} docs from hybrid_search")
    for i, d in enumerate(docs[:3]):
        print(f"  [{i+1}] {d[:100]}")

    # ── Filter + rerank ───────────────────────────────────────────────────────
    filtered = [d for d in docs if is_relevant(d, query) and is_clean(d)]
    if not filtered:
        filtered = docs[:10]

    scored   = [(d, sum(w in d.lower() for w in query.lower().split())) for d in filtered]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_docs = [d for d, _ in scored[:4]]

    context = "".join(f"\n[Chunk {i+1}]\n{d}\n" for i, d in enumerate(top_docs))
    print(f"[CONTEXT] {len(context)} chars")

    # ── Guardrail: block off-topic questions ────────────────────────────────────
    BLOCKED_KEYWORDS = [
        # General off-topic / personal
        "cricket", "football", "sports", "movie", "film", "song", "music",
        "recipe", "cooking", "food", "weather", "news", "politics", "religion",
        "joke", "meme", "girlfriend", "boyfriend", "love", "marriage", "dating",
        "astrology", "horoscope", "lottery", "gambling", "casino", "sex",
        "president", "minister", "prime minister", "modi", "trump",
        "hacking", "porn", "actor", "actress", "bird", "malicious", "hacker",
        "amit shah", "narendre modi", "yogi", "saini", "joshi", "singh",
        "yadav", "thakur", "bollywood", "hollywood","obama","joe","lunch","masala",
        "chicken","mutton","alcohol","daaru","daru","milk","chai","tea","coffee","animal",
        "cow","drink","buffallo","light","electricity","tiffin","tv","television","breakfast",
        "house","hote","road","building","clothes","shoes","chair","bag","table","resturant","cup",
        "plastic","rubber","notebook","bag","pen","charger","water","rajnikant","amitabh","burger","pizza",
        "chinese","italian","earphone","ear","nose","hair","hat","summer","winter","rain","chasma","chair",
        "bottle","coke","pencil","box","camera","parking","color","rupees","dollar","$","ring","gold","silver",
        "diamond","school","dinner","paint","bulb","juice","fruit","apple","banana","orange","mango","beers","beer",
        "salt","oil","petrol","diesel","grapes","kela","shakes","pani puri","pani","ring","bell","AC","air conditioner",
        "toilet","biscuit","chocolate","namkeen","tissue","male","female","men","man","gender","calculator",
        "calculation","umbrella","god","shiv","hanuman","bhagwan","money","paisa","energy","jim","zim","tatoo",
        "paps","pops","beared","pant","shirt","/",".","*","^","~","!","%",";","elon musk","ambani","adani","cm","reliance",
        "tata","kolkata","mumbai","delhi","gujarat","pm","bihar","up","uttar pradesh",
        # Competitor / unrelated tech
        "chatgpt", "openai", "gemini", "copilot", "bard","bus","truck","train","airplane","flight"
    ]
    query_lower = query.lower()
    is_blocked = any(
        re.search(r'(?<![\w])' + re.escape(kw) + r'(?![\w])', query_lower)
        for kw in BLOCKED_KEYWORDS
    )

    if is_blocked:
        def _stream_guardrail():
            time.sleep(random.uniform(0.5, 1))
            msg = "That sounds interesting! However, my expertise is limited to SwaranSoft. Please ask me something related to our platform so I can give you the best information."
            for i, word in enumerate(msg.split(" ")):
                yield word + (" " if i < len(msg.split(" ")) - 1 else "")
                time.sleep(0.05)
        return StreamingResponse(
            _stream_guardrail(), media_type="text/plain",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ── No context fallback ───────────────────────────────────────────────────
    if len(context.strip()) < 50:
        msg = f"I don't have enough information on that. Contact us: {CONTACT}"
        if append_meet:
            msg += MEET_FOOTER_TEMPLATE.format(calendar_link=_build_calendar_link())
        def _stream_fallback(m=msg):
            for word in m.split(" "):
                yield word + " "
                time.sleep(0.03)
        return StreamingResponse(
            _stream_fallback(), media_type="text/plain",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ── Prompt — strict 2 sentence limit ─────────────────────────────────────
    prompt = f"""You are a strict AI assistant for {CFG['company_name']}.

RULES:
- Answer ONLY from the CONTEXT below
- Write EXACTLY 2 sentences. Not 3, not 4. Just 2.
- No bullet points, no lists
- If answer not found in context → say only: "Please contact us at {CONTACT}"

CONTEXT:
{context}

QUESTION:
{query}

2-SENTENCE ANSWER:"""

    return _stream(prompt, session_id, top_docs, query, append_meet_link=append_meet)
