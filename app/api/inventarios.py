# app/api/inventarios.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.utils.db import get_db
from app.models.inventario import Inventario, ItemInventario, StatusInventario, SituacaoItem
from app.models.patrimonio import Patrimonio
from app.models.setor import Setor
from app.models.categoria import Categoria
from app.schemas.inventario import (
    InventarioCreate, InventarioUpdate, InventarioOut, InventarioComItens,
    ItemInventarioCreate, ItemInventarioUpdate, ItemInventarioOut, ItemInventarioBulkCreate,
    InventarioFinalizar, InventarioStats
)
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/inventarios", tags=["Inventários"])


# ===================== CRUD DE INVENTÁRIOS (SESSÕES) =====================

@router.post("/", response_model=InventarioOut, status_code=status.HTTP_201_CREATED)
def criar_inventario(
    inventario_in: InventarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria uma nova sessão de inventário.

    Tipos de inventário:
    - **geral**: Inventário completo de todos os patrimônios
    - **por_setor**: Inventário filtrado por setor específico
    - **por_categoria**: Inventário filtrado por categoria específica
    """
    # Validações
    if inventario_in.tipo == "por_setor" and not inventario_in.filtro_setor_id:
        raise HTTPException(status_code=400, detail="Para tipo 'por_setor', filtro_setor_id é obrigatório")

    if inventario_in.tipo == "por_categoria" and not inventario_in.filtro_categoria_id:
        raise HTTPException(status_code=400, detail="Para tipo 'por_categoria', filtro_categoria_id é obrigatório")

    # Verificar se setor existe
    if inventario_in.filtro_setor_id:
        setor = db.query(Setor).filter(Setor.id == inventario_in.filtro_setor_id).first()
        if not setor:
            raise HTTPException(status_code=404, detail="Setor não encontrado")

    # Verificar se categoria existe
    if inventario_in.filtro_categoria_id:
        categoria = db.query(Categoria).filter(Categoria.id == inventario_in.filtro_categoria_id).first()
        if not categoria:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")

    # Criar inventário
    inventario = Inventario(**inventario_in.model_dump())
    if not inventario.responsavel_id:
        inventario.responsavel_id = current_user.id

    db.add(inventario)
    db.flush()  # Flush para obter o ID do inventário sem fazer commit ainda

    # Buscar patrimônios baseado no tipo de inventário
    patrimonios_query = db.query(Patrimonio)

    if inventario_in.tipo == "por_setor":
        # Filtrar por setor
        patrimonios_query = patrimonios_query.filter(Patrimonio.setor_id == inventario_in.filtro_setor_id)
    elif inventario_in.tipo == "por_categoria":
        # Filtrar por categoria
        patrimonios_query = patrimonios_query.filter(Patrimonio.categoria_id == inventario_in.filtro_categoria_id)
    # Se tipo == "geral", busca todos (sem filtro adicional)

    patrimonios = patrimonios_query.all()

    # Criar itens do inventário automaticamente
    itens_criados = []
    for patrimonio in patrimonios:
        item = ItemInventario(
            inventario_id=inventario.id,
            patrimonio_id=patrimonio.id,
            situacao=SituacaoItem.PENDENTE.value
        )
        db.add(item)
        itens_criados.append(item)

    # Commit de tudo junto (inventário + itens)
    db.commit()
    db.refresh(inventario)

    # Log
    registrar_log(
        db=db,
        acao="Criação de Inventário",
        entidade="inventarios",
        entidade_id=inventario.id,
        usuario_id=current_user.id,
        detalhes={
            "titulo": inventario.titulo,
            "tipo": inventario.tipo,
            "status": inventario.status,
            "total_itens_adicionados": len(itens_criados)
        }
    )

    return inventario


@router.get("/", response_model=List[InventarioOut])
def listar_inventarios(
    status_filter: Optional[StatusInventario] = Query(None, description="Filtrar por status"),
    tipo_filter: Optional[str] = Query(None, description="Filtrar por tipo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todas as sessões de inventário com filtros opcionais."""
    query = db.query(Inventario)

    if status_filter:
        query = query.filter(Inventario.status == status_filter)

    if tipo_filter:
        query = query.filter(Inventario.tipo == tipo_filter)

    return query.order_by(Inventario.data_inicio.desc()).all()


@router.get("/{inventario_id}", response_model=InventarioComItens)
def obter_inventario(
    inventario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtém detalhes de uma sessão de inventário incluindo todos os itens."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    return inventario


@router.put("/{inventario_id}", response_model=InventarioOut)
def atualizar_inventario(
    inventario_id: int,
    inventario_in: InventarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza informações de uma sessão de inventário."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    # Não permitir atualizar inventários finalizados ou cancelados
    if inventario.status in [StatusInventario.CONCLUIDO.value, StatusInventario.CANCELADO.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível atualizar inventário com status '{inventario.status}'"
        )

    for field, value in inventario_in.model_dump(exclude_unset=True).items():
        setattr(inventario, field, value)

    db.commit()
    db.refresh(inventario)

    # Log
    registrar_log(
        db=db,
        acao="Atualização de Inventário",
        entidade="inventarios",
        entidade_id=inventario.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": inventario_in.model_dump(exclude_unset=True)}
    )

    return inventario


@router.delete("/{inventario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_inventario(
    inventario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove uma sessão de inventário e todos os seus itens."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    db.delete(inventario)
    db.commit()

    # Log
    registrar_log(
        db=db,
        acao="Exclusão de Inventário",
        entidade="inventarios",
        entidade_id=inventario_id,
        usuario_id=current_user.id,
        detalhes={"titulo": inventario.titulo}
    )

    return None


# ===================== GERENCIAMENTO DE ITENS DO INVENTÁRIO =====================

@router.get("/{inventario_id}/itens", response_model=List[ItemInventarioOut])
def listar_itens_inventario(
    inventario_id: int,
    situacao_filter: Optional[SituacaoItem] = Query(None, description="Filtrar por situação"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os itens de uma sessão de inventário com filtro opcional por situação."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    query = db.query(ItemInventario).filter(ItemInventario.inventario_id == inventario_id)

    if situacao_filter:
        query = query.filter(ItemInventario.situacao == situacao_filter)

    return query.all()


@router.post("/{inventario_id}/itens", response_model=ItemInventarioOut, status_code=status.HTTP_201_CREATED)
def adicionar_item_inventario(
    inventario_id: int,
    item_in: ItemInventarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adiciona um único patrimônio à sessão de inventário."""
    # Verificar se inventário existe e está em andamento
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    if inventario.status != StatusInventario.EM_ANDAMENTO.value:
        raise HTTPException(status_code=400, detail="Só é possível adicionar itens a inventários em andamento")

    # Verificar se patrimônio existe
    patrimonio = db.query(Patrimonio).filter(Patrimonio.id == item_in.patrimonio_id).first()
    if not patrimonio:
        raise HTTPException(status_code=404, detail="Patrimônio não encontrado")

    # Verificar se item já existe no inventário
    item_existente = db.query(ItemInventario).filter(
        ItemInventario.inventario_id == inventario_id,
        ItemInventario.patrimonio_id == item_in.patrimonio_id
    ).first()
    if item_existente:
        raise HTTPException(status_code=400, detail="Este patrimônio já está no inventário")

    # Criar item
    item = ItemInventario(
        inventario_id=inventario_id,
        **item_in.model_dump()
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # Log
    registrar_log(
        db=db,
        acao="Adição de Item ao Inventário",
        entidade="itens_inventario",
        entidade_id=item.id,
        usuario_id=current_user.id,
        detalhes={
            "inventario_id": inventario_id,
            "patrimonio_id": item_in.patrimonio_id
        }
    )

    return item


@router.post("/{inventario_id}/itens/bulk", response_model=List[ItemInventarioOut], status_code=status.HTTP_201_CREATED)
def adicionar_itens_bulk(
    inventario_id: int,
    items_in: ItemInventarioBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adiciona múltiplos patrimônios de uma vez ao inventário.
    Útil para iniciar um inventário com base em filtros.
    """
    # Verificar se inventário existe e está em andamento
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    if inventario.status != StatusInventario.EM_ANDAMENTO.value:
        raise HTTPException(status_code=400, detail="Só é possível adicionar itens a inventários em andamento")

    # Verificar quais patrimônios existem
    patrimonios = db.query(Patrimonio).filter(Patrimonio.id.in_(items_in.patrimonio_ids)).all()
    patrimonios_ids_encontrados = {p.id for p in patrimonios}

    patrimonios_nao_encontrados = set(items_in.patrimonio_ids) - patrimonios_ids_encontrados
    if patrimonios_nao_encontrados:
        raise HTTPException(
            status_code=404,
            detail=f"Patrimônios não encontrados: {list(patrimonios_nao_encontrados)}"
        )

    # Verificar itens que já existem
    itens_existentes = db.query(ItemInventario.patrimonio_id).filter(
        ItemInventario.inventario_id == inventario_id,
        ItemInventario.patrimonio_id.in_(items_in.patrimonio_ids)
    ).all()
    patrimonios_ja_adicionados = {item[0] for item in itens_existentes}

    # Criar apenas os itens novos
    itens_novos = []
    for patrimonio_id in items_in.patrimonio_ids:
        if patrimonio_id not in patrimonios_ja_adicionados:
            item = ItemInventario(
                inventario_id=inventario_id,
                patrimonio_id=patrimonio_id,
                situacao=SituacaoItem.PENDENTE.value
            )
            itens_novos.append(item)

    if itens_novos:
        db.add_all(itens_novos)
        db.commit()
        for item in itens_novos:
            db.refresh(item)

    # Log
    registrar_log(
        db=db,
        acao="Adição em Massa de Itens ao Inventário",
        entidade="inventarios",
        entidade_id=inventario_id,
        usuario_id=current_user.id,
        detalhes={
            "total_solicitados": len(items_in.patrimonio_ids),
            "total_adicionados": len(itens_novos),
            "ja_existentes": len(patrimonios_ja_adicionados)
        }
    )

    return itens_novos


@router.put("/{inventario_id}/itens/{item_id}", response_model=ItemInventarioOut)
def atualizar_item_inventario(
    inventario_id: int,
    item_id: int,
    item_in: ItemInventarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza um item do inventário (usado para marcar como conferido).
    Registra automaticamente quem conferiu e quando.
    """
    # Verificar se item existe no inventário
    item = db.query(ItemInventario).filter(
        ItemInventario.id == item_id,
        ItemInventario.inventario_id == inventario_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado neste inventário")

    # Verificar se inventário está em andamento
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if inventario.status != StatusInventario.EM_ANDAMENTO.value:
        raise HTTPException(status_code=400, detail="Só é possível atualizar itens de inventários em andamento")

    # Atualizar campos
    for field, value in item_in.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    # Marcar quem conferiu e quando
    item.conferido_por = current_user.id
    item.data_conferencia = datetime.now()

    db.commit()
    db.refresh(item)

    # Log
    registrar_log(
        db=db,
        acao="Conferência de Item de Inventário",
        entidade="itens_inventario",
        entidade_id=item.id,
        usuario_id=current_user.id,
        detalhes={
            "inventario_id": inventario_id,
            "patrimonio_id": item.patrimonio_id,
            "situacao": item.situacao,
            "observacoes": item.observacoes
        }
    )

    return item


@router.delete("/{inventario_id}/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_item_inventario(
    inventario_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove um item do inventário."""
    # Verificar se item existe no inventário
    item = db.query(ItemInventario).filter(
        ItemInventario.id == item_id,
        ItemInventario.inventario_id == inventario_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado neste inventário")

    # Verificar se inventário está em andamento
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if inventario.status != StatusInventario.EM_ANDAMENTO.value:
        raise HTTPException(status_code=400, detail="Só é possível remover itens de inventários em andamento")

    db.delete(item)
    db.commit()

    # Log
    registrar_log(
        db=db,
        acao="Remoção de Item do Inventário",
        entidade="itens_inventario",
        entidade_id=item_id,
        usuario_id=current_user.id,
        detalhes={
            "inventario_id": inventario_id,
            "patrimonio_id": item.patrimonio_id
        }
    )

    return None


# ===================== AÇÕES ESPECIAIS =====================

@router.post("/{inventario_id}/finalizar", response_model=InventarioOut)
def finalizar_inventario(
    inventario_id: int,
    finalizacao: InventarioFinalizar,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Finaliza uma sessão de inventário.
    Marca o inventário como concluído e registra a data de conclusão.
    """
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    if inventario.status != StatusInventario.EM_ANDAMENTO.value:
        raise HTTPException(status_code=400, detail="Só é possível finalizar inventários em andamento")

    # Atualizar status e data de fim
    inventario.status = StatusInventario.CONCLUIDO.value
    inventario.data_fim = datetime.now()

    db.commit()
    db.refresh(inventario)

    # Log
    registrar_log(
        db=db,
        acao="Finalização de Inventário",
        entidade="inventarios",
        entidade_id=inventario.id,
        usuario_id=current_user.id,
        detalhes={
            "titulo": inventario.titulo,
            "observacoes_finais": finalizacao.observacoes_finais
        }
    )

    return inventario


@router.post("/{inventario_id}/cancelar", response_model=InventarioOut)
def cancelar_inventario(
    inventario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancela uma sessão de inventário."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    if inventario.status != StatusInventario.EM_ANDAMENTO.value:
        raise HTTPException(status_code=400, detail="Só é possível cancelar inventários em andamento")

    inventario.status = StatusInventario.CANCELADO.value
    inventario.data_fim = datetime.now()

    db.commit()
    db.refresh(inventario)

    # Log
    registrar_log(
        db=db,
        acao="Cancelamento de Inventário",
        entidade="inventarios",
        entidade_id=inventario.id,
        usuario_id=current_user.id,
        detalhes={"titulo": inventario.titulo}
    )

    return inventario


@router.get("/{inventario_id}/estatisticas", response_model=InventarioStats)
def obter_estatisticas_inventario(
    inventario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna estatísticas sobre o progresso do inventário."""
    inventario = db.query(Inventario).filter(Inventario.id == inventario_id).first()
    if not inventario:
        raise HTTPException(status_code=404, detail="Inventário não encontrado")

    # Contar itens por situação
    stats = db.query(
        func.count(ItemInventario.id).label("total"),
        ItemInventario.situacao
    ).filter(
        ItemInventario.inventario_id == inventario_id
    ).group_by(ItemInventario.situacao).all()

    # Organizar resultados
    resultado = {
        "total_itens": 0,
        "encontrados": 0,
        "nao_encontrados": 0,
        "divergencias": 0,
        "conferidos": 0,
        "pendentes": 0
    }

    for count, situacao in stats:
        resultado["total_itens"] += count
        if situacao == SituacaoItem.PENDENTE.value:
            resultado["pendentes"] = count
        elif situacao == SituacaoItem.ENCONTRADO.value:
            resultado["encontrados"] = count
        elif situacao == SituacaoItem.NAO_ENCONTRADO.value:
            resultado["nao_encontrados"] = count
        elif situacao == SituacaoItem.DIVERGENCIA.value:
            resultado["divergencias"] = count
        elif situacao == SituacaoItem.CONFERIDO.value:
            resultado["conferidos"] = count

    return resultado
