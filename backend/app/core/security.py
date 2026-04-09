# from passlib.context import CryptContext
# from datetime import datetime, timedelta
# from typing import Optional
# from jose import JWTError, jwt
# from app.core.config import settings

# # ✅ Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # def hash_password(password: str) -> str:
# #     """Hash a password"""
# #     return pwd_context.hash(password)

# # def verify_password(plain_password: str, hashed_password: str) -> bool:
# #     """Verify a password against its hash"""
# #     return pwd_context.verify(plain_password, hashed_password)
# def hash_password(password: str) -> str:
#     """Hash a password"""
#     return pwd_context.hash(password[:72])   # ✅ FIX

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """Verify a password against its hash"""
#     return pwd_context.verify(plain_password[:72], hashed_password)  # ✅ FIX

# # ✅ JWT Token
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     """Create JWT access token"""
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
#     return encoded_jwt

# def verify_token(token: str):
#     """Verify JWT token"""
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             return None
#         return username
#     except JWTError:
#         return None


from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings
import hashlib
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Password Hash
def hash_password(password: str) -> str:
    password = hashlib.sha256(password.encode()).hexdigest()
    return pwd_context.hash(password)

# ✅ Verify Password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    password = hashlib.sha256(plain_password.encode()).hexdigest()
    return pwd_context.verify(password, hashed_password)

# ✅ JWT Token
# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()

#     expire = datetime.utcnow() + (
#         expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     )

#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# # ✅ Verify Token
# def verify_token(token: str):
#     try:
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#         return payload
#     except JWTError:
#         return None





# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# # def verify_token(token: str):
# #     try:
# #         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

# #         username: str = payload.get("sub")   # ✅ IMPORTANT
# #         if username is None:
# #             return None

# #         return username   # ✅ return string only

# #     except JWTError:
# #         return None

# def verify_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         print("Decoded Payload:", payload)   # ✅ DEBUG

#         username = payload.get("sub")
#         return username

#     except Exception as e:
#         print("JWT ERROR:", str(e))   # ✅ DEBUG
#         return None


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload   # return full payload dict so callers can use .get("sub"), .get("is_admin") etc.
    except JWTError as e:
        print("JWT ERROR:", str(e))   # debug
        return None