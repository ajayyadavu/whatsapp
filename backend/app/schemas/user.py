# from pydantic import BaseModel, EmailStr
# from typing import Optional
# from datetime import datetime

# # Request schemas
# class UserCreate(BaseModel):
#     username: str
#     email: EmailStr
#     password: str
#     is_admin: Optional[int] = 0

# class UserLogin(BaseModel):
#     username: str
#     password: str

# # Response schemas
# class UserResponse(BaseModel):
#     id: int
#     username: str
#     email: str
#     is_active: int
#     is_admin: int = 0
#     created_at: datetime

#     class Config:
#         from_attributes = True

# class TokenResponse(BaseModel):
#     access_token: str
#     token_type: str
#     user: UserResponse

# class TokenData(BaseModel):
#     username: Optional[str] = None



from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime
import re

# Request schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: Optional[bool] = False   # ✅ FIX

    @validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Min 8 characters required")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Must contain 1 uppercase letter")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Must contain 1 special character")

        if not re.search(r"\d", value):
            raise ValueError("Must contain 1 number")

        return value


class UserLogin(BaseModel):
    username: str
    password: str


# Response schemas
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool          # ✅ FIX
    is_admin: bool           # ✅ FIX
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None