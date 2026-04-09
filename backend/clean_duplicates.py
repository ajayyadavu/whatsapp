"""
Run this ONCE from backend folder to clean duplicate PDF chunks:
  cd C:/Users/fresh/Desktop/whatsapp/backend
"""
import sys
sys.path.insert(0, '.')

from app.services.rag_service import get_collection, WEBSITE_SESSION

collection = get_collection(WEBSITE_SESSION)
print(f"Total chunks before cleanup: {collection.count()}")

# Get all items
all_data = collection.get(include=["metadatas", "documents"])
ids       = all_data["ids"]
metadatas = all_data["metadatas"]
documents = all_data["documents"]

# Find duplicates by document content (first 200 chars)
seen    = {}
to_delete = []

for i, (doc_id, doc, meta) in enumerate(zip(ids, documents, metadatas)):
    key = doc[:200]
    if key in seen:
        to_delete.append(doc_id)  # delete the duplicate
    else:
        seen[key] = doc_id

print(f"Duplicate chunks found: {len(to_delete)}")

if to_delete:
    # Delete in batches of 100
    batch = 100
    for i in range(0, len(to_delete), batch):
        collection.delete(ids=to_delete[i:i+batch])
    print(f"Deleted {len(to_delete)} duplicate chunks")

print(f"Total chunks after cleanup: {collection.count()}")

# Show PDF chunks
all_data2  = collection.get(include=["metadatas", "documents"])
pdf_chunks = [(d, m) for d, m in zip(all_data2["documents"], all_data2["metadatas"])
              if m.get("type") == "pdf" or "Agentic" in d[:50]]
print(f"\nPDF chunks remaining: {len(pdf_chunks)}")
for doc, meta in pdf_chunks[:5]:
    print(f"  source={meta.get('source','?')} | {doc[:80]}")