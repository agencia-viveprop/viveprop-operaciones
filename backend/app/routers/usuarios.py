import secrets
import string
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.usuario import RolUsuario, Sesion, Usuario
from app.security import hash_password
from app.services import dominios_organizacion as servicio_dominios
from app.services.intentos_login import ClaveDebil, validar_clave


def _autorizacion_externa(
    db: Session, email: str, autoriza_externo: bool, admin: Usuario
) -> tuple[int | None, datetime | None]:
    """Devuelve el rastro a guardar, o rechaza el alta.

    Si el correo es de un dominio de la organización, no hay nada que autorizar y
    los dos campos quedan nulos. Si no lo es, hace falta que el admin lo autorice
    explícitamente, y queda registrado quién y cuándo.

    **Por qué así y no una lista de dominios permitidos.** Un director o un
    advisor puede tener un correo cualquiera, y son parte del diseño de la app.
    Habilitar su dominio para dejarlo entrar significaría abrir `gmail.com`
    entero y para siempre: después del primer caso la lista dejaría de decir algo
    y seguiría pareciendo un control. La excepción es por persona, y con nombre.

    Y la protección que se busca es contra el dedazo, no contra la intrusión: la
    app no manda correos, así que una dirección equivocada no le entrega nada a
    nadie. Quien puede juzgar si «ese correo raro» es intencional es el admin que
    lo está escribiendo, en el momento en que lo escribe.
    """
    if servicio_dominios.es_de_la_organizacion(db, email):
        return None, None
    if not autoriza_externo:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "El correo no es de la organización. Para crear un usuario externo hay que "
            "autorizarlo explícitamente.",
        )
    return admin.id, datetime.now(timezone.utc)


def _validar_clave_o_400(clave: str) -> None:
    try:
        validar_clave(clave)
    except ClaveDebil as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

# Sin I, l, 1, O ni 0: la clave se dicta por telefono o se copia de un chat, y
# esos cinco caracteres se confunden entre si.
ALFABETO_TEMPORAL = (
    "".join(c for c in string.ascii_letters if c not in "IlO")
    + "".join(c for c in string.digits if c not in "10")
)
LARGO_TEMPORAL = 12

router = APIRouter(prefix="/admin/usuarios", tags=["admin-usuarios"], dependencies=[Depends(require_role(RolUsuario.admin))])


class UsuarioOut(BaseModel):
    id: int
    email: str
    nombre: str
    rol: RolUsuario
    activo: bool
    debe_cambiar_password: bool = False
    # El rastro del acceso externo, resuelto para que la pantalla no tenga que
    # cruzar ids: quién lo autorizó, por nombre, y cuándo.
    es_externo: bool = False
    externo_autorizado_por: str | None = None
    externo_autorizado_en: datetime | None = None

    model_config = {"from_attributes": True}


def _salida(usuario: Usuario) -> UsuarioOut:
    autor = usuario.externo_autorizado_por
    return UsuarioOut(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol,
        activo=usuario.activo,
        debe_cambiar_password=usuario.debe_cambiar_password,
        # Externo es tener la autorización, no que el correo se vea de fuera: si
        # mañana se agrega su dominio a la lista, el hecho de que se autorizó a
        # mano no deja de ser cierto.
        es_externo=usuario.externo_autorizado_en is not None,
        # El nombre de quien autorizó, y su correo si la cuenta ya no existe --el
        # `SET NULL` deja la fecha sin autor, y decir solo "externo" perdería la
        # mitad del rastro--.
        externo_autorizado_por=(autor.nombre if autor is not None else None),
        externo_autorizado_en=usuario.externo_autorizado_en,
    )


class ClaveReseteada(BaseModel):
    """La clave temporal se devuelve una sola vez, al resetear.

    No se guarda en claro en ninguna parte -- lo que queda en la base es su
    hash, igual que cualquier otra. Si se pierde, se resetea de nuevo.
    """

    usuario_id: int
    email: str
    clave_temporal: str


