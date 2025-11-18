# app/models/log_auditoria.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.utils.db import Base

class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    acao = Column(String(100), nullable=False)
    entidade = Column(String(100), nullable=False)
    entidade_id = Column(Integer, nullable=True)
    usuario_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    detalhes = Column(JSON, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    usuario_rel = relationship("User", foreign_keys=[usuario_id])

    @property
    def usuario(self):
        """Retorna o nome do usuário que executou a ação"""
        return self.usuario_rel.username if self.usuario_rel else "Sistema"

    def __repr__(self):
        return f"<LogAuditoria(acao={self.acao!r}, entidade={self.entidade!r}, usuario_id={self.usuario_id})>"
