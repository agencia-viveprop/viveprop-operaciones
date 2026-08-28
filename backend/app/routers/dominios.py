"""Los dominios de correo de la organización. Solo admin.

Va en su propio router y no colgado de `/admin/usuarios` para que la URL diga qué
es y para no meter rutas nuevas al lado de `/{usuario_id}`, donde un `dominios`
como path param es una colisión esperando. La guarda de rol es la misma.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import require_role
from app.db import get_db
from app.models.usuario import RolUsuario, Usuario
from app.services import dominios_organizacion as servicio

router = APIRouter(
    prefix="/admin/dominios",
    tags=["admin-dominios"],
    dependencies=[Depends(require_role(RolUsuario.admin))],
)


class DominioOut(BaseModel):
    id: int
    dominio: str
    nombre: str
    activo: bool

    model_config = {"from_attributes": True}


class DominioCreate(BaseModel):
    dominio: str
    # Para qué es, cuando el dominio no lo dice solo: «Dataprop» al lado de
    # dataprop.cl. Opcional.
    nombre: str | None = None


def _salida(fila) -> DominioOut:
    return DominioOut(id=fila.id, dominio=fila.codigo, nombre=fila.nombre, activo=fila.activo)


@router.get("", response_model=list[DominioOut])
def listar(db: Session = Depends(get_db)):
    return [_salida(f) for f in servicio.listar(db)]


@router.post("", response_model=DominioOut, status_code=status.HTTP_201_CREATED)
def agregar(payload: DominioCreate, db: Session = Depends(get_db)):
    try:
        return _salida(servicio.agregar(db, payload.dominio, payload.nombre))
    except servicio.DominioDuplicado as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except servicio.DominioInvalido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.delete("/{dominio_id}", response_model=DominioOut)
def desactivar(
    dominio_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_role(RolUsuario.admin)),
):
    """Apaga el dominio. No borra la fila ni toca a los usuarios que ya existen.

    Los usuarios creados con ese dominio siguen entrando: esta lista se aplica al
    crear una cuenta o al cambiarle el correo, no re-valida a nadie. Para cortarle
    el acceso a alguien está el switch `activo` de su usuario, que se chequea en
    cada request.
    """
    fila = servicio.desactivar(db, dominio_id)
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese dominio no existe")
    return _salida(fila)
