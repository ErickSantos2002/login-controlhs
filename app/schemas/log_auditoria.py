# app/schemas/log_auditoria.py
from pydantic import BaseModel, Field
from typing import Optional, Any, List
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
    usuario: Optional[str] = None  # Nome do usuário que executou a ação
    criado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }

class LogAuditoriaListResponse(BaseModel):
    """Resposta paginada da lista de logs"""
    total: int = Field(..., description="Total de logs que correspondem aos filtros")
    pagina: int = Field(..., description="Página atual")
    limite: int = Field(..., description="Itens por página")
    logs: List[LogAuditoriaOut] = Field(..., description="Lista de logs")
