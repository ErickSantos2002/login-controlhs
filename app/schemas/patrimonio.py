# app/schemas/patrimonio.py
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class PatrimonioBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    numero_serie: Optional[str] = None
    categoria_id: Optional[int] = None
    setor_id: Optional[int] = None
    responsavel_id: Optional[int] = None
    data_aquisicao: Optional[date] = None
    valor_aquisicao: Optional[float] = None
    valor_atual: Optional[float] = None
    status: Optional[str] = "ativo"

class PatrimonioCreate(PatrimonioBase):
    pass

class PatrimonioUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    numero_serie: Optional[str] = None
    categoria_id: Optional[int] = None
    setor_id: Optional[int] = None
    responsavel_id: Optional[int] = None
    data_aquisicao: Optional[date] = None
    valor_aquisicao: Optional[float] = None
    valor_atual: Optional[float] = None
    status: Optional[str] = None

class PatrimonioOut(PatrimonioBase):
    id: int
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
