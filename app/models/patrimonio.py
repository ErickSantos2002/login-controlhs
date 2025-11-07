# app/models/patrimonio.py
from sqlalchemy import Column, Integer, String, Text, Date, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Patrimonio(Base):
    __tablename__ = "patrimonios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=True)
    numero_serie = Column(String(100), nullable=True)

    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    setor_id = Column(Integer, ForeignKey("setores.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    responsavel_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)

    data_aquisicao = Column(Date, nullable=True)
    valor_aquisicao = Column(Numeric(12, 2), nullable=True)
    valor_atual = Column(Numeric(12, 2), nullable=True)

    status = Column(String(30), nullable=True, default="ativo")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    categoria = relationship("Categoria", back_populates="patrimonios")
    setor = relationship("Setor", back_populates="patrimonios")
    responsavel = relationship("User")
    transferencias = relationship("Transferencia", back_populates="patrimonio")

    def __repr__(self):
        return f"<Patrimonio(nome={self.nome}, status={self.status})>"
