# app/models/inventario.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.utils.db import Base
import enum

class StatusInventario(str, enum.Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"
    CANCELADO = "cancelado"

class TipoInventario(str, enum.Enum):
    GERAL = "geral"
    POR_SETOR = "por_setor"
    POR_CATEGORIA = "por_categoria"

class SituacaoItem(str, enum.Enum):
    ENCONTRADO = "encontrado"
    NAO_ENCONTRADO = "nao_encontrado"
    DIVERGENCIA = "divergencia"
    CONFERIDO = "conferido"

class Inventario(Base):
    """Sessão de inventário que agrupa múltiplos itens"""
    __tablename__ = "inventarios"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    status = Column(SQLEnum(StatusInventario), default=StatusInventario.EM_ANDAMENTO, nullable=False)
    responsavel_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    data_inicio = Column(DateTime(timezone=True), server_default=func.now())
    data_fim = Column(DateTime(timezone=True), nullable=True)
    tipo = Column(SQLEnum(TipoInventario), default=TipoInventario.GERAL, nullable=False)
    filtro_setor_id = Column(Integer, ForeignKey("setores.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    filtro_categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    responsavel = relationship("User", foreign_keys=[responsavel_id])
    filtro_setor = relationship("Setor", foreign_keys=[filtro_setor_id])
    filtro_categoria = relationship("Categoria", foreign_keys=[filtro_categoria_id])
    itens = relationship("ItemInventario", back_populates="inventario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Inventario(id={self.id}, titulo={self.titulo!r}, status={self.status})>"


class ItemInventario(Base):
    """Item individual dentro de uma sessão de inventário"""
    __tablename__ = "itens_inventario"

    id = Column(Integer, primary_key=True, index=True)
    inventario_id = Column(Integer, ForeignKey("inventarios.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    patrimonio_id = Column(Integer, ForeignKey("patrimonios.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    situacao = Column(SQLEnum(SituacaoItem), default=SituacaoItem.ENCONTRADO, nullable=False)
    observacoes = Column(Text, nullable=True)
    conferido_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    data_conferencia = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    inventario = relationship("Inventario", back_populates="itens")
    patrimonio = relationship("Patrimonio")
    conferido_por_user = relationship("User", foreign_keys=[conferido_por])

    def __repr__(self):
        return f"<ItemInventario(id={self.id}, inventario_id={self.inventario_id}, patrimonio_id={self.patrimonio_id}, situacao={self.situacao})>"
