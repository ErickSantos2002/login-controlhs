# app/api/transferencias.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.utils.db import get_db
from app.models.transferencia import Transferencia
from app.models.patrimonio import Patrimonio
from app.schemas.transferencia import (
    TransferenciaCreate, 
    TransferenciaUpdate, 
    TransferenciaOut,
    TransferenciaAprovar,
    TransferenciaRejeitar
)
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/transferencias", tags=["Transferências"])


# ========================================
# CRIAR TRANSFERÊNCIA
# ========================================
@router.post("/", response_model=TransferenciaOut)
def create_transferencia(
    transfer_in: TransferenciaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria uma nova solicitação de transferência.
    
    ⚠️ REGRAS:
    - Usuários comuns só podem transferir patrimônios dos quais são responsáveis
    - Administradores e gestores podem transferir qualquer patrimônio
    - O solicitante_id é preenchido automaticamente com o usuário logado
    - O patrimônio NÃO é atualizado automaticamente (precisa de aprovação)
    """
    
    # Busca o patrimônio
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == transfer_in.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado.")
    
    # 🆕 VALIDAÇÃO: Verifica permissão do usuário
    user_role = current_user.role.name.lower() if current_user.role else "usuario"
    
    # Usuários comuns só podem transferir seus próprios patrimônios
    if user_role not in ["administrador", "gestor"]:
        if patrimonio.responsavel_id != current_user.id:
            raise HTTPException(
                status_code=403, 
                detail="Você só pode solicitar transferência de patrimônios pelos quais é responsável."
            )
    
    # 🆕 Valida que pelo menos setor OU responsável deve mudar
    setor_muda = transfer_in.setor_destino_id and transfer_in.setor_destino_id != patrimonio.setor_id
    responsavel_muda = transfer_in.responsavel_destino_id and transfer_in.responsavel_destino_id != patrimonio.responsavel_id
    
    if not setor_muda and not responsavel_muda:
        raise HTTPException(
            status_code=400,
            detail="Pelo menos o setor ou o responsável deve ser diferente do atual."
        )
    
    # 🆕 Verifica se já existe transferência pendente para este patrimônio
    transferencia_pendente = db.query(Transferencia).filter(
        Transferencia.patrimonio_id == transfer_in.patrimonio_id,
        Transferencia.aprovado_por.is_(None),
        Transferencia.motivo_rejeicao.is_(None)
    ).first()
    
    if transferencia_pendente:
        raise HTTPException(
            status_code=400,
            detail=f"Já existe uma transferência pendente (#{transferencia_pendente.id}) para este patrimônio."
        )
    
    # Cria a transferência
    transferencia_data = transfer_in.model_dump()
    
    # 🆕 Preenche automaticamente o solicitante_id
    transferencia_data["solicitante_id"] = current_user.id
    
    # 🆕 Se não informou origem, pega do patrimônio atual
    if not transferencia_data.get("setor_origem_id"):
        transferencia_data["setor_origem_id"] = patrimonio.setor_id
    if not transferencia_data.get("responsavel_origem_id"):
        transferencia_data["responsavel_origem_id"] = patrimonio.responsavel_id
    
    transferencia = Transferencia(**transferencia_data)
    db.add(transferencia)
    
    # ⚠️ NÃO ATUALIZA O PATRIMÔNIO AQUI - só após aprovação e efetivação
    
    db.commit()
    db.refresh(transferencia)
    
    # Log automático
    registrar_log(
        db=db,
        acao="Solicitação de Transferência",
        entidade="transferencias",
        entidade_id=transferencia.id,
        usuario_id=current_user.id,
        detalhes={
            "patrimonio_id": patrimonio.id,
            "patrimonio_nome": patrimonio.nome,
            "origem_setor": transfer_in.setor_origem_id,
            "destino_setor": transfer_in.setor_destino_id,
            "responsavel_origem": transfer_in.responsavel_origem_id,
            "responsavel_destino": transfer_in.responsavel_destino_id,
            "motivo": transfer_in.motivo
        }
    )
    
    return transferencia


# ========================================
# LISTAR TRANSFERÊNCIAS
# ========================================
@router.get("/", response_model=List[TransferenciaOut])
def list_transferencias(db: Session = Depends(get_db)):
    """Lista todas as transferências ordenadas por data de criação (mais recentes primeiro)"""
    return db.query(Transferencia).order_by(Transferencia.criado_em.desc()).all()


# ========================================
# DETALHAR TRANSFERÊNCIA
# ========================================
@router.get("/{transferencia_id}", response_model=TransferenciaOut)
def get_transferencia(transferencia_id: int, db: Session = Depends(get_db)):
    """Obtém detalhes de uma transferência específica"""
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    return transferencia


# ========================================
# 🆕 APROVAR TRANSFERÊNCIA
# ========================================
@router.post("/{transferencia_id}/aprovar", response_model=TransferenciaOut)
def aprovar_transferencia(
    transferencia_id: int,
    aprovacao: TransferenciaAprovar,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aprova uma transferência pendente.
    
    ⚠️ REGRAS:
    - Apenas gestores e administradores podem aprovar
    - Gestores só aprovam transferências do seu setor (origem ou destino)
    - Após aprovação, pode efetivar automaticamente se solicitado
    """
    
    # Busca a transferência
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    
    # Verifica se já foi aprovada ou rejeitada
    if transferencia.aprovado_por:
        if transferencia.motivo_rejeicao:
            raise HTTPException(status_code=400, detail="Esta transferência já foi rejeitada.")
        else:
            raise HTTPException(status_code=400, detail="Esta transferência já foi aprovada.")
    
    # Verifica permissão
    user_role = current_user.role.name.lower() if current_user.role else "usuario"
    
    if user_role not in ["administrador", "gestor"]:
        raise HTTPException(status_code=403, detail="Apenas gestores e administradores podem aprovar transferências.")
    
    # Gestor só pode aprovar do seu setor
    if user_role == "gestor":
        user_setor_id = current_user.setor_id
        if user_setor_id not in [transferencia.setor_origem_id, transferencia.setor_destino_id]:
            raise HTTPException(
                status_code=403,
                detail="Você só pode aprovar transferências relacionadas ao seu setor."
            )
    
    # Aprova a transferência
    transferencia.aprovado_por = current_user.id
    transferencia.data_aprovacao = datetime.now()
    transferencia.observacoes = aprovacao.observacoes
    
    db.commit()
    db.refresh(transferencia)
    
    # Log de aprovação
    registrar_log(
        db=db,
        acao="Aprovação de Transferência",
        entidade="transferencias",
        entidade_id=transferencia.id,
        usuario_id=current_user.id,
        detalhes={
            "observacoes": aprovacao.observacoes,
            "efetivar_automaticamente": aprovacao.efetivar_automaticamente
        }
    )
    
    # Efetiva automaticamente se solicitado
    if aprovacao.efetivar_automaticamente:
        return efetivar_transferencia(transferencia_id, db, current_user)
    
    return transferencia


# ========================================
# 🆕 REJEITAR TRANSFERÊNCIA
# ========================================
@router.post("/{transferencia_id}/rejeitar", response_model=TransferenciaOut)
def rejeitar_transferencia(
    transferencia_id: int,
    rejeicao: TransferenciaRejeitar,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rejeita uma transferência pendente.
    
    ⚠️ REGRAS:
    - Apenas gestores e administradores podem rejeitar
    - Motivo de rejeição é obrigatório
    - Transferências rejeitadas NÃO podem ser efetivadas
    """
    
    # Busca a transferência
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    
    # Verifica se já foi processada
    if transferencia.aprovado_por or transferencia.motivo_rejeicao:
        raise HTTPException(status_code=400, detail="Esta transferência já foi processada.")
    
    # Verifica permissão
    user_role = current_user.role.name.lower() if current_user.role else "usuario"
    
    if user_role not in ["administrador", "gestor"]:
        raise HTTPException(status_code=403, detail="Apenas gestores e administradores podem rejeitar transferências.")
    
    # Gestor só pode rejeitar do seu setor
    if user_role == "gestor":
        user_setor_id = current_user.setor_id
        if user_setor_id not in [transferencia.setor_origem_id, transferencia.setor_destino_id]:
            raise HTTPException(
                status_code=403,
                detail="Você só pode rejeitar transferências relacionadas ao seu setor."
            )
    
    # 🆕 Rejeita sem preencher aprovado_por
    transferencia.motivo_rejeicao = rejeicao.motivo_rejeicao
    transferencia.data_aprovacao = datetime.now()  # Data da decisão
    
    db.commit()
    db.refresh(transferencia)
    
    # Log de rejeição
    registrar_log(
        db=db,
        acao="Rejeição de Transferência",
        entidade="transferencias",
        entidade_id=transferencia.id,
        usuario_id=current_user.id,
        detalhes={"motivo_rejeicao": rejeicao.motivo_rejeicao}
    )
    
    return transferencia


# ========================================
# 🆕 EFETIVAR TRANSFERÊNCIA
# ========================================
@router.post("/{transferencia_id}/efetivar", response_model=TransferenciaOut)
def efetivar_transferencia(
    transferencia_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Efetiva uma transferência aprovada, atualizando o patrimônio.
    
    ⚠️ REGRAS:
    - Apenas transferências aprovadas podem ser efetivadas
    - Transferências rejeitadas NÃO podem ser efetivadas
    - Transferências já efetivadas não podem ser efetivadas novamente
    - Atualiza o setor e/ou responsável do patrimônio
    """
    
    # Busca a transferência
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    
    # Verifica se foi rejeitada
    if transferencia.motivo_rejeicao:
        raise HTTPException(status_code=400, detail="Transferências rejeitadas não podem ser efetivadas.")
    
    # Verifica se foi aprovada
    if not transferencia.aprovado_por:
        raise HTTPException(status_code=400, detail="Apenas transferências aprovadas podem ser efetivadas.")
    
    # Verifica se já foi efetivada
    if transferencia.efetivada:
        raise HTTPException(status_code=400, detail="Esta transferência já foi efetivada.")
    
    # Verifica permissão
    user_role = current_user.role.name.lower() if current_user.role else "usuario"
    if user_role not in ["administrador", "gestor"]:
        raise HTTPException(status_code=403, detail="Apenas gestores e administradores podem efetivar transferências.")
    
    # Busca o patrimônio
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == transferencia.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado.")
    
    # 🆕 Atualiza o patrimônio
    if transferencia.setor_destino_id:
        patrimonio.setor_id = transferencia.setor_destino_id
    if transferencia.responsavel_destino_id:
        patrimonio.responsavel_id = transferencia.responsavel_destino_id
    
    # 🆕 Marca como efetivada
    transferencia.efetivada = True
    transferencia.data_efetivacao = datetime.now()
    
    db.commit()
    db.refresh(transferencia)
    db.refresh(patrimonio)
    
    # Log de efetivação
    registrar_log(
        db=db,
        acao="Efetivação de Transferência",
        entidade="patrimonios",
        entidade_id=patrimonio.id,
        usuario_id=current_user.id,
        detalhes={
            "transferencia_id": transferencia.id,
            "novo_setor_id": patrimonio.setor_id,
            "novo_responsavel_id": patrimonio.responsavel_id
        }
    )
    
    return transferencia


# ========================================
# ATUALIZAR TRANSFERÊNCIA (uso geral)
# ========================================
@router.put("/{transferencia_id}", response_model=TransferenciaOut)
def update_transferencia(
    transferencia_id: int,
    transfer_in: TransferenciaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza campos de uma transferência.
    
    ⚠️ Use os endpoints específicos para:
    - /aprovar - aprovar transferência
    - /rejeitar - rejeitar transferência
    - /efetivar - efetivar transferência
    """
    
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    
    # Atualiza apenas os campos fornecidos
    for field, value in transfer_in.model_dump(exclude_unset=True).items():
        setattr(transferencia, field, value)
    
    db.commit()
    db.refresh(transferencia)
    
    # Log automático
    registrar_log(
        db=db,
        acao="Atualização de Transferência",
        entidade="transferencias",
        entidade_id=transferencia.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": transfer_in.model_dump(exclude_unset=True)}
    )
    
    return transferencia


# ========================================
# EXCLUIR TRANSFERÊNCIA
# ========================================
@router.delete("/{transferencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transferencia(
    transferencia_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exclui uma transferência.
    
    ⚠️ CUIDADO: Transferências efetivadas não devem ser excluídas.
    """
    
    transferencia = db.query(Transferencia).filter(Transferencia.id == transferencia_id).first()
    if not transferencia:
        raise HTTPException(status_code=404, detail="Transferência não encontrada.")
    
    # Impede exclusão de transferências efetivadas
    if transferencia.efetivada:
        raise HTTPException(
            status_code=400,
            detail="Transferências efetivadas não podem ser excluídas. Entre em contato com o administrador."
        )
    
    db.delete(transferencia)
    db.commit()
    
    # Log automático
    registrar_log(
        db=db,
        acao="Exclusão de Transferência",
        entidade="transferencias",
        entidade_id=transferencia_id,
        usuario_id=current_user.id,
        detalhes={"mensagem": f"Transferência {transferencia_id} removida"}
    )
    
    return None