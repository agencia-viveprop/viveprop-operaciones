from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.movimiento import EntityType, TipoMovimiento
from app.models.usuario import Usuario

router = APIRouter(prefix="/tipos-movimiento", tags=["tipos-movimiento"])


class TipoMovimientoOut(BaseModel):
    codigo: str
    nombre: str
    etapa_resultante: str | None
    orden: int | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TipoMovimientoOut])
def listar(
    entity_type: EntityType,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    query = (
        select(TipoMovimiento)
        .where(TipoMovimiento.entity_type == entity_type, TipoMovimiento.activo.is_(True))
        .order_by(TipoMovimiento.orden)
    )
    return db.scalars(query).all()
