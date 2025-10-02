# app/utils/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Cria a engine do SQLAlchemy com a URL do banco
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Cria a factory de sessão para o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para todos os models herdarem
Base = declarative_base()

# Dependência para FastAPI (yield session, fecha após uso)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
