from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional


class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    nickname: str
    discord: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    name: Optional[str] = None
    nickname: Optional[str] = None
    discord: Optional[str] = None
    is_active: bool
    role: str
    scopes: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    discord: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class TokenData(BaseModel):
    sub: str
    exp: int
    role: str
    scopes: List[str]
    id: Optional[int] = None
