# app/core/config.py

import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """
    Configurações da aplicação usando Pydantic BaseSettings.
    Carrega automaticamente de variáveis de ambiente ou arquivo .env
    """

    # Database
    DATABASE_URL: str = Field(..., description="URL de conexão PostgreSQL")

    # Security
    SECRET_KEY: str = Field(..., description="Chave secreta para JWT")
    ALGORITHM: str = Field(default="HS256", description="Algoritmo de criptografia JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=1440, description="Tempo de expiração do token (5-1440 min)")

    # CORS
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["*"],
        description="Origens permitidas para CORS (separadas por vírgula ou lista JSON)"
    )

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Ambiente: development, staging ou production")
    DEBUG: bool = Field(default=True, description="Modo debug (desabilitar em produção)")

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Habilitar rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Requisições por minuto por IP")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log: DEBUG, INFO, WARNING, ERROR")

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Converte string separada por vírgula em lista.
        Aceita: "url1,url2,url3" ou ["url1", "url2", "url3"] ou None
        """
        if v is None or v == "":
            return ["*"]
        if isinstance(v, str):
            # Remove espaços e divide por vírgula
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

# Instância global de configurações
settings = Settings()
