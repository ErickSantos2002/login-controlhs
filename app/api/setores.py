# app/api/setores.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.utils.db import get_db
from app.models.setor import Setor
from app.schemas.setor import SetorCreate, SetorUpdate, SetorOut

router = APIRouter(prefix="/setores", tags=["Setores"])

@router.post("/", response_model=SetorOut)
def create_setor(setor_in: SetorCreate, db: Session = Depends(get_db)):
    existente = db.query(Setor).filter(Setor.nome.ilike(setor_in.nome)).first()
    if existente:
        raise HTTPException(status_code=400, detail="Setor já cadastrado.")

    setor = Setor(**setor_in.model_dump())
    db.add(setor)
    db.commit()
    db.refresh(setor)
    return setor

@router.get("/", response_model=List[SetorOut])
def list_setores(db: Session = Depends(get_db)):
    return db.query(Setor).order_by(Setor.nome).all()

@router.get("/{setor_id}", response_model=SetorOut)
def get_setor(setor_id: int, db: Session = Depends(get_db)):
    setor = db.query(Setor).filter(Setor.id == setor_id).first()
    if not setor:
        raise HTTPException(status_code=404, detail="Setor não encontrado.")
    return setor

@router.put("/{setor_id}", response_model=SetorOut)
def update_setor(setor_id: int, setor_in: SetorUpdate, db: Session = Depends(get_db)):
    setor = db.query(Setor).filter(Setor.id == setor_id).first()
    if not setor:
        raise HTTPException(status_code=404, detail="Setor não encontrado.")

    for field, value in setor_in.model_dump(exclude_unset=True).items():
        setattr(setor, field, value)

    db.commit()
    db.refresh(setor)
    return setor

@router.delete("/{setor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_setor(setor_id: int, db: Session = Depends(get_db)):
    setor = db.query(Setor).filter(Setor.id == setor_id).first()
    if not setor:
        raise HTTPException(status_code=404, detail="Setor não encontrado.")

    db.delete(setor)
    db.commit()
    return None
