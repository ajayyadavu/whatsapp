# app/db/base_class.py
# Single source of truth for SQLAlchemy Base.
# Models import from HERE — never from app.db.base (which imports models back).

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
