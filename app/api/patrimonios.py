# app/api/patrimonios.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.db import get_db
from app.models.patrimonio import Patrimonio
from app.schemas.patrimonio import PatrimonioCreate, PatrimonioUpdate, PatrimonioOut
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/patrimonios", tags=["Patrimônios"])

# ===================== CRIAR =====================
@router.post("/", response_model=PatrimonioOut)
def create_patrimonio(
    patrimonio_in: PatrimonioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patrimonio = Patrimonio(**patrimonio_in.model_dump())
    db.add(patrimonio)
    db.commit()
    db.refresh(patrimonio)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Criação de Patrimônio",
        entidade="patrimonios",
        entidade_id=patrimonio.id,
        usuario_id=current_user.id,
        detalhes={"dados": patrimonio_in.model_dump()}
    )

    return patrimonio


# ===================== LISTAR =====================
@router.get("/", response_model=List[PatrimonioOut])
def list_patrimonios(db: Session = Depends(get_db)):
    return db.query(Patrimonio).all()


# ===================== DETALHAR =====================
@router.get("/{patrimonio_id}", response_model=PatrimonioOut)
def get_patrimonio(patrimonio_id: int, db: Session = Depends(get_db)):
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado")
    return patrimonio


# ===================== ATUALIZAR =====================
@router.put("/{patrimonio_id}", response_model=PatrimonioOut)
def update_patrimonio(
    patrimonio_id: int,
    patrimonio_in: PatrimonioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado")

    for field, value in patrimonio_in.model_dump(exclude_unset=True).items():
        setattr(patrimonio, field, value)

    db.commit()
    db.refresh(patrimonio)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Atualização de Patrimônio",
        entidade="patrimonios",
        entidade_id=patrimonio.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": patrimonio_in.model_dump(exclude_unset=True)}
    )

    return patrimonio


# ===================== EXCLUIR =====================
@router.delete("/{patrimonio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patrimonio(
    patrimonio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado")

    db.delete(patrimonio)
    db.commit()

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Exclusão de Patrimônio",
        entidade="patrimonios",
        entidade_id=patrimonio_id,
        usuario_id=current_user.id,
        detalhes={"mensagem": f"Patrimônio {patrimonio_id} excluído"}
    )

    return None
