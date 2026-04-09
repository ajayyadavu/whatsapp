import re
import threading
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.services.whatsapp_service import send_whatsapp_message
from app.services.rag_service import hybrid_search
from app.services.llm_service import stream_llama, format_rag_answer
from app.services.memory_service import get_memory, add_to_memory
from app.services.log_service import save_log
from app.db.session import SessionLocal
from app.core.bot_config import BOT_CONFIG

router = APIRouter()

VERIFY_TOKEN    = "swaran_verify_2024"
CFG             = BOT_CONFIG
CONTACT         = f"{CFG['phone_india']} | {CFG['phone_uae']} | {CFG['email']}"
WEBSITE_SESSION = "swaransoft_website"


# ── Helpers (same logic as chat.py) ──────────────────────────────────────────

def _rewrite_query(query: str, history: list) -> str:
    """Expand vague short queries using last user message from history."""
    if len(query.split()) <= 3 and history:
        last = next(
            (m["content"] for m in reversed(history) if m["role"] == "user"),
            ""
        )
        if last and last != query:
            return f"{last} {query}"
    return query


def _is_relevant(doc: str, query: str) -> bool:
    q_words = set(query.lower().split())
    d_words = set(doc.lower().split())
    return len(q_words & d_words) >= 2


def _is_clean(doc: str) -> bool:
    bad_words = ["contact", "email", "phone", "iso", "+91", "visit"]
    return not any(w in doc.lower() for w in bad_words)


# ── Meta verification (GET) ───────────────────────────────────────────────────

@router.get("/webhook")
async def verify(request: Request):
    mode      = request.query_params.get("hub.mode")
    token     = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)
    return {"error": "Verification failed"}


# ── Incoming messages (POST) ──────────────────────────────────────────────────

@router.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("📩 RAW WEBHOOK:", body)

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
            target=_process_rag,
            args=(from_no, text),
            daemon=True,
        ).start()

    except Exception as e:
        print(f"Webhook parse error: {e}")

    return {"status": "ok"}


# ── Background RAG pipeline (quality matched to chat.py) ─────────────────────

def _process_rag(from_no: str, text: str):
    """
    Full RAG pipeline with:
    - Smart query rewriting
    - RAG filtering & reranking
    - Rich structured prompt (same quality as chat.py)
    - Proper LLM settings (enough tokens + context)
    """
    session_id = f"wa_{from_no}"
    db = SessionLocal()

    try:
        # ── Step 1: Conversation history ──────────────────────────────────────
        history = get_memory(session_id)[-8:]   # last 4 user+assistant turns

        # ── Step 2: Query rewriting (expand vague short queries) ──────────────
        search_query = _rewrite_query(text, history)
        print(f"[SMART QUERY] {search_query!r}")

        # ── Step 3: RAG search ─────────────────────────────────────────────────
        docs = hybrid_search(search_query, WEBSITE_SESSION)
        if not docs:
            docs = hybrid_search(search_query, session_id)
        print(f"[RAG] got {len(docs)} docs")

        # ── Step 4: Filter + Rerank (same as chat.py) ─────────────────────────
        filtered = [d for d in docs if _is_relevant(d, text) and _is_clean(d)]
        if not filtered:
            filtered = docs[:10]

        scored   = [(d, sum(w in d.lower() for w in text.lower().split())) for d in filtered]
        scored.sort(key=lambda x: x[1], reverse=True)
        top_docs = [d for d, _ in scored[:4]]

        context = "".join(f"\n[Chunk {i+1}]\n{d}\n" for i, d in enumerate(top_docs))
        print(f"[CONTEXT] {len(context)} chars")

        # ── Step 5: Build conversation history block ───────────────────────────
        history_text = ""
        if history:
            lines = []
            for m in history:
                role = "User" if m["role"] == "user" else "Bot"
                lines.append(f"{role}: {m['content'][:200]}")
            history_text = "\n".join(lines)

        # ── Step 6: Build prompt ───────────────────────────────────────────────
        if len(context.strip()) >= 50:
            history_block = f"\nCONVERSATION SO FAR:\n{history_text}\n" if history_text else ""
            prompt = (
                f"You are Swaran AI for {CFG['company_name']}, answering on WhatsApp.\n"
                f"{history_block}\n"
                f"CRITICAL: Reply in plain text only. NO JSON. NO markdown. NO code blocks.\n"
                f"Do NOT start your reply with phrases like 'Here is the answer:' or 'Sure!'. Start directly with the answer.\n\n"
                f"INSTRUCTIONS:\n"
                f"- Use ONLY the CONTEXT below.\n"
                f"- If the question is about a specific person (e.g. 'who is X'), write ONLY 1 sentence (under 20 words).\n"
                f"- For service/product/topic questions: write MAXIMUM 2-3 short sentences (under 60 words total).\n"
                f"- Do NOT use bullet points.\n"
                f"- Do NOT add unrequested details.\n"
                f"- End with: More info: {CFG['website']}\n"
                f"- If answer NOT in context say: Not found. Contact: {CONTACT}\n\n"
                f"CONTEXT:\n{context}\n\nQ: {text}\nA:"
            )
            print("MODE: RAG answer")
        else:
            prompt = (
                f"You are Swaran AI for {CFG['company_name']} on WhatsApp.\n"
                f"Reply in plain text only. NO JSON.\n"
                f"No data found. In 1 line direct user to contact: {CONTACT}\n\nQ: {text}\nA:"
            )
            print("MODE: No RAG fallback")

        # ── Step 7: Save user message ──────────────────────────────────────────
        add_to_memory(session_id, "user", text)

        # ── Step 8: LLM call ───────────────────────────────────────────────────
        full_response = ""
        for chunk in stream_llama(prompt):
            if chunk in ("[LLM_UNAVAILABLE]", "[LLM_TIMEOUT]", "[LLM_ERROR]"):
                full_response = format_rag_answer(text, top_docs) if top_docs else ""
                if not full_response:
                    full_response = f"I don't have that detail right now. Please contact us: {CONTACT}"
                break
            full_response += chunk

        # ── Step 9: Strip JSON wrapper if LLM returned JSON instead of plain text
        import json as _json
        try:
            parsed = _json.loads(full_response.strip())
            if isinstance(parsed, dict) and "response" in parsed:
                full_response = parsed["response"]
        except Exception:
            pass

        json_match = re.search(r'\{\s*"response"\s*:\s*"(.*?)"\s*\}', full_response, re.DOTALL)
        if json_match:
            full_response = json_match.group(1)

        # ── Step 10: Strip LLM preamble phrases ───────────────────────────────
        full_response = re.sub(
            r'^(here\s+is\s+(the|my|an)?\s*answer\s*:|answer\s*:|response\s*:|sure[,!]?\s*here\s+is\s*:|certainly!?|of\s+course!?|great\s+question!?|sure[,!])\s*',
            '', full_response.strip(), flags=re.IGNORECASE
        ).strip()

        if not full_response.strip():
            full_response = f"I don't have that info right now. Contact us: {CONTACT}"

        # ── Step 11: Save & send ───────────────────────────────────────────────
        add_to_memory(session_id, "assistant", full_response)
        send_whatsapp_message(from_no, full_response)
        save_log(
            db=db, session_id=session_id, query=text,
            response=full_response, intent="rag",
            username=from_no, ip_address=None,
        )

    except Exception as e:
        print(f"[_process_rag ERROR] {e}")
    finally:
        db.close()
