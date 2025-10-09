# app/api/baixas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.db import get_db
from app.models.baixa import Baixa
from app.models.patrimonio import Patrimonio
from app.schemas.baixa import BaixaCreate, BaixaUpdate, BaixaOut
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/baixas", tags=["Baixas"])

# ===================== CRIAR =====================
@router.post("/", response_model=BaixaOut)
def create_baixa(
    baixa_in: BaixaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == baixa_in.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado.")

    if patrimonio.status == "baixado":
        raise HTTPException(status_code=400, detail="Este patrimônio já foi baixado.")

    baixa = Baixa(**baixa_in.model_dump())
    db.add(baixa)

    # Atualiza o status do patrimônio
    patrimonio.status = "baixado"
    db.commit()
    db.refresh(baixa)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Baixa de Patrimônio",
        entidade="baixas",
        entidade_id=baixa.id,
        usuario_id=current_user.id,
        detalhes={
            "patrimonio_id": baixa_in.patrimonio_id,
            "tipo": baixa_in.tipo,
            "motivo": baixa_in.motivo,
            "documento": baixa_in.documento_anexo
        }
    )

    return baixa


# ===================== LISTAR =====================
@router.get("/", response_model=List[BaixaOut])
def list_baixas(db: Session = Depends(get_db)):
    return db.query(Baixa).order_by(Baixa.data_baixa.desc()).all()


# ===================== DETALHAR =====================
@router.get("/{baixa_id}", response_model=BaixaOut)
def get_baixa(baixa_id: int, db: Session = Depends(get_db)):
    baixa = db.query(Baixa).filter(Baixa.id == baixa_id).first()
    if not baixa:
        raise HTTPException(status_code=404, detail="Baixa não encontrada.")
    return baixa


# ===================== ATUALIZAR =====================
@router.put("/{baixa_id}", response_model=BaixaOut)
def update_baixa(
    baixa_id: int,
    baixa_in: BaixaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    baixa = db.query(Baixa).filter(Baixa.id == baixa_id).first()
    if not baixa:
        raise HTTPException(status_code=404, detail="Baixa não encontrada.")

    for field, value in baixa_in.model_dump(exclude_unset=True).items():
        setattr(baixa, field, value)

    db.commit()
    db.refresh(baixa)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Atualização de Baixa",
        entidade="baixas",
        entidade_id=baixa.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": baixa_in.model_dump(exclude_unset=True)}
    )

    return baixa


# ===================== EXCLUIR =====================
@router.delete("/{baixa_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_baixa(
    baixa_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    baixa = db.query(Baixa).filter(Baixa.id == baixa_id).first()
    if not baixa:
        raise HTTPException(status_code=404, detail="Baixa não encontrada.")

    db.delete(baixa)
    db.commit()

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Exclusão de Baixa",
        entidade="baixas",
        entidade_id=baixa_id,
        usuario_id=current_user.id,
        detalhes={"mensagem": f"Baixa {baixa_id} removida"}
    )

    return None
