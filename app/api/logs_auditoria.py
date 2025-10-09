# app/api/logs_auditoria.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.utils.db import get_db
from app.models.log_auditoria import LogAuditoria
from app.schemas.log_auditoria import LogAuditoriaCreate, LogAuditoriaOut

router = APIRouter(prefix="/logs", tags=["Logs de Auditoria"])

@router.post("/", response_model=LogAuditoriaOut)
def create_log(log_in: LogAuditoriaCreate, db: Session = Depends(get_db)):
    log = LogAuditoria(**log_in.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

@router.get("/", response_model=List[LogAuditoriaOut])
def list_logs(db: Session = Depends(get_db)):
    """Lista todos os logs de auditoria."""
    return db.query(LogAuditoria).order_by(LogAuditoria.criado_em.desc()).all()

@router.get("/{log_id}", response_model=LogAuditoriaOut)
def get_log(log_id: int, db: Session = Depends(get_db)):
    """Busca um log de auditoria específico."""
    log = db.query(LogAuditoria).filter(LogAuditoria.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado.")
    return log
