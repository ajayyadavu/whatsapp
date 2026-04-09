# test_website_kb.py
# Place in D:\workbench\ and run: python test_website_kb.py
# Tests if swaransoft.com content is loaded and answering correctly

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import hybrid_search, get_collection
from app.services.llm_service import stream_llama

SESSION_ID = "swaransoft_website"

def test_kb():
    # ── Step 1: Check how many chunks are loaded ──────────────
    collection = get_collection(SESSION_ID)
    count = collection.count()
    print(f"\n ChromaDB has {count} chunks for 'swaransoft_website'")

    if count == 0:
        print(" No website content found. Run: python scrape_website.py first.")
        return

    # ── Step 2: Run test questions ────────────────────────────
    questions = [
        "What does Swaran Soft do?",
        "What AI services does Swaran Soft offer?",
        "How long does a pilot take?",
        "Which industries does Swaran Soft serve?",
        "How can I contact Swaran Soft?",
        "What is the cost of a pilot?",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"❓ {q}")

        docs = hybrid_search(q, SESSION_ID)

        if not docs:
            print("⚠️  No relevant chunks found — will use LLM general knowledge")
            prompt = f"Answer this about Swaran Soft: {q}"
        else:
            print(f"✅ Found {len(docs)} relevant chunks")
            context = "\n\n".join(docs[:3])
            prompt = f"""You are Swaran AI for Swaran Soft (swaransoft.com).
Answer using ONLY the context below. Be concise.

Context:
{context}

Question: {q}

Answer:"""

        print("💬 Answer: ", end="", flush=True)
        for chunk in stream_llama(prompt):
            print(chunk, end="", flush=True)
        print()

if __name__ == "__main__":
    test_kb()
