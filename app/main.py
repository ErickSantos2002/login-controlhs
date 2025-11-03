# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
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

app = FastAPI(
    title="ControlHS API",
    description="API para controle de patrimônios",
    version="1.0.0"
)

# ========================================
# CORS CONFIGURATION
# ========================================

# Lista de origens permitidas
allowed_origins = [
    "https://controlhs.healthsafetytech.com",
    "https://authapicontrolhs.healthsafetytech.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
]

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
        # Log detalhado do erro
        print(f"❌ Erro não tratado: {exc}")
        print(f"Traceback: {traceback.format_exc()}")
        
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
# LOGGING MIDDLEWARE (OPCIONAL)
# ========================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para logging de requisições (útil para debug)
    """
    print(f"📥 {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    print(f"📤 {request.method} {request.url.path} - Status: {response.status_code}")
    
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