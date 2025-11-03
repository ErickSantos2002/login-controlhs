# app/utils/logs.py
from app.models.log_auditoria import LogAuditoria
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any


def converter_para_json_serializavel(data: Any) -> Any:
    """
    Converte recursivamente um objeto para um formato JSON-serializável.
    
    Trata especialmente:
    - datetime/date -> string ISO format
    - Decimal -> float
    - dict -> processa recursivamente
    - list -> processa recursivamente
    """
    if data is None:
        return None
    
    if isinstance(data, dict):
        return {key: converter_para_json_serializavel(value) for key, value in data.items()}
    
    if isinstance(data, list):
        return [converter_para_json_serializavel(item) for item in data]
    
    if isinstance(data, (datetime, date)):
        return data.isoformat()
    
    if isinstance(data, Decimal):
        return float(data)
    
    # Para outros tipos, retorna como está
    return data


def registrar_log(
    db: Session,
    acao: str,
    entidade: str,
    entidade_id: Optional[int] = None,
    usuario_id: Optional[int] = None,
    detalhes: Optional[Any] = None
):
    """
    Registra uma ação no log de auditoria.
    
    Args:
        db: Sessão do banco de dados
        acao: Descrição da ação realizada
        entidade: Nome da entidade (tabela) afetada
        entidade_id: ID do registro afetado (opcional)
        usuario_id: ID do usuário que realizou a ação (opcional)
        detalhes: Dicionário com detalhes adicionais (será convertido para JSON)
    """
    try:
        # Converter detalhes para formato JSON-serializável
        detalhes_serializaveis = converter_para_json_serializavel(detalhes) if detalhes else None
        
        # Criar o log
        log = LogAuditoria(
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            usuario_id=usuario_id,
            detalhes=detalhes_serializaveis,
            criado_em=datetime.utcnow()
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        return log
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao registrar log: {e}")
        # Não propaga o erro para não quebrar a operação principal
        return None