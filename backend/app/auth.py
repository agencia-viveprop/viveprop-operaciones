import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.usuario import JERARQUIA_ROLES, RolUsuario, Sesion, Usuario

COOKIE_NAME = "session_id"
SLIDING_WINDOW = timedelta(hours=12)
ABSOLUTE_MAX = timedelta(days=30)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    # SQLite no conserva tzinfo en columnas timestamptz (llegan "naive"); Postgres si.
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def crear_sesion(db: Session, usuario: Usuario, ip: str | None, user_agent: str | None) -> Sesion:
    ahora = _utcnow()
    sesion = Sesion(usuario_id=usuario.id, creado_en=ahora, expira_en=ahora + SLIDING_WINDOW, ip=ip, user_agent=user_agent)
    db.add(sesion)
    usuario.ultimo_login = ahora
    db.commit()
    db.refresh(sesion)
    return sesion


def set_session_cookie(response: Response, sesion_id: uuid.UUID) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=str(sesion_id),
        httponly=True,
        # Seguro por defecto: solo un ambiente local declarado la deja salir sin
        # `secure`. Ver `Settings.es_local` para por qué es al revés que antes.
        secure=not settings.es_local,
        samesite="lax",
        max_age=int(ABSOLUTE_MAX.total_seconds()),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


def get_current_user(
    response: Response,
    db: Session = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Usuario:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    if not session_id:
        raise unauthorized

    try:
        sesion_uuid = uuid.UUID(session_id)
    except ValueError:
        raise unauthorized

    sesion = db.get(Sesion, sesion_uuid)
    if sesion is None:
        raise unauthorized

    ahora = _utcnow()
    sesion_expira_en = _aware(sesion.expira_en)
    sesion_creado_en = _aware(sesion.creado_en)
    expirada = sesion_expira_en < ahora or (ahora - sesion_creado_en) > ABSOLUTE_MAX
    if expirada:
        db.delete(sesion)
        db.commit()
        raise unauthorized

    usuario = db.get(Usuario, sesion.usuario_id)
    if usuario is None or not usuario.activo:
        raise unauthorized

    # Ventana deslizante: se extiende en cada request, sin pasar el tope absoluto de 30 dias
    nueva_expiracion = min(ahora + SLIDING_WINDOW, sesion_creado_en + ABSOLUTE_MAX)
    if nueva_expiracion > sesion_expira_en:
        sesion.expira_en = nueva_expiracion
        db.commit()
        set_session_cookie(response, sesion.id)

    return usuario


def require_role(minimo: RolUsuario):
    def dependency(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if JERARQUIA_ROLES[usuario.rol] < JERARQUIA_ROLES[minimo]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return usuario

    return dependency
