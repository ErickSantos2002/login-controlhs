# app/core/config.py

import os

class Settings:
    # Lê as variáveis do ambiente da VPS
    DATABASE_URL: str = os.environ.get('DATABASE_URL')
    SECRET_KEY: str = os.environ.get('SECRET_KEY')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

    # Coloque outras variáveis conforme necessidade

settings = Settings()
