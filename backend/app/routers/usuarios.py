import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.usuario import RolUsuario, Sesion, Usuario
from app.security import hash_password

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

    model_config = {"from_attributes": True}


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


class UsuarioUpdate(BaseModel):
    email: EmailStr | None = None
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

    if payload.email is not None and payload.email != usuario.email:
        if db.scalar(select(Usuario).where(Usuario.email == payload.email)) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese email ya tiene una cuenta")
        usuario.email = payload.email
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
            "No podés resetear tu propia contraseña. Usá «Cambiar contraseña».",
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
