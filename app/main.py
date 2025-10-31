# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, patrimonios, categorias, setores, transferencias, baixas, logs_auditoria, inventarios, anexos

app = FastAPI(
    title="Login API",
    description="API para autenticação de usuários",
    version="1.0.0"
)

# CORS para liberar acesso ao frontend (ajuste para os domínios corretos depois)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://controlhs.healthsafetytech.com",
        "https://authapicontrolhs.healthsafetytech.com",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas de autenticação
app.include_router(auth.router)
app.include_router(patrimonios.router)
app.include_router(categorias.router)
app.include_router(setores.router)
app.include_router(transferencias.router)
app.include_router(baixas.router)
app.include_router(logs_auditoria.router)
app.include_router(inventarios.router)
app.include_router(anexos.router)

# (Opcional) Rota raiz simples
@app.get("/")
def read_root():
    return {"msg": "API do ControlHS rodando! 🚀"}
