import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr, Field

# ── Request Schemas ──


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Response Schemas ──


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleOut(BaseModel):
    id: int
    role_name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    roles: List[RoleOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
