from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.usuario import RolUsuario, Usuario
from app.services.bandeja_canjes import Bandeja, obtener_bandeja
from app.services.estructura_archivo import EstructuraArchivo
from app.services.importar_canjes import ImportarCanjesResumen, importar_canjes
from app.services.movimientos import (
    MovimientoError,
    crear_movimiento_canje,
    eliminar_movimiento_canje,
)
from app.services.plantilla_canjes import estructura_importacion, generar_plantilla
from app.services.reportes_canjes import ResumenCanjes, obtener_resumen_canjes

router = APIRouter(prefix="/canjes", tags=["canjes"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class CanjeOut(BaseModel):
    id: int
    fecha_solicitud: datetime
    fecha_cierre: datetime | None
    estado: CanjeEstado
    etapa: CanjeEtapa
    corredor_solicitante_nombre: str | None
    corredor_solicitante_email: str | None
    corredor_propietario_nombre: str | None
    corredor_propietario_email: str | None
    tipo_operacion: OperacionTipo | None
    tipo_inmueble: str | None
    comuna: str | None
    direccion: str | None
    valor_prop: float | None
    moneda_valor: MonedaTipo | None
    link_propiedad: str | None
    valor_negocio: float | None
    valor_negocio_moneda: MonedaTipo | None
    comision_dbrokers: float | None
    comision_dbrokers_moneda: MonedaTipo | None
    notas: str | None
    gestionado_en_app: bool

    model_config = {"from_attributes": True}


class CanjeCreate(BaseModel):
    id: int
    fecha_solicitud: datetime
    estado: CanjeEstado = CanjeEstado.ACTIVO
    etapa: CanjeEtapa = CanjeEtapa.SIN_ETAPA
    corredor_solicitante_nombre: str | None = None
    corredor_solicitante_email: str | None = None
    corredor_propietario_nombre: str | None = None
    corredor_propietario_email: str | None = None
    tipo_operacion: OperacionTipo | None = None
    tipo_inmueble: str | None = None
    comuna: str | None = None
    direccion: str | None = None
    valor_prop: float | None = None
    moneda_valor: MonedaTipo | None = None
    link_propiedad: str | None = None
    valor_negocio: float | None = None
    valor_negocio_moneda: MonedaTipo | None = None
    comision_dbrokers: float | None = None
    comision_dbrokers_moneda: MonedaTipo | None = None
    notas: str | None = None


class CanjeUpdate(BaseModel):
    fecha_cierre: datetime | None = None
    estado: CanjeEstado | None = None
    etapa: CanjeEtapa | None = None
    corredor_solicitante_nombre: str | None = None
    corredor_solicitante_email: str | None = None
    corredor_propietario_nombre: str | None = None
    corredor_propietario_email: str | None = None
    tipo_operacion: OperacionTipo | None = None
    tipo_inmueble: str | None = None
    comuna: str | None = None
    direccion: str | None = None
    valor_prop: float | None = None
    moneda_valor: MonedaTipo | None = None
    link_propiedad: str | None = None
    valor_negocio: float | None = None
    valor_negocio_moneda: MonedaTipo | None = None
    comision_dbrokers: float | None = None
    comision_dbrokers_moneda: MonedaTipo | None = None
    notas: str | None = None


# Va antes de "/{canje_id}": FastAPI resuelve por orden de registro, y si esta
# ruta quedara despues, "bandeja" se intentaria parsear como un id.
@router.get("/bandeja", response_model=Bandeja)
def bandeja(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    """Que canje hay que tocar hoy, ordenado por urgencia (sprint 20)."""
    return obtener_bandeja(db)


@router.get("/reportes/resumen", response_model=ResumenCanjes)
def reportes_resumen(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    return obtener_resumen_canjes(db)


# Las dos van antes de "/{canje_id}", por el mismo motivo que "/bandeja".
@router.get("/plantilla/estructura", response_model=EstructuraArchivo)
def estructura_del_archivo(usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    """Qué columnas espera el export de Dataprop, para verlo antes de subir nada."""
    return estructura_importacion()


@router.get("/plantilla")
def descargar_plantilla(usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    """El .xlsx vacío con los 16 encabezados exactos.

    No es para llenarlo a mano --el archivo sale de Dataprop-- sino para comparar
    encabezados cuando la carga falla y no se entiende por qué.
    """
    return Response(
        content=generar_plantilla(),
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="plantilla-canjes.xlsx"'},
    )


@router.get("", response_model=list[CanjeOut])
def listar(
    estado: CanjeEstado | None = None,
    etapa: CanjeEtapa | None = None,
    comuna: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    query = select(Canje)
    if estado is not None:
        query = query.where(Canje.estado == estado)
    if etapa is not None:
        query = query.where(Canje.etapa == etapa)
    if comuna:
        query = query.where(Canje.comuna.ilike(f"%{comuna}%"))
    query = query.order_by(Canje.fecha_solicitud.desc())
    return db.scalars(query).all()


@router.get("/{canje_id}", response_model=CanjeOut)
def obtener(canje_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canje no encontrado")
    return canje


@router.post("", response_model=CanjeOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CanjeCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    if db.get(Canje, payload.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un canje con ese ID")

    canje = Canje(**payload.model_dump(), gestionado_en_app=True)
    db.add(canje)
    db.commit()
    db.refresh(canje)
    return canje


@router.patch("/{canje_id}", response_model=CanjeOut)
def actualizar(
    canje_id: int,
    payload: CanjeUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canje no encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(canje, campo, valor)
    canje.gestionado_en_app = True

    db.commit()
    db.refresh(canje)
    return canje


@router.post("/importar", response_model=ImportarCanjesResumen)
async def importar(
    archivo: UploadFile,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    if not archivo.filename or not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo debe ser un .xlsx")

    contenido = await archivo.read()
    try:
        return importar_canjes(db, contenido)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


class MovimientoOut(BaseModel):
    id: int
    tipo_movimiento: str
    tipo_nombre: str
    etapa_resultante: str | None
    fecha: datetime
    autor_nombre: str | None
    comentario: str | None
    # Cuándo se prometió volver a mirar el canje. El del movimiento más reciente
    # es el que manda en «Qué me toca hoy».
    proximo_seguimiento: date | None


class MovimientoCreate(BaseModel):
    tipo_movimiento: str
    comentario: str | None = None
    fecha: datetime | None = None
    # Opcional. Sin él, el servicio agenda dos días corridos hacia adelante,
    # corridos al siguiente hábil si caen fin de semana.
    proximo_seguimiento: date | None = None


def _a_movimiento_out(db: Session, m: Movimiento) -> MovimientoOut:
    tipo = db.get(TipoMovimiento, m.tipo_movimiento)
    autor = db.get(Usuario, m.autor_id) if m.autor_id else None
    return MovimientoOut(
        id=m.id,
        tipo_movimiento=m.tipo_movimiento,
        tipo_nombre=tipo.nombre if tipo else m.tipo_movimiento,
        etapa_resultante=m.etapa_resultante,
        fecha=m.fecha,
        autor_nombre=autor.nombre if autor else None,
        comentario=m.comentario,
        proximo_seguimiento=m.proximo_seguimiento,
    )


@router.get("/{canje_id}/movimientos", response_model=list[MovimientoOut])
def listar_movimientos(canje_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    if db.get(Canje, canje_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canje no encontrado")
    movimientos = db.scalars(
        select(Movimiento)
        .where(Movimiento.entity_type == EntityType.canje, Movimiento.entity_id == canje_id)
        .order_by(Movimiento.fecha.desc())
    ).all()
    return [_a_movimiento_out(db, m) for m in movimientos]


@router.post("/{canje_id}/movimientos", response_model=MovimientoOut, status_code=status.HTTP_201_CREATED)
def crear_movimiento(
    canje_id: int,
    payload: MovimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    try:
        movimiento = crear_movimiento_canje(
            db,
            canje_id,
            payload.tipo_movimiento,
            usuario.id,
            payload.comentario,
            payload.fecha,
            payload.proximo_seguimiento,
        )
    except MovimientoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _a_movimiento_out(db, movimiento)


@router.delete(
    "/{canje_id}/movimientos/{movimiento_id}", status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_movimiento(
    canje_id: int,
    movimiento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    """Borra un movimiento mal registrado y recalcula lo que dependía de él.

    Lo puede hacer quien los registra: corregir un tipeo propio no debería
    necesitar a otra persona. La etapa se vuelve a derivar de lo que queda y, si
    el borrado era la cancelación, el canje vuelve a activo.
    """
    try:
        eliminar_movimiento_canje(db, canje_id, movimiento_id)
    except MovimientoError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
