# app/api/logs_auditoria.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import List, Optional
from datetime import datetime
from app.utils.db import get_db
from app.models.log_auditoria import LogAuditoria
from app.models.user import User
from app.schemas.log_auditoria import LogAuditoriaCreate, LogAuditoriaOut, LogAuditoriaListResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/logs", tags=["Logs de Auditoria"])

@router.post("/", response_model=LogAuditoriaOut)
def create_log(log_in: LogAuditoriaCreate, db: Session = Depends(get_db)):
    log = LogAuditoria(**log_in.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@router.get("/", response_model=LogAuditoriaListResponse)
def list_logs(
    skip: int = Query(0, ge=0, description="Número de registros a pular (offset)"),
    limit: int = Query(50, ge=1, le=100, description="Número de registros por página (max 100)"),
    entidade: Optional[str] = Query(None, description="Filtrar por entidade (ex: patrimonios, users)"),
    acao: Optional[str] = Query(None, description="Filtrar por ação (ex: Criação, Atualização)"),
    usuario: Optional[str] = Query(None, description="Filtrar por nome de usuário"),
    data_inicio: Optional[str] = Query(None, description="Data inicial (formato: YYYY-MM-DD)"),
    data_fim: Optional[str] = Query(None, description="Data final (formato: YYYY-MM-DD)"),
    busca: Optional[str] = Query(None, description="Busca geral (ação, entidade ou usuário)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista logs de auditoria com paginação e filtros avançados.

    - **skip**: Registros a pular (para paginação)
    - **limit**: Registros por página (máx 100)
    - **entidade**: Filtrar por tipo de entidade
    - **acao**: Filtrar por ação realizada
    - **usuario**: Filtrar por nome do usuário
    - **data_inicio/data_fim**: Filtrar por período
    - **busca**: Busca geral em ação, entidade e usuário
    """
    # Query base com join para carregar usuário
    query = db.query(LogAuditoria).options(joinedload(LogAuditoria.usuario_rel))

    # Aplicar filtros
    if entidade:
        query = query.filter(LogAuditoria.entidade.ilike(f"%{entidade}%"))

    if acao:
        query = query.filter(LogAuditoria.acao.ilike(f"%{acao}%"))

    if usuario:
        query = query.join(User, LogAuditoria.usuario_id == User.id).filter(
            User.username.ilike(f"%{usuario}%")
        )

    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(LogAuditoria.criado_em >= data_inicio_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data_inicio inválido. Use YYYY-MM-DD")

    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
            # Adicionar 1 dia para incluir todo o dia final
            from datetime import timedelta
            data_fim_dt = data_fim_dt + timedelta(days=1)
            query = query.filter(LogAuditoria.criado_em < data_fim_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data_fim inválido. Use YYYY-MM-DD")

    if busca:
        # Busca geral em ação, entidade ou username
        query = query.outerjoin(User, LogAuditoria.usuario_id == User.id).filter(
            or_(
                LogAuditoria.acao.ilike(f"%{busca}%"),
                LogAuditoria.entidade.ilike(f"%{busca}%"),
                User.username.ilike(f"%{busca}%")
            )
        )

    # Contar total antes de paginar
    total = query.count()

    # Aplicar paginação e ordenação
    logs = query.order_by(LogAuditoria.criado_em.desc()).offset(skip).limit(limit).all()

    return LogAuditoriaListResponse(
        total=total,
        pagina=(skip // limit) + 1,
        limite=limit,
        logs=logs
    )

@router.get("/{log_id}", response_model=LogAuditoriaOut)
def get_log(log_id: int, db: Session = Depends(get_db)):
    """Busca um log de auditoria específico."""
    log = db.query(LogAuditoria).filter(LogAuditoria.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado.")
    return log
