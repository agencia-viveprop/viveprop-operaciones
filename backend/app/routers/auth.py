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
from app.services.intentos_login import (
    ClaveDebil,
    DemasiadosIntentos,
    registrar_exito,
    registrar_fallo,
    validar_clave,
    verificar,
)

# Hash de una contrasena que nadie tiene, para gastar el mismo tiempo cuando el
# email no existe. Sin esto, un email desconocido responde en microsegundos y uno
# real en ~70 ms: la diferencia dice quien tiene cuenta. Se calcula una vez al
# importar, no en cada intento.
_HASH_SENUELO = hash_password("no-existe-ningun-usuario-con-esta-clave")

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
    """Entrada con límite de intentos y sin fuga de tiempos.

    **El límite se evalúa antes de verificar el hash.** Cada verificación Argon2id
    cuesta ~70 ms de CPU; si el límite se aplicara después, frenaría la fuerza
    bruta pero no la saturación, que es la otra mitad del problema.

    **Y siempre se verifica un hash, exista o no el usuario.** Antes, un email
    desconocido respondía en microsegundos y uno real en ~70 ms, y esa diferencia
    revelaba qué correos tienen cuenta. Ahora el camino del email inexistente
    gasta lo mismo contra un hash señuelo.
    """
    ip = request.client.host if request.client else None
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contraseña incorrectos"
    )

    try:
        verificar(db, payload.email, ip)
    except DemasiadosIntentos as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)
        ) from exc

    usuario = db.scalar(select(Usuario).where(Usuario.email == payload.email))
    # El hash a comparar: el del usuario, o el señuelo. Las dos ramas cuestan lo
    # mismo, así que el tiempo de respuesta no dice si el email existe.
    hash_a_probar = usuario.password_hash if usuario is not None else _HASH_SENUELO
    clave_correcta = verify_password(hash_a_probar, payload.password)

    if usuario is None or not usuario.activo or not clave_correcta:
        registrar_fallo(db, payload.email, ip)
        raise credenciales_invalidas

    registrar_exito(db, payload.email, ip)
    sesion = crear_sesion(
        db, usuario, ip=ip, user_agent=request.headers.get("user-agent")
    )
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
    try:
        validar_clave(payload.clave_nueva)
    except ClaveDebil as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    usuario.password_hash = hash_password(payload.clave_nueva)
    usuario.debe_cambiar_password = False
    db.commit()
    return {"ok": True}
