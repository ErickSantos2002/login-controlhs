# app/schemas/inventario.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.inventario import StatusInventario, TipoInventario, SituacaoItem

# ==================== SCHEMAS DE INVENTÁRIO (SESSÃO) ====================

class PatrimonioSimples(BaseModel):
    """Schema simplificado do patrimônio para usar no inventário"""
    id: int
    nome: str
    numero_serie: Optional[str] = None
    descricao: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }

class InventarioBase(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=200, description="Título do inventário")
    descricao: Optional[str] = Field(None, description="Descrição detalhada do inventário")
    tipo: TipoInventario = Field(default=TipoInventario.GERAL, description="Tipo de inventário")
    filtro_setor_id: Optional[int] = Field(None, description="ID do setor para filtro (quando tipo = por_setor)")
    filtro_categoria_id: Optional[int] = Field(None, description="ID da categoria para filtro (quando tipo = por_categoria)")

class InventarioCreate(InventarioBase):
    """Schema para criar uma nova sessão de inventário"""
    responsavel_id: Optional[int] = None

class InventarioUpdate(BaseModel):
    """Schema para atualizar uma sessão de inventário"""
    titulo: Optional[str] = Field(None, min_length=3, max_length=200)
    descricao: Optional[str] = None
    status: Optional[StatusInventario] = None
    responsavel_id: Optional[int] = None

class InventarioOut(InventarioBase):
    """Schema de resposta com dados completos do inventário"""
    id: int
    status: StatusInventario
    responsavel_id: Optional[int]
    data_inicio: datetime
    data_fim: Optional[datetime]
    criado_em: datetime
    atualizado_em: datetime

    model_config = {
        "from_attributes": True
    }

class InventarioComItens(InventarioOut):
    """Schema de resposta com inventário e seus itens"""
    itens: List["ItemInventarioOut"] = []

    model_config = {
        "from_attributes": True
    }


# ==================== SCHEMAS DE ITEM DE INVENTÁRIO ====================

class ItemInventarioBase(BaseModel):
    patrimonio_id: int = Field(..., description="ID do patrimônio sendo inventariado")
    observacoes: Optional[str] = Field(None, description="Observações sobre o item")

class ItemInventarioCreate(ItemInventarioBase):
    """Schema para adicionar item ao inventário"""
    situacao: SituacaoItem = Field(default=SituacaoItem.ENCONTRADO, description="Situação do item")

class ItemInventarioBulkCreate(BaseModel):
    """Schema para adicionar múltiplos itens de uma vez"""
    patrimonio_ids: List[int] = Field(..., description="Lista de IDs de patrimônios")

class ItemInventarioUpdate(BaseModel):
    """Schema para atualizar (conferir) um item do inventário"""
    situacao: Optional[SituacaoItem] = None
    observacoes: Optional[str] = None

class ItemInventarioOut(ItemInventarioBase):
    id: int
    inventario_id: int
    situacao: SituacaoItem
    conferido_por: Optional[int]
    data_conferencia: Optional[datetime]
    criado_em: datetime
    atualizado_em: datetime
    patrimonio: Optional[PatrimonioSimples] = None

    model_config = {
        "from_attributes": True
    }


# ==================== SCHEMAS AUXILIARES ====================

class InventarioFinalizar(BaseModel):
    """Schema para finalizar inventário"""
    observacoes_finais: Optional[str] = Field(None, description="Observações sobre o encerramento")

class InventarioStats(BaseModel):
    """Estatísticas do inventário"""
    total_itens: int
    encontrados: int
    nao_encontrados: int
    divergencias: int
    conferidos: int
    pendentes: int
