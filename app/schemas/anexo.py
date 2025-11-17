# app/schemas/anexo.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnexoBase(BaseModel):
    patrimonio_id: Optional[int] = None
    baixa_id: Optional[int] = None
    tipo: str
    caminho_arquivo: str
    descricao: Optional[str] = None
    enviado_por: Optional[int] = None

class AnexoCreate(AnexoBase):
    pass

class AnexoUpdate(BaseModel):
    tipo: Optional[str] = None
    caminho_arquivo: Optional[str] = None
    descricao: Optional[str] = None

class AnexoOut(AnexoBase):
    id: int
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }