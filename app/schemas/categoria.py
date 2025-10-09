# app/schemas/categoria.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CategoriaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None

class CategoriaOut(CategoriaBase):
    id: int
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
