# # app/models/user.py

# from sqlalchemy import Column, Integer, String, DateTime
# from datetime import datetime

# from app.db.base_class import Base


# class User(Base):
#     __tablename__ = "users"

#     id              = Column(Integer, primary_key=True, index=True)
#     username        = Column(String(100), unique=True, index=True, nullable=False)
#     email           = Column(String(255), unique=True, index=True, nullable=False)
#     hashed_password = Column(String(255), nullable=False)
#     is_active       = Column(Integer, default=1)
#     is_admin        = Column(Integer, default=0)   # 1 = admin, 0 = regular user
#     created_at      = Column(DateTime, default=datetime.utcnow)
#     updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

#     def __repr__(self):
#         return f"<User(id={self.id}, username={self.username}, is_admin={self.is_admin})>"



from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True)   # ✅ FIX
    is_admin = Column(Boolean, default=False)   # ✅ FIX

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, is_admin={self.is_admin})>"