# app/schemas/setor.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SetorBase(BaseModel):
    nome: str
    descricao: Optional[str] = None

class SetorCreate(SetorBase):
    pass

class SetorUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None

class SetorOut(SetorBase):
    id: int
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
