# app/services/llm_service.py

import requests
import json
from app.core.config import settings
from app.core.bot_config import BOT_CONFIG

CFG = BOT_CONFIG


def _base_options(num_predict: int = None, ctx: int = 2048) -> dict:
    return {
        "temperature": 0.2,
        "num_predict": num_predict or CFG["max_tokens"],
        "num_ctx": ctx,
        "top_k": 20,
        "top_p": 0.85,
        "repeat_penalty": 1.1,
    }


# ── Blocking call ─────────────────────────────────────────────────────────────

def call_llama(prompt: str, temperature: float = 0.2, num_predict: int = None) -> str:
    """
    Blocking LLM call — optimized for RAG (low temperature).
    """
    predict = num_predict or CFG["max_tokens"]

    try:
        response = requests.post(
            settings.OLLAMA_URL,
            json={
                "model": settings.LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": predict,
                    "num_ctx": 2048,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                },
            },
            timeout=300,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except requests.exceptions.Timeout:
        print("[call_llama] Timeout after 300s")
        return ""

    except Exception as e:
        print(f"[call_llama ERROR] {e}")
        return ""


# ── Streaming call ────────────────────────────────────────────────────────────

def stream_llama(prompt: str):
    """
    Streams tokens live from Ollama.
    ✅ FIXED: num_predict 80→200, num_ctx 1024→4096 for quality responses.
    """
    try:
        response = requests.post(
            settings.OLLAMA_URL,
            json={
                "model": settings.LLM_MODEL,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 200,   # ✅ was 80 (too short, answers were cut off)
                    "num_ctx": 4096,      # ✅ was 1024 (context was being truncated)
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                },
            },
            stream=True,
            timeout=300,
        )

        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                continue

    except requests.exceptions.ConnectionError:
        yield "[LLM_UNAVAILABLE]"

    except requests.exceptions.Timeout:
        yield "[LLM_TIMEOUT]"

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        yield "[LLM_ERROR]"


# ── RAG-only fallback formatter ───────────────────────────────────────────────

def format_rag_answer(query: str, docs: list) -> str:
    if not docs:
        return ""

    q_words = set(query.lower().split())
    bullets = []

    for doc in docs[:5]:
        lines = [
            l.strip()
            for l in doc.replace(".", ".\n").splitlines()
            if len(l.strip()) > 20
        ]

        best = max(
            lines,
            key=lambda l: len(q_words & set(l.lower().split())),
            default=""
        )

        if best and len(best) > 20:
            short = best[:90] + "..." if len(best) > 90 else best
            bullets.append(f"• {short}")

    if not bullets:
        return ""

    return "\n".join(bullets)


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(query: str, context_docs: list[str]) -> str:
    context = "\n\n".join(context_docs)

    return f"""
You are a strict AI assistant.

Rules:
- Use ONLY the provided context
- Do NOT use your own knowledge
- If answer is not in context, say: "Not found"
- Give SHORT answer (max 3-4 lines)
- No extra explanation

Context:
{context}

Question:
{query}

Answer:
"""
