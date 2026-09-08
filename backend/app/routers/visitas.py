from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.usuario import RolUsuario, Usuario
from app.models.visita import Visita
from app.services.importar_visitas import ImportarVisitasResumen, importar_visitas

router = APIRouter(prefix="/visitas", tags=["visitas"])


class VisitaOut(BaseModel):
    id: int
    propiedad: str
    direccion: str | None
    tipo: str | None
    mercado: str | None
    cliente: str | None
    rut: str | None
    objetivo_compra: str | None
    fecha_solicitada: datetime | None
    etapa: str | None
    solicitada_el: datetime | None

    model_config = {"from_attributes": True}


@router.get("", response_model=list[VisitaOut])
def listar(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    query = select(Visita).order_by(Visita.solicitada_el.desc(), Visita.id.desc())
    return db.scalars(query).all()


@router.post("/importar", response_model=ImportarVisitasResumen)
async def importar(
    archivo: UploadFile,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    if not archivo.filename or not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo debe ser un .xlsx")

    contenido = await archivo.read()
    try:
        return importar_visitas(db, contenido)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{visita_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    visita_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    visita = db.get(Visita, visita_id)
    if visita is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Visita no encontrada")
    db.delete(visita)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
