# app/models/baixa.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Baixa(Base):
    __tablename__ = "baixas"

    id = Column(Integer, primary_key=True, index=True)
    patrimonio_id = Column(Integer, ForeignKey("patrimonios.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    tipo = Column(String(50), nullable=False)
    motivo = Column(Text, nullable=True)
    data_baixa = Column(DateTime(timezone=True), server_default=func.now())
    aprovado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patrimonio = relationship("Patrimonio")
    aprovador = relationship("User")
    anexos = relationship("Anexo", back_populates="baixa", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Baixa(patrimonio_id={self.patrimonio_id}, tipo={self.tipo})>"
