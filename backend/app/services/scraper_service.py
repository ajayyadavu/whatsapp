# app/services/scraper_service.py
# IMPROVED:
#   - LLM generates a clean title/name for each scraped page
#   - LLM rewrites raw scraped text into structured, readable knowledge chunks
#   - Better deduplication and noise removal before storing to ChromaDB

# from playwright.sync_api import sync_playwright
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from app.services.rag_service import get_collection, _CHROMA_DIR
# from app.services.llm_service import call_llama
# from urllib.parse import urlparse
# import uuid
# import re
# import json

# SWARAN_PAGES = [
#     "https://swaransoft.com/",
#     "https://swaransoft.com/services",
#     "https://swaransoft.com/agentic-ai",
#     "https://swaransoft.com/healthcare-ai",
#     "https://swaransoft.com/geo",
#     "https://swaransoft.com/ai-revenue-systems",
#     "https://swaransoft.com/industries",
#     "https://swaransoft.com/industries/manufacturing",
#     "https://swaransoft.com/industries/bfsi",
#     "https://swaransoft.com/industries/healthcare",
#     "https://swaransoft.com/industries/retail",
#     "https://swaransoft.com/industries/telecom",
#     "https://swaransoft.com/industries/education",
#     "https://swaransoft.com/industries/government",
#     "https://swaransoft.com/industries/logistics",
#     "https://swaransoft.com/about",
#     "https://swaransoft.com/case-studies",
#     "https://swaransoft.com/portfolio",
#     "https://swaransoft.com/contact",
#     "https://swaransoft.com/blog",
#     "https://swaransoft.com/services/ai-consulting",
#     "https://swaransoft.com/services/app-development",
#     "https://swaransoft.com/services/digital-security",
#     "https://swaransoft.com/services/sap-machine-learning",
#     "https://swaransoft.com/about/life-at-swaran-soft",
#     "https://swaransoft.com/about/our-story",
#     "https://swaransoft.com/about#leadership",
#     "https://swaransoft.manus.space/agentic-ai/ai-labs",
#     "https://swaransoft.com/agentic-ai/strategy",
#     "https://swaransoft.com/agentic-ai/development",
#     "https://swaransoft.com/agentic-ai/ai-labs",
#     "https://swaransoft.com/agentic-ai/automation",
#     "https://swaransoft.com/agentic-ai/analytics",
#     "https://swaransoft.com/agentic-ai/managed",
#     "https://swaransoft.com/agentic-ai/workflow-orchestration",
#     "https://swaransoft.com/agentic-ai/voice-ai-agents",
#     "https://swaransoft.com/agentic-ai/whatsapp-ai",
#     "https://swaransoft.com/agentic-ai/smart-ticketing",
#     "https://swaransoft.com/agentic-ai/sentiment-nlp",
#     "https://swaransoft.com/agentic-ai/managed-aiops",
#     "https://swaransoft.com/agentic-ai/aikosh-advantage",
#     "https://swaransoft.com/careers",

    

# ]

# SESSION_ID = "swaransoft_website"

# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,
#     chunk_overlap=150
# )


# # ── Text cleaning ─────────────────────────────────────────────────────────────

# def clean_text(text: str) -> str:
#     """Remove noise: repeated whitespace, symbol-only lines, very short lines."""
#     text = re.sub(r'\n{3,}', '\n\n', text)
#     text = re.sub(r' {2,}', ' ', text)
#     # Drop lines shorter than 5 chars (nav artifacts, stray punctuation, etc.)
#     lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 5]
#     # Drop lines that are mostly non-alphanumeric (e.g. "--- | ---")
#     lines = [l for l in lines if sum(c.isalnum() for c in l) / max(len(l), 1) > 0.35]
#     return "\n".join(lines)


# # ── Verbatim key-facts extractor (bypasses LLM rewrite) ──────────────────────

# def extract_key_facts(url: str, title: str, raw_text: str) -> str:
#     """
#     Pull lines containing statistics, numbers, or key metrics verbatim.
#     These are stored as a separate chunk that the LLM rewrite can NEVER corrupt.
#     """
#     fact_pattern = re.compile(
#         r'(\d+[\+\%]|\d+\s*\+|\d+\s*years?|\d+\s*clients?|\d+\s*wks?|\d+\s*weeks?)',
#         re.IGNORECASE
#     )
#     fact_lines = []
#     for line in raw_text.splitlines():
#         stripped = line.strip()
#         if len(stripped) > 4 and fact_pattern.search(stripped):
#             fact_lines.append(stripped)

