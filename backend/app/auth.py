import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.usuario import JERARQUIA_ROLES, RolUsuario, Sesion, Usuario, VistaComo

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


# El detalle viaja tal cual al front, que lo usa para distinguir "tu sesion se
# vencio" de "tenes que cambiar la clave". Sin una marca estable habria que
# comparar textos.
CLAVE_VENCIDA = "debe_cambiar_password"


# --- Ver como otro usuario (`D-120`) -------------------------------------------
#
# Un admin puede ver la app como un usuario de operaciones o gerencia. La vista
# vive en **su propia sesión** (`Sesion.viendo_como_id`): `resolver_usuario`
# devuelve al usuario visto, así que el menú, las rutas y cada permiso de la API
# responden exactamente como para esa persona, sin tocar ningún endpoint.
#
# **Es solo para mirar.** La bitácora y las obligaciones guardan quién hizo cada
# cosa; un cambio hecho desde la vista quedaría a nombre del otro usuario. Por eso
# cualquier método que no sea de lectura se rechaza acá, en un solo lugar, salvo
# volver al propio usuario.

METODOS_DE_LECTURA = {"GET", "HEAD", "OPTIONS"}
RUTAS_PERMITIDAS_EN_VISTA = {"/api/auth/dejar-de-ver-como"}
SOLO_LECTURA = (
    "Estás viendo la app como otro usuario, y eso es solo para mirar. "
    "Vuelve a tu usuario para hacer cambios."
)


def iniciar_vista(db: Session, sesion: Sesion, admin: Usuario, visto: Usuario) -> None:
    """Empieza a ver como `visto` y deja el registro. No comitea."""
    sesion.viendo_como_id = visto.id
    db.add(VistaComo(admin_id=admin.id, usuario_id=visto.id, sesion_id=sesion.id, inicio=_utcnow()))


def terminar_vista(db: Session, sesion: Sesion) -> None:
    """Vuelve al propio usuario y cierra el registro abierto. No comitea."""
    sesion.viendo_como_id = None
    abiertos = db.query(VistaComo).filter(VistaComo.sesion_id == sesion.id, VistaComo.fin.is_(None))
    for registro in abiertos:
        registro.fin = _utcnow()


def admin_real(request: Request) -> Usuario | None:
    """El admin detrás de una vista, o `None` si la sesión es la de su dueño."""
    return getattr(request.state, "admin_real", None)


def resolver_usuario(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    session_id: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> Usuario:
    """El usuario de la sesion, **sin** exigir que la clave este al dia.

    La usan los tres endpoints que tienen que funcionar con una clave temporal:
    `/me` para que el front sepa que hay que cambiarla, `cambiar-clave` para
    poder cambiarla, y `logout` para poder salir. Cualquier otro endpoint usa
    `get_current_user`, que si lo exige.

    Si la sesión es de un admin viendo como otro usuario, devuelve **al usuario
    visto** y deja al admin en `request.state.admin_real` (`D-120`).
    """
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

    request.state.sesion = sesion
    request.state.admin_real = None
    if sesion.viendo_como_id is None:
        return usuario

    visto = db.get(Usuario, sesion.viendo_como_id)
    # Se revalida en cada request: si al admin le quitaron el rol, o el usuario
    # visto se desactivó o pasó a admin, la vista se termina sola.
    vigente = (
        usuario.rol == RolUsuario.admin
        and visto is not None
        and visto.activo
        and visto.rol != RolUsuario.admin
    )
    if not vigente:
        terminar_vista(db, sesion)
        db.commit()
        return usuario

    if request.method not in METODOS_DE_LECTURA and request.url.path not in RUTAS_PERMITIDAS_EN_VISTA:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=SOLO_LECTURA)
    request.state.admin_real = usuario
    return visto


def get_current_user(request: Request, usuario: Usuario = Depends(resolver_usuario)) -> Usuario:
    """El usuario, exigiendo que su contrasena este al dia.

    **La guarda vive aca y no en la pantalla.** Si solo la aplicara el front, la
    clave temporal serviria para usar toda la API con un cliente cualquiera, y el
    cambio forzado seria decorativo.

    No aplica en una vista de admin: la clave temporal es del otro usuario, y el
    admin que lo está viendo no la va a cambiar por él.
    """
    if usuario.debe_cambiar_password and admin_real(request) is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CLAVE_VENCIDA,
        )
    return usuario


def require_role(minimo: RolUsuario):
    def dependency(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if JERARQUIA_ROLES[usuario.rol] < JERARQUIA_ROLES[minimo]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes")
        return usuario

    return dependency
