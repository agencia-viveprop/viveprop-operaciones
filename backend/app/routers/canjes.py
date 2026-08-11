from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
from app.models.usuario import RolUsuario, Usuario
from app.services.importar_canjes import ImportarCanjesResumen, importar_canjes

router = APIRouter(prefix="/canjes", tags=["canjes"])


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
