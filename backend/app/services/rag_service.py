import os
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from io import BytesIO

CHROMA_DIR = os.path.join(os.getcwd(), "chroma_db")

client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False),
)

embedding = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
)

WEBSITE_SESSION = "swaransoft_website"


# ── Collection ────────────────────────────────────────────────────────────────

def get_collection(name: str):
    return client.get_or_create_collection(
        name=f"docs_{name}",
        embedding_function=embedding,
    )


# ── PDF helpers ───────────────────────────────────────────────────────────────

def extract_text(file) -> str:
    reader = PdfReader(file)
    return "".join(page.extract_text() or "" for page in reader.pages)


def store_pdf(file_bytes: bytes, filename: str, session_id: str) -> int:
    try:
        text   = extract_text(BytesIO(file_bytes))
        chunks = splitter.split_text(text)

        # Remove very short / noisy chunks
        chunks = [c for c in chunks if len(c) > 80 and "http" not in c.lower()]

        if not chunks:
            print(f"[store_pdf] No usable chunks from '{filename}'")
            return 0

        def _store(target: str):
            col = get_collection(target)
            for i, c in enumerate(chunks):
                col.add(
                    documents=[c],
                    ids=[f"{filename}_{target}_{i}_{uuid.uuid4()}"],
                    metadatas=[{"source": filename, "type": "pdf", "session": target}],
                )
            print(f"[store_pdf] Stored {len(chunks)} chunks into '{target}'")

        _store(session_id)
        if session_id != WEBSITE_SESSION:
            _store(WEBSITE_SESSION)

        return len(chunks)

    except Exception as e:
        print(f"[store_pdf ERROR] {e}")
        return 0


# ── Search helpers ────────────────────────────────────────────────────────────

def keyword_score(doc: str, query: str) -> int:
    return sum(word in doc.lower() for word in query.lower().split())


def _search_collection(col, query: str, n: int = 10) -> list[tuple[str, float]]:
    """Search one collection. Returns [(doc, distance)] sorted best-first."""
    try:
        count = col.count()
        if count == 0:
            return []

        n_results = min(n, count)
        results   = col.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "distances"],
        )
        docs  = results["documents"][0] if results["documents"] else []
        dists = results["distances"][0]  if results["distances"]  else []

        print(f"  [SEARCH] '{col.name}' — {count} total, top {len(docs)} returned")
        for doc, dist in zip(docs[:3], dists[:3]):
            print(f"    dist={dist:.3f} | {doc[:80]}")

        return list(zip(docs, dists))

    except Exception as e:
        print(f"[_search_collection ERROR] {e}")
        return []


# ── Main hybrid search ────────────────────────────────────────────────────────

def hybrid_search(query: str, session_id: str) -> list[str]:
    """
    Searches BOTH:
      1. docs_{session_id}       — per-session uploaded PDFs
      2. docs_swaransoft_website — global KB (website + all uploaded PDFs)

    PDF chunks get a distance boost (×0.7) so they rank above website content.
    Returns up to 6 deduplicated document strings, best match first.
    """
    session_col = get_collection(session_id)
    website_col = get_collection(WEBSITE_SESSION)

    session_results = _search_collection(session_col, query, n=10)
    website_results = _search_collection(website_col, query, n=15)

    print(f"\n[RAG] session={len(session_results)}  website={len(website_results)}")

    scored = []
    seen   = set()

    # Session PDF results — boosted score
    for doc, dist in session_results:
        key = doc[:120]
        if key not in seen:
            seen.add(key)
            kscore = keyword_score(doc, query)
            scored.append((doc, dist * 0.7 - kscore * 0.05))

    # Website KB results
    for doc, dist in website_results:
        key = doc[:120]
        if key not in seen:
            seen.add(key)
            kscore = keyword_score(doc, query)
            scored.append((doc, dist - kscore * 0.05))

    scored.sort(key=lambda x: x[1])
    final = [doc for doc, _ in scored[:6]]

    print(f"[RAG FINAL] {len(final)} chunks selected")
    return final
