# app/core/config.py

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Configurações da aplicação usando Pydantic BaseSettings.
    Carrega automaticamente de variáveis de ambiente ou arquivo .env
    """

    # Database
    DATABASE_URL: str = Field(..., description="URL de conexão PostgreSQL")

    # Security
    SECRET_KEY: str = Field(..., min_length=32, description="Chave secreta para JWT (min 32 chars)")
    ALGORITHM: str = Field(default="HS256", description="Algoritmo de criptografia JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=1440, description="Tempo de expiração do token (5-1440 min)")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        description="Origens permitidas para CORS (separadas por vírgula)"
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Ambiente: development, staging ou production")
    DEBUG: bool = Field(default=True, description="Modo debug (desabilitar em produção)")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Habilitar rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Requisições por minuto por IP")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log: DEBUG, INFO, WARNING, ERROR")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

        # Converter string separada por vírgula em lista
        @staticmethod
        def parse_env_var(field_name: str, raw_val: str):
            if field_name == "CORS_ORIGINS":
                return [origin.strip() for origin in raw_val.split(",")]
            return raw_val

# Instância global de configurações
settings = Settings()
