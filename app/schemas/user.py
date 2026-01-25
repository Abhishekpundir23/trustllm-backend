from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 👇 NEW: Schema for updating keys
class UserKeysUpdate(BaseModel):
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    gemini_key: Optional[str] = None

# 👇 NEW: User Profile Response
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    # We return booleans so the frontend knows keys exist
    has_openai: bool = False
    has_anthropic: bool = False
    has_gemini: bool = False

    class Config:
        from_attributes = True