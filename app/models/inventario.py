# app/models/inventario.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Inventario(Base):
    __tablename__ = "inventarios"

    id = Column(Integer, primary_key=True, index=True)
    patrimonio_id = Column(Integer, ForeignKey("patrimonios.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    responsavel_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    data_verificacao = Column(DateTime(timezone=True), server_default=func.now())
    situacao = Column(String(50), nullable=False)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patrimonio = relationship("Patrimonio")
    responsavel = relationship("User")

    def __repr__(self):
        return f"<Inventario(patrimonio_id={self.patrimonio_id}, situacao={self.situacao!r})>"
