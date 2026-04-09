import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Store per session
faiss_store = {}

def get_faiss_index(session_id):
    if session_id not in faiss_store:
        dimension = 384
        index = faiss.IndexFlatL2(dimension)

        faiss_store[session_id] = {
            "index": index,
            "documents": []
        }

    return faiss_store[session_id]

# Add documents
def add_to_faiss(chunks, session_id):
    store = get_faiss_index(session_id)

    embeddings = model.encode(chunks)

    store["index"].add(np.array(embeddings))
    store["documents"].extend(chunks)

# Search
def search_faiss(query, session_id, k=3):
    store = get_faiss_index(session_id)

    if not store["documents"]:
        return []

    query_vector = model.encode([query])
    distances, indices = store["index"].search(query_vector, k)

    results = []
    for idx in indices[0]:
        if idx < len(store["documents"]):
            results.append(store["documents"][idx])

    return results