class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str
    password: str
    rol: RolUsuario = RolUsuario.operaciones
    # El admin declara que sabe que el correo no es de la organización y que
    # autoriza igual ese acceso. Por defecto en `False`: la autorización tiene
    # que ser un acto, no un descuido del que llama a la API.
    autoriza_externo: bool = False


class UsuarioUpdate(BaseModel):
    email: EmailStr | None = None
    nombre: str | None = None
    rol: RolUsuario | None = None
    activo: bool | None = None
    password: str | None = None
    autoriza_externo: bool = False


@router.get("", response_model=list[UsuarioOut])
def listar(db: Session = Depends(get_db)):
    return [_salida(u) for u in db.scalars(select(Usuario).order_by(Usuario.email)).all()]


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_user),
):
    autor_id, autorizado_en = _autorizacion_externa(db, payload.email, payload.autoriza_externo, admin)
    _validar_clave_o_400(payload.password)
    if db.scalar(select(Usuario).where(Usuario.email == payload.email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese email ya tiene una cuenta")

    usuario = Usuario(
        email=payload.email,
        nombre=payload.nombre,
        rol=payload.rol,
        password_hash=hash_password(payload.password),
        externo_autorizado_por_id=autor_id,
        externo_autorizado_en=autorizado_en,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return _salida(usuario)


@router.patch("/{usuario_id}", response_model=UsuarioOut)
def actualizar(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_user),
):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if payload.email is not None and payload.email != usuario.email:
        autor_id, autorizado_en = _autorizacion_externa(
            db, payload.email, payload.autoriza_externo, admin
        )
        if db.scalar(select(Usuario).where(Usuario.email == payload.email)) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese email ya tiene una cuenta")
        usuario.email = payload.email
        # El rastro sigue al correo: si pasa a uno de la organización, la
        # autorización deja de aplicar --ese correo ya no la necesita-- y si pasa
        # a otro externo, queda quién lo autorizó esta vez.
        usuario.externo_autorizado_por_id = autor_id
        usuario.externo_autorizado_en = autorizado_en
    if payload.nombre is not None:
        usuario.nombre = payload.nombre
    if payload.rol is not None:
        usuario.rol = payload.rol
    if payload.activo is not None:
        usuario.activo = payload.activo
    if payload.password:
        _validar_clave_o_400(payload.password)
        usuario.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(usuario)
    return _salida(usuario)


@router.post("/{usuario_id}/resetear-clave", response_model=ClaveReseteada)
def resetear_clave(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(get_current_user),
):
    """Genera una clave temporal y obliga a cambiarla en el primer ingreso.

    **Cierra las sesiones abiertas de esa persona.** Sin eso, una pestaña que ya
    estaba logueada seguiria funcionando con todos los permisos y el cambio
    forzado no se aplicaria nunca: el flag solo se mira al resolver la sesion, y
    esa sesion ya resuelta seguiria viva hasta doce horas.

    **La clave la genera el sistema, no la elige el admin.** Una que alguien
    inventa en el momento termina siendo "viveprop2026", y ademas hay que
    transmitirla por un canal aparte igual. Se devuelve una sola vez.

    **No se puede resetear la propia.** Para eso esta "cambiar contrasena": si el
    unico admin se reseteara a si mismo y perdiera el texto que aparece una sola
    vez, quedaria fuera de la app sin nadie que pueda ayudarlo.
    """
    if usuario_id == admin.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No puedes resetear tu propia contraseña. Usa «Cambiar contraseña».",
        )

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    temporal = "".join(secrets.choice(ALFABETO_TEMPORAL) for _ in range(LARGO_TEMPORAL))
    usuario.password_hash = hash_password(temporal)
    usuario.debe_cambiar_password = True
    db.execute(delete(Sesion).where(Sesion.usuario_id == usuario.id))
    db.commit()

    return ClaveReseteada(
        usuario_id=usuario.id, email=usuario.email, clave_temporal=temporal
    )
