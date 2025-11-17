# app/api/anexos.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.utils.db import get_db
from app.models.anexo import Anexo
from app.models.patrimonio import Patrimonio
from app.models.baixa import Baixa
from app.schemas.anexo import AnexoCreate, AnexoUpdate, AnexoOut
from app.utils.logs import registrar_log
from app.core.security import get_current_user
from app.models.user import User
import shutil
import os
import uuid
import time
import re
from pathlib import Path

router = APIRouter(prefix="/anexos", tags=["Anexos"])

# ========================================
# 🔧 CONFIGURAÇÕES
# ========================================

UPLOAD_DIR = Path("uploads/anexos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Tipos de arquivo permitidos
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# ========================================
# 🛡️ FUNÇÕES DE SEGURANÇA
# ========================================

def validate_file_extension(filename: str) -> bool:
    """Valida se a extensão do arquivo é permitida."""
    extension = filename.split('.')[-1].lower()
    return extension in ALLOWED_EXTENSIONS

def get_safe_filename(original_filename: str) -> str:
    name, ext = os.path.splitext(original_filename)
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
    timestamp = int(time.time())
    return f"{safe_name}_{timestamp}{ext.lower()}"

def validate_file_size(file: UploadFile) -> bool:
    """Valida o tamanho do arquivo."""
    file.file.seek(0, 2)  # Move para o final
    file_size = file.file.tell()  # Obtém posição (tamanho)
    file.file.seek(0)  # Volta ao início
    return file_size <= MAX_FILE_SIZE

# ========================================
# 📤 CRIAR (UPLOAD)
# ========================================

@router.post("/", response_model=AnexoOut)
async def upload_anexo(
    patrimonio_id: Optional[int] = Form(None),
    baixa_id: Optional[int] = Form(None),
    tipo: str = Form(...),
    descricao: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Faz upload e cria registro de anexo.

    ⚠️ REGRAS:
    - Extensões permitidas: PDF, JPG, JPEG, PNG, DOC, DOCX, XLS, XLSX
    - Tamanho máximo: 10MB
    - Nomes de arquivo são sanitizados automaticamente
    - Pode ser vinculado a um patrimônio OU a uma baixa (não ambos)
    """

    # 🛡️ Validação 1: Extensão permitida
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido. Extensões válidas: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )

    # 🛡️ Validação 2: Tamanho do arquivo
    if not validate_file_size(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Arquivo muito grande. Tamanho máximo: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )

    # 🛡️ Validação 3: Não pode ter patrimonio_id E baixa_id ao mesmo tempo
    if patrimonio_id and baixa_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anexo não pode ser vinculado a patrimônio e baixa ao mesmo tempo. Escolha apenas um."
        )

    # 🛡️ Validação 4: Patrimônio existe (se fornecido)
    if patrimonio_id:
        patrimonio = db.query(Patrimonio).filter(Patrimonio.id == patrimonio_id).first()
        if not patrimonio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patrimônio não encontrado."
            )

    # 🛡️ Validação 5: Baixa existe (se fornecida)
    if baixa_id:
        baixa = db.query(Baixa).filter(Baixa.id == baixa_id).first()
        if not baixa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Baixa não encontrada."
            )

    # 🔒 Gera nome seguro para o arquivo
    safe_filename = get_safe_filename(file.filename)
    file_path = UPLOAD_DIR / safe_filename

    # 💾 Salva o arquivo no disco
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar arquivo: {str(e)}"
        )

    # 📝 Cria registro no banco de dados
    anexo = Anexo(
        patrimonio_id=patrimonio_id,
        baixa_id=baixa_id,
        tipo=tipo,
        caminho_arquivo=str(file_path),
        descricao=descricao,
        enviado_por=current_user.id,
    )

    db.add(anexo)
    db.commit()
    db.refresh(anexo)

    # 📋 Log automático
    registrar_log(
        db=db,
        acao="Upload de Anexo",
        entidade="anexos",
        entidade_id=anexo.id,
        usuario_id=current_user.id,
        detalhes={
            "arquivo_original": file.filename,
            "arquivo_salvo": safe_filename,
            "tipo": tipo,
            "descricao": descricao,
            "patrimonio_id": patrimonio_id,
            "baixa_id": baixa_id,
            "tamanho_bytes": file.size if hasattr(file, 'size') else 'desconhecido'
        }
    )

    return anexo


# ========================================
# 📥 DOWNLOAD SEGURO
# ========================================

@router.get("/{anexo_id}/download")
def download_anexo(
    anexo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Baixa um arquivo anexo.
    
    ⚠️ SEGURANÇA:
    - Requer autenticação
    - Verifica se arquivo existe no banco
    - Verifica se arquivo existe no disco
    """
    
    # Busca registro no banco
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrado."
        )
    
    # Verifica se arquivo existe no disco
    file_path = Path(anexo.caminho_arquivo)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico não encontrado no servidor."
        )
    
    # Determina o nome original (se possível) ou usa um genérico
    original_filename = f"anexo_{anexo_id}{file_path.suffix}"
    
    # Registra download no log
    registrar_log(
        db=db,
        acao="Download de Anexo",
        entidade="anexos",
        entidade_id=anexo.id,
        usuario_id=current_user.id,
        detalhes={"arquivo": str(file_path)}
    )
    
    # Retorna o arquivo
    return FileResponse(
        path=file_path,
        filename=original_filename,
        media_type='application/octet-stream'
    )


