# app/models/anexo.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.utils.db import Base

class Anexo(Base):
    __tablename__ = "anexos"

    id = Column(Integer, primary_key=True, index=True)
    patrimonio_id = Column(Integer, ForeignKey("patrimonios.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    baixa_id = Column(Integer, ForeignKey("baixas.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    tipo = Column(String(50), nullable=False)
    caminho_arquivo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    enviado_por = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    patrimonio = relationship("Patrimonio")
    baixa = relationship("Baixa", back_populates="anexos")
    usuario = relationship("User")

    def __repr__(self):
        return f"<Anexo(patrimonio_id={self.patrimonio_id}, baixa_id={self.baixa_id}, tipo={self.tipo}, caminho={self.caminho_arquivo})>"
