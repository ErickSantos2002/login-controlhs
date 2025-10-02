# app/models/user.py

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.db import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)

    role = relationship("Role")

    def __repr__(self):
        return f"<User(username={self.username!r}, role={self.role.name if self.role else None})>"