# ========================================
# 📋 LISTAR
# ========================================

@router.get("/", response_model=List[AnexoOut])
def list_anexos(
    patrimonio_id: Optional[int] = None,
    baixa_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lista todos os anexos cadastrados.

    Pode filtrar por:
    - patrimonio_id: anexos vinculados a um patrimônio específico
    - baixa_id: anexos vinculados a uma baixa específica
    """
    query = db.query(Anexo)

    if patrimonio_id:
        query = query.filter(Anexo.patrimonio_id == patrimonio_id)

    if baixa_id:
        query = query.filter(Anexo.baixa_id == baixa_id)

    return query.order_by(Anexo.criado_em.desc()).all()


# ========================================
# 🔍 DETALHAR
# ========================================

@router.get("/{anexo_id}", response_model=AnexoOut)
def get_anexo(anexo_id: int, db: Session = Depends(get_db)):
    """Retorna informações de um anexo específico."""
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrado."
        )
    return anexo


# ========================================
# ✏️ ATUALIZAR
# ========================================

@router.put("/{anexo_id}", response_model=AnexoOut)
def update_anexo(
    anexo_id: int,
    anexo_in: AnexoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza informações de um anexo.
    
    ⚠️ NOTA: Não permite alterar o arquivo. Para isso, delete e crie novo.
    """
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrado."
        )
    
    # Atualiza apenas campos permitidos (não caminho_arquivo)
    update_data = anexo_in.model_dump(exclude_unset=True, exclude={'caminho_arquivo'})
    
    for field, value in update_data.items():
        setattr(anexo, field, value)
    
    db.commit()
    db.refresh(anexo)
    
    # 📋 Log automático
    registrar_log(
        db=db,
        acao="Atualização de Anexo",
        entidade="anexos",
        entidade_id=anexo.id,
        usuario_id=current_user.id,
        detalhes={"alteracoes": update_data}
    )
    
    return anexo


# ========================================
# 🗑️ EXCLUIR
# ========================================

@router.delete("/{anexo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_anexo(
    anexo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove o registro e o arquivo físico.
    
    ⚠️ CUIDADO: Esta ação é irreversível!
    """
    anexo = db.query(Anexo).filter(Anexo.id == anexo_id).first()
    if not anexo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anexo não encontrado."
        )
    
    # Remove o arquivo físico se existir
    file_path = Path(anexo.caminho_arquivo)
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            # Log do erro mas não impede a exclusão do registro
            print(f"Erro ao remover arquivo físico: {e}")
    
    # Remove registro do banco
    db.delete(anexo)
    db.commit()
    
    # 📋 Log automático
    registrar_log(
        db=db,
        acao="Exclusão de Anexo",
        entidade="anexos",
        entidade_id=anexo_id,
        usuario_id=current_user.id,
        detalhes={
            "arquivo": str(file_path),
            "mensagem": f"Anexo {anexo_id} removido"
        }
    )
    
    return None


# ========================================
# 📊 ESTATÍSTICAS (OPCIONAL)
# ========================================

@router.get("/stats/summary")
def get_anexos_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna estatísticas sobre anexos do sistema.
    """
    total_anexos = db.query(Anexo).count()
    
    # Conta anexos por tipo
    tipos_count = {}
    for tipo in db.query(Anexo.tipo).distinct():
        count = db.query(Anexo).filter(Anexo.tipo == tipo[0]).count()
        tipos_count[tipo[0]] = count
    
    return {
        "total_anexos": total_anexos,
        "por_tipo": tipos_count,
        "upload_dir": str(UPLOAD_DIR),
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024)
    }