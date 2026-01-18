import uuid
from pydantic import BaseModel, EmailStr
from app.db.models import UserRole

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True
