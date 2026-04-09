# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from datetime import timedelta
# from app.db.session import get_db
# from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
# from app.services.user_service import UserService
# from app.core.security import create_access_token
# from app.core.config import settings

# router = APIRouter(prefix="/auth", tags=["auth"])

# @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# def register(user: UserCreate, db: Session = Depends(get_db)):
#     """Register a new user"""
#     # ✅ Check if username already exists
#     existing_user = UserService.get_user_by_username(db, user.username)
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Username already registered"
#         )
    
#     # ✅ Check if email already exists
#     existing_email = UserService.get_user_by_email(db, user.email)
#     if existing_email:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     # ✅ Create user
#     return UserService.create_user(db, user)

# @router.post("/login", response_model=TokenResponse)
# def login(user: UserLogin, db: Session = Depends(get_db)):
#     """Login user and return access token"""
#     # ✅ Authenticate user
#     db_user = UserService.authenticate_user(db, user.username, user.password)
#     if not db_user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
    
#     # ✅ Create access token
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": db_user.username}, 
#         expires_delta=access_token_expires
#     )
    
#     user_response = UserResponse.from_orm(db_user)
    
#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": user_response
#     }

# @router.get("/me", response_model=UserResponse)
# def get_current_user(token: str = None, db: Session = Depends(get_db)):
#     """Get current logged-in user info"""
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated"
#         )
    
#     # ✅ Verify token and get username
#     from app.core.security import verify_token
#     username = verify_token(token)
#     if not username:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token"
#         )
    
#     user = UserService.get_user_by_username(db, username)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="User not found"
#         )
    
#     return UserResponse.from_orm(user)



from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse
from app.services.user_service import UserService
from app.core.security import create_access_token, verify_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# ✅ OAuth2 scheme (token from header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ===========================
# ✅ REGISTER
# ===========================
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""

    # Check username
    existing_user = UserService.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check email
    existing_email = UserService.get_user_by_email(db, user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    return UserService.create_user(db, user)


# ===========================
# ✅ LOGIN
# ===========================
@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""

    db_user = UserService.authenticate_user(db, user.username, user.password)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token with role
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={
            "sub": db_user.username,
            "is_admin": db_user.is_admin   # ✅ role included
        },
        expires_delta=access_token_expires
    )

    user_response = UserResponse.from_orm(db_user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }


# ===========================
# ✅ GET CURRENT USER (/me)
# ===========================
@router.get("/me", response_model=UserResponse)
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current logged-in user"""

    payload = verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    username = payload.get("sub")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = UserService.get_user_by_username(db, username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)


# ===========================
# 🔐 OPTIONAL: ADMIN CHECK
# ===========================
def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Only admin can access"""

    payload = verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    username = payload.get("sub")
    user = UserService.get_user_by_username(db, username)

    return user