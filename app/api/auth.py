# app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserLogin, UserOut, UserUpdate
from app.models.user import User
from app.models.role import Role
from app.utils.db import get_db
from app.core.security import hash_password, verify_password, create_access_token
from sqlalchemy import func
from app.core.security import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Busca a role pelo nome, ou usa 'comum' como padrão
    role_name = user_in.role_name or "comum"
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{role_name}' not found.")
    print("DEBUG PASSWORD:", repr(user_in.password), type(user_in.password), len(user_in.password))

    new_user = User(
        username=user_in.username.lower(),
        password_hash=hash_password(user_in.password),
        role_id=role.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    from sqlalchemy import func  # garantir import

    user = (
        db.query(User)
        .filter(func.lower(User.username) == user_in.username.lower())
        .first()
    )

    if not user or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.name}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.name,
        "username": user.username,
        "user_id": user.id
    }

@router.get("/users/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista todos os usuários cadastrados no sistema.
    Requer autenticação.
    """
    users = db.query(User).all()
    return users

@router.get("/users/{user_id}", response_model=UserOut)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário {user_id} não encontrado")
    return user

@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.username:
        user.username = user_in.username.lower()
    if user_in.password:
        user.password_hash = hash_password(user_in.password)
    if user_in.role_name:
        role = db.query(Role).filter(Role.name == user_in.role_name).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"Role '{user_in.role_name}' not found.")
        user.role_id = role.id

    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user