# app/api/anexos.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.utils.db import get_db
from app.models.anexo import Anexo
from app.models.patrimonio import Patrimonio
from app.schemas.anexo import AnexoCreate, AnexoUpdate, AnexoOut
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User
import shutil, os

router = APIRouter(prefix="/anexos", tags=["Anexos"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ===================== CRIAR (UPLOAD) =====================
@router.post("/", response_model=AnexoOut)
async def upload_anexo(
    patrimonio_id: Optional[int] = Form(None),
    tipo: str = Form(...),
    descricao: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Faz upload e cria registro de anexo."""
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    anexo = Anexo(
        patrimonio_id=patrimonio_id,
        tipo=tipo,
        caminho_arquivo=file_path,
        descricao=descricao,
        enviado_por=current_user.id,
    )

    db.add(anexo)
    db.commit()
    db.refresh(anexo)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Upload de Anexo",
        entidade="anexos",
        entidade_id=anexo.id,
        usuario_id=current_user.id,
        detalhes={
            "arquivo": file.filename,
            "tipo": tipo,
            "descricao": descricao,
            "patrimonio_id": patrimonio_id
        }
    )

    return anexo


# ===================== LISTAR =====================
@router.get("/", response_model=List[AnexoOut])
def list_anexos(db: Session = Depends(get_db)):
    """Lista todos os anexos cadastrados."""
    return db.query(Anexo).order_by(Anexo.criado_em.desc()).all()


# ===================== DETALHAR =====================
@router.get("/{anexo_id}", response_model=AnexoOut)
def get_anexo(anexo_id: int, db: Session = Depends(get_db)):
    """Retorna informações de um anexo específico."""
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    return anexo


# ===================== ATUALIZAR =====================
@router.put("/{anexo_id}", response_model=AnexoOut)
def update_anexo(
    anexo_id: int,
    anexo_in: AnexoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza informações de um anexo."""
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")

    for field, value in anexo_in.model_dump(exclude_unset=True).items():
        setattr(anexo, field, value)

    db.commit()
    db.refresh(anexo)

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Atualização de Anexo",
        entidade="anexos",
        entidade_id=anexo.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": anexo_in.model_dump(exclude_unset=True)}
    )

    return anexo


# ===================== EXCLUIR =====================
@router.delete("/{anexo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_anexo(
    anexo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove o registro e o arquivo físico."""
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")

    # Remove o arquivo físico se existir
    if anexo.caminho_arquivo and os.path.exists(anexo.caminho_arquivo):
        os.remove(anexo.caminho_arquivo)

    db.delete(anexo)
    db.commit()

    # 🟢 Log automático
    registrar_log(
        db=db,
        acao="Exclusão de Anexo",
        entidade="anexos",
        entidade_id=anexo_id,
        usuario_id=current_user.id,
        detalhes={"arquivo": anexo.caminho_arquivo, "mensagem": f"Anexo {anexo_id} removido"}
    )

    return None
