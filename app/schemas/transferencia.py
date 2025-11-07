# app/schemas/transferencia.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TransferenciaBase(BaseModel):
    patrimonio_id: int
    setor_origem_id: Optional[int] = None
    setor_destino_id: Optional[int] = None
    responsavel_origem_id: Optional[int] = None
    responsavel_destino_id: Optional[int] = None
    motivo: Optional[str] = None

class TransferenciaCreate(TransferenciaBase):
    """
    Schema para criação de transferência.
    O solicitante_id será preenchido automaticamente no endpoint.
    """
    # 🆕 NOVO - será preenchido automaticamente na rota
    solicitante_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "patrimonio_id": 1,
                "setor_origem_id": 1,
                "setor_destino_id": 2,
                "responsavel_origem_id": 1,
                "responsavel_destino_id": 2,
                "motivo": "Realocação de equipamento para novo setor"
            }
        }

class TransferenciaUpdate(BaseModel):
    """
    Schema para atualização de transferência.
    Usado principalmente para aprovação/rejeição.
    """
    setor_destino_id: Optional[int] = None
    responsavel_destino_id: Optional[int] = None
    aprovado_por: Optional[int] = None
    motivo: Optional[str] = None
    
    # 🆕 NOVOS CAMPOS
    observacoes: Optional[str] = None
    data_aprovacao: Optional[datetime] = None
    motivo_rejeicao: Optional[str] = None
    efetivada: Optional[bool] = None
    data_efetivacao: Optional[datetime] = None

class TransferenciaOut(TransferenciaBase):
    """
    Schema de resposta da transferência.
    Inclui todos os campos do banco.
    """
    id: int
    
    # 🆕 NOVOS CAMPOS
    solicitante_id: Optional[int] = None
    efetivada: bool = False
    motivo_rejeicao: Optional[str] = None
    observacoes: Optional[str] = None
    
    # Campos de aprovação
    aprovado_por: Optional[int] = None
    data_aprovacao: Optional[datetime] = None
    data_efetivacao: Optional[datetime] = None
    
    # Campos de timestamp
    data_transferencia: Optional[datetime] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

# ========================================
# 🆕 SCHEMAS ESPECÍFICOS PARA AÇÕES
# ========================================

class TransferenciaAprovar(BaseModel):
    """Schema para aprovar transferência"""
    observacoes: Optional[str] = Field(None, description="Observações sobre a aprovação")
    efetivar_automaticamente: bool = Field(False, description="Se deve efetivar imediatamente após aprovar")

class TransferenciaRejeitar(BaseModel):
    """Schema para rejeitar transferência"""
    motivo_rejeicao: str = Field(..., min_length=10, description="Motivo da rejeição (obrigatório)")