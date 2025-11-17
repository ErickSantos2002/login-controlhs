# app/api/baixas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.utils.db import get_db
from app.models.baixa import Baixa
from app.models.patrimonio import Patrimonio
from app.schemas.baixa import BaixaCreate, BaixaUpdate, BaixaOut, BaixaAprovar, BaixaRejeitar
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
    """
    Cria uma solicitação de baixa de patrimônio.

    ⚠️ IMPORTANTE:
    - A baixa é criada com status PENDENTE (aprovado_por = NULL, rejeitado_por = NULL)
    - O patrimônio NÃO muda de status imediatamente
    - Apenas após aprovação o patrimônio será marcado como "baixado"
    """
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == baixa_in.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado.")

    if patrimonio.status == "baixado":
        raise HTTPException(status_code=400, detail="Este patrimônio já foi baixado.")

    baixa = Baixa(**baixa_in.model_dump())
    db.add(baixa)
    db.commit()
    db.refresh(baixa)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Solicitação de Baixa de Patrimônio",
        entidade="baixas",
        entidade_id=baixa.id,
        usuario_id=current_user.id,
        detalhes={
            "patrimonio_id": baixa_in.patrimonio_id,
            "tipo": baixa_in.tipo,
            "motivo": baixa_in.motivo,
            "status": "PENDENTE"
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


# ===================== APROVAR =====================
@router.post("/{baixa_id}/aprovar", response_model=BaixaOut)
def aprovar_baixa(
    baixa_id: int,
    dados: BaixaAprovar,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aprova uma solicitação de baixa de patrimônio.

    ⚠️ PERMISSÕES:
    - Apenas usuários com role "Administrador" podem aprovar

    ⚠️ VALIDAÇÕES:
    - Não pode aprovar se já aprovada
    - Não pode aprovar se já rejeitada

    ✅ AÇÕES:
    - Marca aprovado_por = user_id atual
    - Marca data_aprovacao = timestamp atual
    - Salva observacoes se fornecido
    - ATUALIZA o patrimônio para status = "baixado"
    """
    # Validação 1: Apenas Administrador pode aprovar
    if current_user.role.name != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem aprovar baixas."
        )

    # Busca a baixa
    baixa = db.query(Baixa).filter(Baixa.id == baixa_id).first()
    if not baixa:
        raise HTTPException(status_code=404, detail="Baixa não encontrada.")

    # Validação 2: Não pode aprovar se já aprovada
    if baixa.aprovado_por is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta baixa já foi aprovada."
        )

    # Validação 3: Não pode aprovar se já rejeitada
    if baixa.rejeitado_por is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta baixa já foi rejeitada e não pode ser aprovada."
        )

    # Busca o patrimônio
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == baixa.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado.")

    # Atualiza a baixa
    baixa.aprovado_por = current_user.id
    baixa.data_aprovacao = datetime.utcnow()
    baixa.observacoes = dados.observacoes

    # Atualiza o status do patrimônio
    patrimonio.status = "baixado"

    db.commit()
    db.refresh(baixa)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Aprovação de Baixa",
        entidade="baixas",
        entidade_id=baixa.id,
        usuario_id=current_user.id,
        detalhes={
            "baixa_id": baixa_id,
            "patrimonio_id": baixa.patrimonio_id,
            "observacoes": dados.observacoes,
            "patrimonio_status": "baixado"
        }
    )

    return baixa


# ===================== REJEITAR =====================
@router.post("/{baixa_id}/rejeitar", response_model=BaixaOut)
def rejeitar_baixa(
    baixa_id: int,
    dados: BaixaRejeitar,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rejeita uma solicitação de baixa de patrimônio.

    ⚠️ PERMISSÕES:
    - Apenas usuários com role "Administrador" podem rejeitar

    ⚠️ VALIDAÇÕES:
    - Não pode rejeitar se já aprovada
    - Não pode rejeitar se já rejeitada

    ✅ AÇÕES:
    - Marca rejeitado_por = user_id atual
    - Marca data_rejeicao = timestamp atual
    - Salva motivo_rejeicao
    - NÃO altera o patrimônio
    """
    # Validação 1: Apenas Administrador pode rejeitar
    if current_user.role.name != "Administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem rejeitar baixas."
        )

    # Busca a baixa
    baixa = db.query(Baixa).filter(Baixa.id == baixa_id).first()
    if not baixa:
        raise HTTPException(status_code=404, detail="Baixa não encontrada.")

    # Validação 2: Não pode rejeitar se já aprovada
    if baixa.aprovado_por is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta baixa já foi aprovada e não pode ser rejeitada."
        )

    # Validação 3: Não pode rejeitar se já rejeitada
    if baixa.rejeitado_por is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta baixa já foi rejeitada."
        )

    # Atualiza a baixa
    baixa.rejeitado_por = current_user.id
    baixa.data_rejeicao = datetime.utcnow()
    baixa.motivo_rejeicao = dados.motivo_rejeicao

    db.commit()
    db.refresh(baixa)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Rejeição de Baixa",
        entidade="baixas",
        entidade_id=baixa.id,
        usuario_id=current_user.id,
        detalhes={
            "baixa_id": baixa_id,
            "patrimonio_id": baixa.patrimonio_id,
            "motivo_rejeicao": dados.motivo_rejeicao
        }
    )

    return baixa
