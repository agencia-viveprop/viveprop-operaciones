import uuid

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    COOKIE_NAME,
    clear_session_cookie,
    crear_sesion,
    resolver_usuario,
    set_session_cookie,
)
from app.db import get_db
from app.models.usuario import Sesion, Usuario
from app.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    id: int
    email: str
    nombre: str
    rol: str
    # El front lo usa para tapar la app con el formulario de cambio de clave. La
    # guarda de verdad esta en la API (ver `get_current_user`); esto solo evita
    # que la persona choque contra un 403 en cada pantalla sin saber por que.
    debe_cambiar_password: bool = False

    model_config = {"from_attributes": True}


@router.post("/login", response_model=UsuarioOut)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    credenciales_invalidas = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos")

    if usuario is None or not usuario.activo:
        raise credenciales_invalidas
    if not verify_password(usuario.password_hash, payload.password):
        raise credenciales_invalidas

    sesion = crear_sesion(db, usuario, ip=request.client.host if request.client else None, user_agent=request.headers.get("user-agent"))
    set_session_cookie(response, sesion.id)
    return usuario


@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db), session_id: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if session_id:
        try:
            sesion = db.get(Sesion, uuid.UUID(session_id))
        except ValueError:
            sesion = None
        if sesion is not None:
            db.delete(sesion)
            db.commit()
    clear_session_cookie(response)
    return {"ok": True}


@router.get("/me", response_model=UsuarioOut)
def me(usuario: Usuario = Depends(resolver_usuario)):
    return usuario


class CambiarClaveRequest(BaseModel):
    clave_actual: str
    clave_nueva: str


@router.post("/cambiar-clave")
def cambiar_clave(
    payload: CambiarClaveRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(resolver_usuario),
):
    """Cambia la propia clave, y limpia la marca de cambio forzado.

    Usa `resolver_usuario` y no `get_current_user` porque tiene que funcionar
    **justamente** cuando la clave esta marcada como temporal: con la dependencia
    estricta, la persona quedaria bloqueada del unico endpoint que la desbloquea.
    """
    if not verify_password(usuario.password_hash, payload.clave_actual):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual no es correcta")
    if payload.clave_nueva == payload.clave_actual:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña nueva tiene que ser distinta de la actual",
        )

    usuario.password_hash = hash_password(payload.clave_nueva)
    usuario.debe_cambiar_password = False
    db.commit()
    return {"ok": True}
