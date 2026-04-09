# scrape_website.py  ← place this in your D:\workbench\ root folder
# Run manually: python scrape_website.py
# Run weekly via Task Scheduler to keep knowledge fresh

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.scraper_service import load_website_to_chromadb

if __name__ == "__main__":
    print("Starting swaransoft.com ingestion into ChromaDB...")
    total = load_website_to_chromadb()
    print(f"Done. {total} chunks ready for chat and WhatsApp queries.")
