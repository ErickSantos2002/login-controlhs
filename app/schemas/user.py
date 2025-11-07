# app/schemas/user.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ========================================
# SCHEMAS DE SUPORTE
# ========================================

class RoleOut(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }

class SetorOut(BaseModel):
    """Schema simplificado de Setor para evitar imports circulares"""
    id: int
    nome: str

    model_config = {
        "from_attributes": True
    }

# ========================================
# SCHEMAS DE USER
# ========================================

class UserCreate(BaseModel):
    username: str
    password: str
    role_name: Optional[str] = None
    setor_id: Optional[int] = None  # 🆕 NOVO CAMPO
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "joao.silva",
                "password": "senha123",
                "role_name": "Gestor",
                "setor_id": 1
            }
        }

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    created_at: Optional[datetime]
    role: Optional[RoleOut]
    setor_id: Optional[int] = None  # 🆕 NOVO CAMPO
    setor: Optional[SetorOut] = None  # 🆕 NOVO CAMPO (objeto completo)

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role_name: Optional[str] = None
    setor_id: Optional[int] = None  # 🆕 NOVO CAMPO