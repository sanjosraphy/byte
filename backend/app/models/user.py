"""User-related Pydantic models."""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class UserRegisterRequest(BaseModel):
    """User registration request."""
    username: str
    email: EmailStr
    password: str
    full_name: str


class UserLoginRequest(BaseModel):
    """User login request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class UserResponse(BaseModel):
    """User response."""
    id: int
    username: str
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True
