# app/models/transferencia.py
from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Transferencia(Base):
    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True, index=True)
    patrimonio_id = Column(Integer, ForeignKey("patrimonios.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    setor_origem_id = Column(Integer, ForeignKey("setores.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    setor_destino_id = Column(Integer, ForeignKey("setores.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    responsavel_origem_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    responsavel_destino_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    aprovado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)

    data_transferencia = Column(DateTime(timezone=True), server_default=func.now())
    motivo = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    patrimonio = relationship("Patrimonio")
    setor_origem = relationship("Setor", foreign_keys=[setor_origem_id])
    setor_destino = relationship("Setor", foreign_keys=[setor_destino_id])
    responsavel_origem = relationship("User", foreign_keys=[responsavel_origem_id])
    responsavel_destino = relationship("User", foreign_keys=[responsavel_destino_id])
    aprovador = relationship("User", foreign_keys=[aprovado_por])

    def __repr__(self):
        return f"<Transferencia(patrimonio_id={self.patrimonio_id}, origem={self.setor_origem_id}, destino={self.setor_destino_id})>"
