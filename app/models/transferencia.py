# app/models/transferencia.py
from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Transferencia(Base):
    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True, index=True)
    patrimonio_id = Column(Integer, ForeignKey("patrimonios.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    
    # ========================================
    # CAMPOS DE ORIGEM E DESTINO
    # ========================================
    setor_origem_id = Column(Integer, ForeignKey("setores.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    setor_destino_id = Column(Integer, ForeignKey("setores.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    responsavel_origem_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    responsavel_destino_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    
    # ========================================
    # 🆕 NOVOS CAMPOS - SOLICITANTE
    # ========================================
    solicitante_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    
    # ========================================
    # CAMPOS DE APROVAÇÃO/REJEIÇÃO
    # ========================================
    aprovado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    data_aprovacao = Column(DateTime(timezone=True), nullable=True)
    
    # 🆕 NOVO CAMPO - MOTIVO DE REJEIÇÃO
    motivo_rejeicao = Column(Text, nullable=True)
    
    # ========================================
    # 🆕 NOVO CAMPO - EFETIVAÇÃO
    # ========================================
    efetivada = Column(Boolean, default=False, nullable=False)
    data_efetivacao = Column(DateTime(timezone=True), nullable=True)
    
    # ========================================
    # CAMPOS GERAIS
    # ========================================
    data_transferencia = Column(DateTime(timezone=True), server_default=func.now())
    motivo = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)  # 🆕 Para observações do aprovador
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ========================================
    # RELACIONAMENTOS
    # ========================================
    patrimonio = relationship("Patrimonio", back_populates="transferencias")
    setor_origem = relationship("Setor", foreign_keys=[setor_origem_id])
    setor_destino = relationship("Setor", foreign_keys=[setor_destino_id])
    responsavel_origem = relationship("User", foreign_keys=[responsavel_origem_id])
    responsavel_destino = relationship("User", foreign_keys=[responsavel_destino_id])
    solicitante = relationship("User", foreign_keys=[solicitante_id])  # 🆕
    aprovador = relationship("User", foreign_keys=[aprovado_por])

    def __repr__(self):
        return f"<Transferencia(id={self.id}, patrimonio_id={self.patrimonio_id}, efetivada={self.efetivada})>"