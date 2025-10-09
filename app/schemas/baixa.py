# app/schemas/baixa.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BaixaBase(BaseModel):
    patrimonio_id: int
    tipo: str
    motivo: Optional[str] = None
    aprovado_por: Optional[int] = None
    documento_anexo: Optional[str] = None

class BaixaCreate(BaixaBase):
    pass

class BaixaUpdate(BaseModel):
    tipo: Optional[str] = None
    motivo: Optional[str] = None
    aprovado_por: Optional[int] = None
    documento_anexo: Optional[str] = None

class BaixaOut(BaixaBase):
    id: int
    data_baixa: Optional[datetime]
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
