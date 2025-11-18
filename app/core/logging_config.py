# app/core/logging_config.py

import logging
import sys
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """
    Configura o sistema de logging da aplicação.

    - Desenvolvimento: Logs coloridos no console
    - Produção: Logs estruturados em JSON
    """

    # Criar diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configurar formato baseado no ambiente
    if settings.ENVIRONMENT == "production":
        # Produção: Logs em JSON para ferramentas de análise
        log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    else:
        # Desenvolvimento: Logs legíveis
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configurar nível de log
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configurar logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            # Console
            logging.StreamHandler(sys.stdout),
            # Arquivo (rotativo)
            logging.FileHandler(
                log_dir / "app.log",
                encoding="utf-8"
            )
        ]
    )

    # Silenciar logs verbosos de bibliotecas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configurado para ambiente: {settings.ENVIRONMENT}")
    logger.info(f"Nível de log: {settings.LOG_LEVEL}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para um módulo específico.

    Uso:
        logger = get_logger(__name__)
        logger.info("Mensagem")
    """
    return logging.getLogger(name)
