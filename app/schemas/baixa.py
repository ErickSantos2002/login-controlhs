# app/schemas/baixa.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaixaBase(BaseModel):
    patrimonio_id: int
    tipo: str
    motivo: Optional[str] = None

class BaixaCreate(BaixaBase):
    pass

class BaixaUpdate(BaseModel):
    tipo: Optional[str] = None
    motivo: Optional[str] = None

class BaixaAprovar(BaseModel):
    observacoes: Optional[str] = None

class BaixaRejeitar(BaseModel):
    motivo_rejeicao: str

class BaixaOut(BaixaBase):
    id: int
    data_baixa: Optional[datetime]

    # Campos de aprovação
    aprovado_por: Optional[int] = None
    data_aprovacao: Optional[datetime] = None
    observacoes: Optional[str] = None

    # Campos de rejeição
    rejeitado_por: Optional[int] = None
    data_rejeicao: Optional[datetime] = None
    motivo_rejeicao: Optional[str] = None

    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