#     if not fact_lines:
#         return ""

#     block = "\n".join(dict.fromkeys(fact_lines[:50]))  # deduplicate, cap at 50
#     return (
#         f"[VERBATIM KEY FACTS from {title} — {url}]\n"
#         f"{block}"
#     )


# # ── LLM-powered page title generation ────────────────────────────────────────

# def llm_generate_title(url: str, raw_text: str) -> str:
#     """
#     Ask the LLM to produce a clear, descriptive title for this page.
#     Falls back to URL slug if LLM fails.
#     """
#     snippet = raw_text[:800]
#     prompt = (
#         f"You are a content analyst. Given the URL and a snippet of page content below, "
#         f"write a SHORT, clear, descriptive title (5–10 words) that accurately names "
#         f"what this page is about. Output ONLY the title — no quotes, no explanation.\n\n"
#         f"URL: {url}\n\n"
#         f"Content snippet:\n{snippet}\n\n"
#         f"Title:"
#     )
#     title = call_llama(prompt, temperature=0.2, num_predict=30)
#     if title:
#         # Strip any accidental quotes or newlines
#         title = title.strip('" \n')
#         print(f"  LLM title: {title}")
#         return title
#     # Fallback: derive from URL slug
#     slug = urlparse(url).path.strip("/").replace("/", " › ").replace("-", " ").title()
#     return slug or "Swaran Soft Homepage"


# # ── LLM-powered page content rewriting ───────────────────────────────────────

# def llm_rewrite_page(url: str, title: str, raw_text: str) -> str:
#     """
#     Ask the LLM to rewrite the raw scraped text into clean, structured,
#     knowledge-base-ready content. Returns the rewritten text, or the
#     original cleaned text if LLM fails.
#     """
#     # Only send first 3000 chars to keep prompt manageable
#     snippet = raw_text[:3000]
#     prompt = (
#         f"You are a knowledge base editor for Swaran Soft (swaransoft.com).\n"
#         f"Below is raw text scraped from the page titled '{title}' at {url}.\n\n"
#         f"Your task:\n"
#         f"1. Remove all navigation links, cookie notices, and repeated boilerplate.\n"
#         f"2. Rewrite the remaining content into clear, factual, well-structured paragraphs.\n"
#         f"3. CRITICAL: Preserve ALL specific facts EXACTLY as they appear: "
#         f"numbers (350+, 25+, 80%, 12 weeks), service names, pricing, timelines, "
#         f"contact info, client counts, percentages. Do NOT round, estimate, or change any number.\n"
#         f"4. Start directly with the content — no preamble like 'Here is the rewritten text:'.\n"
#         f"5. Keep it concise: aim for 300–600 words.\n\n"
#         f"RAW TEXT:\n{snippet}\n\n"
#         f"REWRITTEN CONTENT:"
#     )
#     rewritten = call_llama(prompt, temperature=0.3, num_predict=800)
#     if rewritten and len(rewritten) > 100:
#         print(f"  LLM rewrote content: {len(rewritten)} chars")
#         return rewritten
#     # Fallback: use cleaned raw text
#     print(f"  LLM rewrite failed/too short — using cleaned raw text")
#     return raw_text


# # ── Playwright scraper ────────────────────────────────────────────────────────

# def scrape_page_playwright(page, url: str) -> str:
#     try:
#         page.goto(url, wait_until="networkidle", timeout=40000)
#         page.wait_for_timeout(2500)

#         # Remove clutter elements
#         page.evaluate("""
#             ['nav', 'footer', 'header', 'script', 'style', 'noscript',
#              '.cookie-banner', '.popup', '[aria-hidden="true"]'
#             ].forEach(sel => {
#                 document.querySelectorAll(sel).forEach(el => el.remove());
#             });
#         """)

#         text = page.inner_text("body")
#         clean = clean_text(text)
#         print(f"  Scraped {url} — {len(clean)} chars")
#         return clean

#     except Exception as e:
#         print(f"  Failed {url}: {e}")
#         return ""


# # ── Main ingestion pipeline ───────────────────────────────────────────────────

# def load_website_to_chromadb():
#     collection = get_collection(SESSION_ID)

