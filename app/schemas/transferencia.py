# app/schemas/transferencia.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransferenciaBase(BaseModel):
    patrimonio_id: int
    setor_origem_id: Optional[int] = None
    setor_destino_id: Optional[int] = None
    responsavel_origem_id: Optional[int] = None
    responsavel_destino_id: Optional[int] = None
    aprovado_por: Optional[int] = None
    motivo: Optional[str] = None

class TransferenciaCreate(TransferenciaBase):
    pass

class TransferenciaUpdate(BaseModel):
    setor_destino_id: Optional[int] = None
    responsavel_destino_id: Optional[int] = None
    aprovado_por: Optional[int] = None
    motivo: Optional[str] = None

class TransferenciaOut(TransferenciaBase):
    id: int
    data_transferencia: Optional[datetime]
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
