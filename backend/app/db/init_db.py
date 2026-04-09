from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.base import Base
from app.services.user_service import UserService
from app.schemas.user import UserCreate

def init_db(db: Session) -> None:
    """Initialize database by creating all tables and optional seed data"""
    # ✅ Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    
    # ✅ Optional: Create default user for testing
    # existing_user = UserService.get_user_by_username(db, "admin")
    # if not existing_user:
    #     admin = UserCreate(
    #         username="admin",
    #         email="admin@example.com",
    #         password="admin123"
    #     )
    #     UserService.create_user(db, admin)
    #     print("✅ Admin user created")

if __name__ == "__main__":
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