#     # Clear existing chunks
#     try:
#         existing = collection.count()
#         if existing > 0:
#             print(f"Clearing {existing} existing chunks...")
#             all_ids = collection.get()["ids"]
#             if all_ids:
#                 collection.delete(ids=all_ids)
#     except Exception as e:
#         print(f"Clear error (non-fatal): {e}")

#     total_chunks = 0

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=True)
#         page    = browser.new_page()

#         for url in SWARAN_PAGES:
#             print(f"\nScraping: {url}")
#             raw_text = scrape_page_playwright(page, url)

#             if not raw_text.strip() or len(raw_text) < 100:
#                 print(f"  Skipping — too little content")
#                 continue

#             # ── Step 1: LLM generates a descriptive page title ────────────────
#             title = llm_generate_title(url, raw_text)

#             # ── Step 1b: Extract & store verbatim facts BEFORE any LLM rewrite ───
#             facts_chunk = extract_key_facts(url, title, raw_text)
#             if facts_chunk:
#                 collection.add(
#                     documents=[facts_chunk],
#                     ids=[f"facts_{urlparse(url).path.replace('/', '_') or 'home'}_{uuid.uuid4()}"],
#                     metadatas=[{
#                         "source":  url,
#                         "title":   title,
#                         "type":    "key_facts",
#                         "session": SESSION_ID
#                     }]
#                 )
#                 total_chunks += 1
#                 print(f"  Stored verbatim facts chunk for '{title}'")

#             # ── Step 2: LLM rewrites the content into clean KB text ────────
#             refined_text = llm_rewrite_page(url, title, raw_text)

#             # ── Step 3: Prepend rich metadata header to every chunk ────────
#             text_with_meta = (
#                 f"Page Title: {title}\n"
#                 f"URL: {url}\n"
#                 f"Company: Swaran Soft | Website: swaransoft.com\n\n"
#                 f"{refined_text}"
#             )

#             # ── Step 4: Chunk and store ────────────────────────────────────
#             chunks = splitter.split_text(text_with_meta)

#             for i, chunk in enumerate(chunks):
#                 collection.add(
#                     documents=[chunk],
#                     ids=[f"web_{urlparse(url).path.replace('/', '_') or 'home'}_{i}_{uuid.uuid4()}"],
#                     metadatas=[{
#                         "source":  url,
#                         "title":   title,
#                         "type":    "website",
#                         "session": SESSION_ID
#                     }]
#                 )

#             total_chunks += len(chunks)
#             print(f"  Stored {len(chunks)} chunks for '{title}'")

#         browser.close()

#     print(f"\nWebsite ingestion complete. Total chunks: {total_chunks}")
#     return total_chunks



# app/services/scraper_service.py
#
# FAST VERSION — no LLM calls during scraping.
# Scrapes each page, cleans the text, chunks it, and stores directly into ChromaDB.
# This avoids the 180s timeout that happened when calling LLM for title + rewrite per page.
# Each chunk gets a metadata header (URL + page slug) so the LLM can identify the source.

from playwright.sync_api import sync_playwright
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.rag_service import get_collection, WEBSITE_SESSION
from urllib.parse import urlparse
import uuid
import re

SWARAN_PAGES = [
    "https://swaransoft.com/",
    "https://swaransoft.com/services",
    "https://swaransoft.com/agentic-ai",
    "https://swaransoft.com/healthcare-ai",
    "https://swaransoft.com/geo",
    "https://swaransoft.com/ai-revenue-systems",
    "https://swaransoft.com/industries",
    "https://swaransoft.com/industries/manufacturing",
    "https://swaransoft.com/industries/bfsi",
    "https://swaransoft.com/industries/healthcare",
    "https://swaransoft.com/industries/retail",
    "https://swaransoft.com/industries/telecom",
    "https://swaransoft.com/industries/education",
    "https://swaransoft.com/industries/government",
    "https://swaransoft.com/industries/logistics",
    "https://swaransoft.com/about",
    "https://swaransoft.com/case-studies",
    "https://swaransoft.com/portfolio",
    "https://swaransoft.com/contact",
    "https://swaransoft.com/blog",
    "https://swaransoft.com/services/ai-consulting",
    "https://swaransoft.com/services/app-development",
    "https://swaransoft.com/services/digital-security",
    "https://swaransoft.com/services/sap-machine-learning",
    "https://swaransoft.com/about/life-at-swaran-soft",
    "https://swaransoft.com/about/our-story",
    "https://swaransoft.com/about#leadership",
    "https://swaransoft.com/agentic-ai/strategy",
    "https://swaransoft.com/agentic-ai/development",
    "https://swaransoft.com/agentic-ai/ai-labs",
    "https://swaransoft.com/agentic-ai/automation",
    "https://swaransoft.com/agentic-ai/analytics",
    "https://swaransoft.com/agentic-ai/managed",
    "https://swaransoft.com/agentic-ai/workflow-orchestration",
    "https://swaransoft.com/agentic-ai/voice-ai-agents",
    "https://swaransoft.com/agentic-ai/whatsapp-ai",
    "https://swaransoft.com/agentic-ai/smart-ticketing",
    "https://swaransoft.com/agentic-ai/sentiment-nlp",
    "https://swaransoft.com/agentic-ai/managed-aiops",
    "https://swaransoft.com/agentic-ai/aikosh-advantage",
    "https://swaransoft.com/careers",
    "https://swaransoft.com/careers#open-roles",
]

