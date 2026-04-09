# app/core/bot_config.py
# ✅ Single source of truth — edit this file to change ALL bot behaviour.

BOT_CONFIG = {
    # ── Company identity ──────────────────────────────────────────────────────
    "company_name":   "Swaran Soft",
    "website":        "https://swaransoft.com",
    "email":          "info@swaransoft.com",
    "phone_india":    "+91 9220-313-650",
    "phone_uae":      "+971-50-9292-650",
    "tagline":        "India's AI-first enterprise implementation partner",
    "years":          "25+",
    "clients":        "350+",
    "offices":        "India, UAE, USA, Estonia and Finland",

    # ── Response length ───────────────────────────────────────────────────────
    "max_tokens":    200,
    "max_sentences": 3,

    # ── WhatsApp ──────────────────────────────────────────────────────────────
    "whatsapp_verify_token": "swaran_verify_2024",

    # ── Services ──────────────────────────────────────────────────────────────
    "services": [
        {"emoji": "💡", "name": "AI Consulting"},
        {"emoji": "📱", "name": "App Development"},
        {"emoji": "🔒", "name": "Digital Security"},
        {"emoji": "📣", "name": "Digital Marketing"},
        {"emoji": "⚙️",  "name": "SAP & Machine Learning"},
    ],

    # ── Post-service actions ──────────────────────────────────────────────────
    "actions": [
        {"key": "1", "emoji": "📅", "label": "Schedule a Demo"},
        {"key": "2", "emoji": "💬", "label": "Talk to an Expert"},
        {"key": "3", "emoji": "🌐", "label": "Visit our Website"},
        {"key": "4", "emoji": "❓", "label": "Ask a Question"},
        {"key": "5", "emoji": "📹", "label": "Book a Google Meet"},
    ],

    # ── Guardrail: always block ───────────────────────────────────────────────
    "blocked_topics": [
        "cricket", "football", "soccer", "tennis", "golf", "baseball", "hockey",
        "nba", "ipl", "fifa", "olympics",
        "recipe", "cook", "bake", "ingredient", "restaurant",
        "weather", "temperature", "forecast",
        "movie", "film", "actor", "actress", "bollywood", "hollywood",
        "song", "music", "lyrics", "album", "singer",
        "porn", "sex", "nude", "naked",
        "drug", "narcotics", "hack", "malware", "virus", "exploit",
        "bitcoin", "crypto", "ethereum", "nft", "stock market", "forex",
        "politics", "election", "vote", "parliament",
        "joke", "meme",
        "modi", "trump", "biden", "obama", "gandhi", "einstein",
        "elon musk", "bill gates", "mark zuckerberg", "jeff bezos",
        "capital of", "population of", "gdp", "inflation",
        "world war", "battle of",
        "planet", "galaxy", "astronomy", "evolution",
        "periodic table", "newton", "darwin",
    ],

    # ── Guardrail: always allow ───────────────────────────────────────────────
    "allowed_topics": [
        "swaran", "swaransoft", "swaran soft",
        "ai consulting", "app development", "digital security",
        "digital marketing", "sap", "machine learning",
        "agentic", "healthcare ai", "geo", "generative engine",
        "ai revenue", "digital transformation",
        "your service", "your product", "your solution", "your team",
        "your company", "your office", "your client", "your price",
        "your cost", "your demo", "your pilot", "your contact",
        "about you", "who are you", "what do you do", "what can you",
    ],

    # ── Guardrail: conversational pass-through ────────────────────────────────
    "conversational": [
        "hi", "hello", "hey", "thanks", "thank you", "okay", "ok",
        "sure", "great", "got it", "sounds good", "yes", "no", "bye",
        "my name", "i am", "i'm", "call me",
    ],
}
