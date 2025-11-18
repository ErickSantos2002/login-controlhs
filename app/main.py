# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
import logging
from app.api import (
    auth,
    patrimonios,
    categorias,
    setores,
    transferencias,
    baixas,
    logs_auditoria,
    inventarios,
    anexos
)
from app.core.config import settings
# from app.core.rate_limit import RateLimitMiddleware  # Removido - não usado
from app.core.logging_config import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ControlHS API",
    description="API para controle de patrimônios",
    version="1.0.0",
    debug=settings.DEBUG
)

# ========================================
# 🚀 CONFIGURAÇÃO DE UPLOAD
# ========================================

# Aumenta limite de tamanho de requisição para 10MB
# (padrão FastAPI é 1MB)
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class LimitUploadSize(BaseHTTPMiddleware):
    """Middleware para limitar tamanho de upload."""
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request, call_next):
        # Verifica tamanho apenas em uploads
        if request.method == "POST" and "/anexos/" in str(request.url):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Arquivo muito grande. Máximo: 10MB"}
                )
        
        response = await call_next(request)
        return response

# Adiciona o middleware
app.add_middleware(LimitUploadSize)

# ========================================
# RATE LIMITING - REMOVIDO
# ========================================
# Rate limiting foi removido pois a API é consumida tanto externamente
# quanto pelo próprio sistema frontend, causando bloqueios indevidos
# em ambientes de produção com múltiplos usuários simultâneos.
#
# Para proteção contra abuso, considere implementar:
# - Rate limiting no Traefik/Nginx (camada de proxy)
# - WAF (Web Application Firewall) como Cloudflare
# - Autenticação JWT já limita acesso não autorizado

logger.info("Rate limiting: DESABILITADO (proteção deve ser feita no proxy/WAF)")

# ========================================
# 📁 GARANTIR QUE PASTA UPLOADS EXISTE
# ========================================

from pathlib import Path

UPLOAD_DIR = Path("uploads/anexos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ========================================
# CORS CONFIGURATION
# ========================================

# Lista de origens permitidas (configurável via .env)
allowed_origins = settings.CORS_ORIGINS

logger.info(f"CORS configurado para: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ========================================
# ERROR HANDLING MIDDLEWARE
# ========================================

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    """
    Middleware para capturar exceções não tratadas e garantir que
    os headers CORS sejam incluídos mesmo em respostas de erro
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        # Log detalhado do erro com logger
        logger.error(f"Erro não tratado em {request.method} {request.url.path}: {exc}")
        logger.debug(f"Traceback completo: {traceback.format_exc()}")

        # Determina a origem da requisição
        origin = request.headers.get("origin")
        
        # Cria resposta de erro com headers CORS
        response = JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "message": str(exc),
                "type": type(exc).__name__
            }
        )
        
        # Adiciona headers CORS explicitamente
        if origin in allowed_origins or origin is None:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

# ========================================
# LOGGING MIDDLEWARE
# ========================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para logging de requisições
    """
    # Obter IP real do cliente
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

    if settings.DEBUG:
        logger.debug(f"Requisição: {request.method} {request.url.path} de {client_ip}")

    response = await call_next(request)

    # Log apenas erros em produção
    if response.status_code >= 400:
        logger.warning(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"IP: {client_ip}"
        )
    elif settings.DEBUG:
        logger.debug(f"Resposta: {request.method} {request.url.path} - Status: {response.status_code}")

    return response

# ========================================
# ROUTERS
# ========================================

app.include_router(auth.router, tags=["Authentication"])
app.include_router(patrimonios.router, tags=["Patrimônios"])
app.include_router(categorias.router, tags=["Categorias"])
app.include_router(setores.router, tags=["Setores"])
app.include_router(transferencias.router, tags=["Transferências"])
app.include_router(baixas.router, tags=["Baixas"])
app.include_router(logs_auditoria.router, tags=["Logs"])
app.include_router(inventarios.router, tags=["Inventários"])
app.include_router(anexos.router, tags=["Anexos"])

# ========================================
# ROOT ENDPOINT
# ========================================

@app.get("/", tags=["Health Check"])
def read_root():
    """
    Endpoint raiz para verificar se a API está rodando
    """
    return {
        "msg": "API do ControlHS rodando! 🚀",
        "version": "1.0.0",
        "status": "online"
    }

# ========================================
# HEALTH CHECK
# ========================================

@app.get("/health", tags=["Health Check"])
def health_check():
    """
    Endpoint de health check para monitoramento
    """
    return {
        "status": "healthy",
        "service": "ControlHS API"
    }