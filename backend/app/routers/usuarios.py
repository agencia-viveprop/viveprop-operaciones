from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.models.usuario import RolUsuario, Usuario
from app.security import hash_password

router = APIRouter(prefix="/admin/usuarios", tags=["admin-usuarios"], dependencies=[Depends(require_role(RolUsuario.admin))])


class UsuarioOut(BaseModel):
    id: int
    email: str
    nombre: str
    rol: RolUsuario
    activo: bool

    model_config = {"from_attributes": True}


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str
    password: str
    rol: RolUsuario = RolUsuario.operaciones


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    rol: RolUsuario | None = None
    activo: bool | None = None
    password: str | None = None


@router.get("", response_model=list[UsuarioOut])
def listar(db: Session = Depends(get_db)):
    return db.scalars(select(Usuario).order_by(Usuario.email)).all()


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear(payload: UsuarioCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Usuario).where(Usuario.email == payload.email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese email ya tiene una cuenta")

    usuario = Usuario(
        email=payload.email,
        nombre=payload.nombre,
        rol=payload.rol,
        password_hash=hash_password(payload.password),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def actualizar(usuario_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db)):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if payload.nombre is not None:
        usuario.nombre = payload.nombre
    if payload.rol is not None:
        usuario.rol = payload.rol
    if payload.activo is not None:
        usuario.activo = payload.activo
    if payload.password:
        usuario.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(usuario)
    return usuario
