# app/utils/logs.py
from app.models.log_auditoria import LogAuditoria
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any

def registrar_log(
    db: Session,
    acao: str,
    entidade: str,
    entidade_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    detalhes: Optional[Any] = None
):
    """Registra uma ação no log de auditoria."""
    log = LogAuditoria(
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        usuario_id=usuario_id,
        detalhes=detalhes,
        criado_em=datetime.utcnow()
    )
    db.add(log)
    db.commit()
