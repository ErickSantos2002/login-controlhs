# app/schemas/log_auditoria.py
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class LogAuditoriaBase(BaseModel):
    acao: str
    entidade: str
    entidade_id: Optional[int] = None
    usuario_id: Optional[int] = None
    detalhes: Optional[Any] = None  # JSON dinâmico

class LogAuditoriaCreate(LogAuditoriaBase):
    pass

class LogAuditoriaOut(LogAuditoriaBase):
    id: int
    criado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
