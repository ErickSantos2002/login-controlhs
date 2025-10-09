# app/schemas/inventario.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InventarioBase(BaseModel):
    patrimonio_id: int
    responsavel_id: Optional[int] = None
    situacao: str
    observacoes: Optional[str] = None

class InventarioCreate(InventarioBase):
    pass

class InventarioUpdate(BaseModel):
    situacao: Optional[str] = None
    observacoes: Optional[str] = None
    responsavel_id: Optional[int] = None

class InventarioOut(InventarioBase):
    id: int
    data_verificacao: Optional[datetime]
    criado_em: Optional[datetime]
    atualizado_em: Optional[datetime]

    model_config = {
        "from_attributes": True
    }