SESSION_ID = WEBSITE_SESSION

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
)


# ---------------------------------------------------------------------------
# Text cleaning — remove nav clutter, short lines, symbol-only lines
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 5]
    # Drop lines that are mostly non-alphanumeric (nav artifacts, icons, etc.)
    lines = [l for l in lines if sum(c.isalnum() for c in l) / max(len(l), 1) > 0.35]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Derive a readable page title from the URL slug (no LLM needed)
# ---------------------------------------------------------------------------

def slug_to_title(url: str) -> str:
    path = urlparse(url).path.strip("/")
    if not path:
        return "Swaran Soft — Home"
    # Take last segment, replace hyphens, title-case
    parts = path.split("/")
    title = " ".join(p.replace("-", " ").title() for p in parts if p)
    return f"Swaran Soft — {title}"


# ---------------------------------------------------------------------------
# Playwright scraper
# ---------------------------------------------------------------------------

def scrape_page(page, url: str) -> str:
    try:
        page.goto(url, wait_until="networkidle", timeout=40000)
        page.wait_for_timeout(2000)

        # Remove clutter
        page.evaluate("""
            ['nav', 'footer', 'header', 'script', 'style', 'noscript',
             '.cookie-banner', '.popup', '[aria-hidden="true"]'
            ].forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });
        """)

        text = page.inner_text("body")
        clean = clean_text(text)
        print(f"  Scraped {url} — {len(clean)} chars")
        return clean

    except Exception as e:
        print(f"  FAILED {url}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Main ingestion — fast, no LLM calls
# ---------------------------------------------------------------------------

def load_website_to_chromadb():
    collection = get_collection(SESSION_ID)

    # Clear existing data
    try:
        existing = collection.count()
        if existing > 0:
            print(f"Clearing {existing} existing chunks from '{SESSION_ID}'...")
            all_ids = collection.get()["ids"]
            if all_ids:
                collection.delete(ids=all_ids)
            print("Cleared.")
    except Exception as e:
        print(f"Clear error (non-fatal): {e}")

    total_chunks = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        for url in SWARAN_PAGES:
            print(f"\nScraping: {url}")
            raw_text = scrape_page(page, url)

            if not raw_text.strip() or len(raw_text) < 80:
                print(f"  Skipping — too little content ({len(raw_text)} chars)")
                continue

            # Derive title from URL slug (instant, no LLM)
            title = slug_to_title(url)

            # Prepend metadata header to every chunk so LLM knows the source
            text_with_header = (
                f"Source: {url}\n"
                f"Page: {title}\n"
                f"Company: Swaran Soft | swaransoft.com | info@swaransoft.com\n\n"
                f"{raw_text}"
            )

            chunks = splitter.split_text(text_with_header)
            if not chunks:
                print(f"  No chunks produced, skipping")
                continue

            slug = urlparse(url).path.replace("/", "_") or "home"

            for i, chunk in enumerate(chunks):
                collection.add(
                    documents=[chunk],
                    ids=[f"web_{slug}_{i}_{uuid.uuid4()}"],
                    metadatas=[{
                        "source":  url,
                        "title":   title,
                        "type":    "website",
                        "session": SESSION_ID,
                    }],
                )

            total_chunks += len(chunks)
            print(f"  Stored {len(chunks)} chunks for '{title}'")

        browser.close()

    print(f"\nIngestion complete. Total chunks stored: {total_chunks}")
    return total_chunks