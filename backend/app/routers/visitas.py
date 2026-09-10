from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.usuario import RolUsuario, Usuario
from app.models.visita import Visita
from app.services.estructura_archivo import EstructuraArchivo
from app.services.importar_visitas import ImportarVisitasResumen, importar_visitas
from app.services.plantilla_visitas import estructura_importacion, generar_plantilla

router = APIRouter(prefix="/visitas", tags=["visitas"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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
    corredor: str | None
    solicitada_el: datetime | None

    model_config = {"from_attributes": True}


# Las dos van antes de "/{visita_id}"-like paths por si alguna vez se agrega
# una, igual que en canjes: FastAPI resuelve por orden de registro.
@router.get("/plantilla/estructura", response_model=EstructuraArchivo)
def estructura_del_archivo(usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    """Qué columnas espera el export de la consola, para verlo antes de subir nada."""
    return estructura_importacion()


@router.get("/plantilla")
def descargar_plantilla(usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    """El .xlsx vacío con los 11 encabezados exactos.

    No es para llenarlo a mano --el archivo sale de la consola-- sino para
    comparar encabezados cuando la carga falla y no se entiende por qué.
    """
    return Response(
        content=generar_plantilla(),
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="plantilla-visitas.xlsx"'},
    )


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


class EliminarTodasOut(BaseModel):
    eliminadas: int


@router.delete("", response_model=EliminarTodasOut)
def eliminar_todas(db: Session = Depends(get_db), usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    """Vacía la tabla entera, para volver a cargar desde cero.

    **Es recuperable**, y por eso no exige admin como el borrado de un canje
    (`D-096`): con la carga en modo "actualiza en vez de duplicar", reimportar
    el mismo archivo repone exactamente lo que había. Existe porque las cargas
    de antes de esa regla dejaron duplicados que no valía la pena sacar de a
    uno.
    """
    cantidad = db.query(Visita).delete()
    db.commit()
    return EliminarTodasOut(eliminadas=cantidad)
