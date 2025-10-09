# app/api/transferencias.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.db import get_db
from app.models.transferencia import Transferencia
from app.models.patrimonio import Patrimonio
from app.schemas.transferencia import TransferenciaCreate, TransferenciaUpdate, TransferenciaOut
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/transferencias", tags=["Transferências"])

# ===================== CRIAR =====================
@router.post("/", response_model=TransferenciaOut)
def create_transferencia(
    transfer_in: TransferenciaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == transfer_in.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado.")

    transferencia = Transferencia(**transfer_in.model_dump())
    db.add(transferencia)

    # Atualiza o patrimônio com o novo setor e responsável, se informados
    if transfer_in.setor_destino_id:
        patrimonio.setor_id = transfer_in.setor_destino_id
    if transfer_in.responsavel_destino_id:
        patrimonio.responsavel_id = transfer_in.responsavel_destino_id

    db.commit()
    db.refresh(transferencia)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Transferência de Patrimônio",
        entidade="transferencias",
        entidade_id=transferencia.id,
        usuario_id=current_user.id,
        detalhes={
            "patrimonio_id": patrimonio.id,
            "origem_setor": transfer_in.setor_origem_id,
            "destino_setor": transfer_in.setor_destino_id,
            "responsavel_origem": transfer_in.responsavel_origem_id,
            "responsavel_destino": transfer_in.responsavel_destino_id,
            "motivo": transfer_in.motivo
        }
    )

    return transferencia


# ===================== LISTAR =====================
@router.get("/", response_model=List[TransferenciaOut])
def list_transferencias(db: Session = Depends(get_db)):
    return db.query(Transferencia).order_by(Transferencia.data_transferencia.desc()).all()


# ===================== DETALHAR =====================
@router.get("/{transferencia_id}", response_model=TransferenciaOut)
def get_transferencia(transferencia_id: int, db: Session = Depends(get_db)):
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    return transferencia


# ===================== ATUALIZAR =====================
@router.put("/{transferencia_id}", response_model=TransferenciaOut)
def update_transferencia(
    transferencia_id: int,
    transfer_in: TransferenciaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")

    for field, value in transfer_in.model_dump(exclude_unset=True).items():
        setattr(transferencia, field, value)

    db.commit()
    db.refresh(transferencia)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Atualização de Transferência",
        entidade="transferencias",
        entidade_id=transferencia.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": transfer_in.model_dump(exclude_unset=True)}
    )

    return transferencia


# ===================== EXCLUIR =====================
@router.delete("/{transferencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transferencia(
    transferencia_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")

    db.delete(transferencia)
    db.commit()

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Exclusão de Transferência",
        entidade="transferencias",
        entidade_id=transferencia_id,
        usuario_id=current_user.id,
        detalhes={"mensagem": f"Transferência {transferencia_id} removida"}
    )

    return None
