# from sqlalchemy.orm import Session
# from app.models.user import User
# from app.core.security import hash_password, verify_password
# from app.schemas.user import UserCreate, UserLogin

# class UserService:
#     """Service for user-related database operations"""
    
#     @staticmethod
#     def create_user(db: Session, user: UserCreate) -> User:
#         """Create a new user"""
#         hashed_password = hash_password(user.password)

#         db_user = User(
#             username=user.username,
#             email=user.email,
#             hashed_password=hashed_password,
#             is_active=True,       # ✅ ADD THIS
#             is_admin=False,       # ✅ ADD THIS
#             created_at=datetime.utcnow(),   # optional but good
#             updated_at=datetime.utcnow()    # optional but good
#         )

#         db.add(db_user)
#         db.commit()
#         db.refresh(db_user)
#         return db_user
    
#     @staticmethod
#     def get_user_by_username(db: Session, username: str) -> User:
#         """Get user by username"""
#         return db.query(User).filter(User.username == username).first()
    
#     @staticmethod
#     def get_user_by_email(db: Session, email: str) -> User:
#         """Get user by email"""
#         return db.query(User).filter(User.email == email).first()
    
#     @staticmethod
#     def authenticate_user(db: Session, username: str, password: str) -> User:
#         """Authenticate user by username and password"""
#         user = UserService.get_user_by_username(db, username)
#         if not user:
#             return None
#         if not verify_password(password, user.hashed_password):
#             return None
#         return user


from sqlalchemy.orm import Session
from datetime import datetime
from app.models.user import User
from app.core.security import hash_password, verify_password

# class UserService:

#     @staticmethod
#     def create_user(db: Session, user):
#         hashed_password = hash_password(user.password)

#         db_user = User(
#             username=user.username,
#             email=user.email,
#             hashed_password=hashed_password,
#             is_active=True,
#             is_admin=False,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow()
#         )

#         db.add(db_user)
#         db.commit()
#         db.refresh(db_user)
#         return db_user

#     @staticmethod
#     def get_user_by_username(db: Session, username: str):
#         return db.query(User).filter(User.username == username).first()

#     @staticmethod
#     def authenticate_user(db: Session, username: str, password: str):
#         user = UserService.get_user_by_username(db, username)

#         if not user:
#             return None

#         if not verify_password(password, user.hashed_password):
#             return None

#         if not user.is_active:
#             return None

#         return user


class UserService:

    @staticmethod
    def create_user(db: Session, user):
        hashed_password = hash_password(user.password)

        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_username(db, username):
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str):   # ✅ ADD THIS
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        user = UserService.get_user_by_username(db, username)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user
