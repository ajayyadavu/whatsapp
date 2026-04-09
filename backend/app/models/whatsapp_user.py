# app/models/whatsapp_user.py
# Stores WhatsApp user names permanently by phone number.

from sqlalchemy import Column, String, DateTime
from datetime import datetime

from app.db.base_class import Base          # ← base_class, NOT base


class WhatsAppUser(Base):
    __tablename__ = "whatsapp_users"

    phone      = Column(String(20), primary_key=True, index=True)   # "919220313650"
    name       = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WhatsAppUser phone={self.phone} name={self.name}>"
