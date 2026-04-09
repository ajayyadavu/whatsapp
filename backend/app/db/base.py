# app/db/base.py
# Imports Base + all models so Base.metadata has every table registered.
# Used by main.py (create_all) and Alembic migrations.

from app.db.base_class import Base          # noqa: F401

# Import every model here so SQLAlchemy registers the tables
from app.models.user          import User          # noqa: F401, E402
from app.models.whatsapp_user import WhatsAppUser  # noqa: F401, E402
from app.models.chat_log      import ChatLog       # noqa: F401, E402
from app.models.chat_session  import ChatSession   # noqa: F401, E402  ← NEW
