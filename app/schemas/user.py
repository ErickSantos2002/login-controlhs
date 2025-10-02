# app/schemas/user.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RoleOut(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }

class UserCreate(BaseModel):
    username: str
    password: str
    role_name: Optional[str] = None  # Novo campo opcional

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: Optional[datetime]
    role: Optional[RoleOut]

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role_name: Optional[str] = None