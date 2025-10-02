# app/models/role.py

from sqlalchemy import Column, Integer, String
from app.utils.db import Base

class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"<Role(name={self.name!r})>"
