# app/api/inventarios.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.db import get_db
from app.models.inventario import Inventario
from app.models.patrimonio import Patrimonio
from app.schemas.inventario import InventarioCreate, InventarioUpdate, InventarioOut
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/inventarios", tags=["Inventários"])

# ===================== CRIAR =====================
@router.post("/", response_model=InventarioOut)
def create_inventario(
    inventario_in: InventarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == inventario_in.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado.")

    inventario = Inventario(**inventario_in.model_dump())
    db.add(inventario)
    db.commit()
    db.refresh(inventario)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Registro de Inventário",
        entidade="inventarios",
        entidade_id=inventario.id,
        usuario_id=current_user.id,
        detalhes={
            "patrimonio_id": inventario_in.patrimonio_id,
            "situacao": inventario_in.situacao,
            "observacoes": inventario_in.observacoes
        }
    )

    return inventario


# ===================== LISTAR =====================
@router.get("/", response_model=List[InventarioOut])
def list_inventarios(db: Session = Depends(get_db)):
    """Lista todos os registros de inventário."""
    return db.query(Inventario).order_by(Inventario.data_verificacao.desc()).all()


# ===================== DETALHAR =====================
@router.get("/{inventario_id}", response_model=InventarioOut)
def get_inventario(inventario_id: int, db: Session = Depends(get_db)):
    """Obtém um registro de inventário específico."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado.")
    return inventario


# ===================== ATUALIZAR =====================
@router.put("/{inventario_id}", response_model=InventarioOut)
def update_inventario(
    inventario_id: int,
    inventario_in: InventarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza informações de um registro de inventário."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado.")

    for field, value in inventario_in.model_dump(exclude_unset=True).items():
        setattr(inventario, field, value)

    db.commit()
    db.refresh(inventario)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Atualização de Inventário",
        entidade="inventarios",
        entidade_id=inventario.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": inventario_in.model_dump(exclude_unset=True)}
    )

    return inventario


# ===================== EXCLUIR =====================
@router.delete("/{inventario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventario(
    inventario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove um registro de inventário."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado.")

    db.delete(inventario)
    db.commit()

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Exclusão de Inventário",
        entidade="inventarios",
        entidade_id=inventario_id,
        usuario_id=current_user.id,
        detalhes={"mensagem": f"Inventário {inventario_id} excluído"}
    )

    return None
