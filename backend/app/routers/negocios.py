from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.canje import MonedaTipo
from app.models.catalogo import EstadoNegocio, ModeloNegocio, TipoCatalogo
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.models.usuario import RolUsuario, Usuario
from app.services import negocios as servicio
from app.services.negocios import NegocioError

router = APIRouter(prefix="/negocios", tags=["negocios"])


# ------------------------------------------------------------------- esquemas


class PropiedadIn(BaseModel):
    direccion: str
    unidad: str | None = None
    comuna: str
    tipo_propiedad_id: int | None = None
    estado_propiedad_id: int | None = None


class PropiedadOut(PropiedadIn):
    id: int
    model_config = {"from_attributes": True}


class HitoIn(BaseModel):
    nombre: str | None = None
    fecha_inicio: date
    fecha_cierre: date | None = None
    estado: EstadoNegocio = EstadoNegocio.ACTIVO
    etapa: str | None = None

    valor_negocio: Decimal | None = None
    moneda: MonedaTipo | None = None
    fecha_valorizacion: date | None = None
    valor_clp_manual: Decimal | None = None
    motivo_valor_manual: str | None = None

    pct_lado_vendedor: Decimal | None = None
    pct_lado_comprador: Decimal | None = None
    pct_rebate_concentrador: Decimal | None = None
    pct_broker_vendedor: Decimal | None = None
    pct_broker_comprador: Decimal | None = None
    pct_vp_vendedor: Decimal | None = None
    pct_vp_comprador: Decimal | None = None
    pct_equipo: Decimal | None = None
    pct_tercero: Decimal | None = None
    nombre_tercero: str | None = None

    motivo_perdida_id: int | None = None
    motivo_perdida_detalle: str | None = None


class HitoOut(BaseModel):
    id: int
    nombre: str | None
    fecha_inicio: date
    fecha_cierre: date | None
    estado: EstadoNegocio
    etapa: str | None

    valor_negocio: Decimal | None
    moneda: MonedaTipo | None
    fecha_valorizacion: date | None
    uf_snapshot: Decimal | None
    valor_clp_calculado: Decimal | None
    valor_clp_manual: Decimal | None
    motivo_valor_manual: str | None
    # Derivado, no columna: deja explicito sobre que se calculo (D-017).
    base_comision: Decimal | None

    comision_total: Decimal | None
    comision_broker: Decimal | None
    rebate_concentrador: Decimal | None
    comision_vp_bruta: Decimal | None
    comision_equipo: Decimal | None
    comision_tercero: Decimal | None
    comision_real_vp: Decimal | None

    nombre_tercero: str | None
    motivo_perdida_id: int | None
    motivo_perdida_detalle: str | None

    model_config = {"from_attributes": True}


class NegocioIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    modelo: ModeloNegocio
    propiedad_id: int | None = None
    propiedad: PropiedadIn | None = None
    alianza_id: int | None = None
    tipo_operacion_id: int | None = None
    vendedor_arrendador: str | None = None
    comprador_arrendatario: str | None = None
    corredor_agente: str | None = None
    notas: str | None = None
    observaciones: str | None = None
    hitos: list[HitoIn] = Field(min_length=1)

    @model_validator(mode="after")
    def _propiedad_por_id_o_por_datos(self):
        if (self.propiedad_id is None) == (self.propiedad is None):
            raise ValueError("Hay que indicar propiedad_id o propiedad, y solo uno de los dos.")
        return self


class NegocioUpdate(BaseModel):
    modelo: ModeloNegocio | None = None
    alianza_id: int | None = None
    tipo_operacion_id: int | None = None
    vendedor_arrendador: str | None = None
    comprador_arrendatario: str | None = None
    corredor_agente: str | None = None
    notas: str | None = None
    observaciones: str | None = None


class NegocioOut(BaseModel):
    id: int
    codigo: str
    modelo: ModeloNegocio
    propiedad: PropiedadOut
    alianza_id: int | None
    tipo_operacion_id: int | None
    vendedor_arrendador: str | None
    comprador_arrendatario: str | None
    corredor_agente: str | None
    notas: str | None
    observaciones: str | None
    creado_en: datetime
    hitos: list[HitoOut]

    model_config = {"from_attributes": True}


class NegocioResumen(BaseModel):
    """Para el listado: sin los hitos completos, con sus totales sumados."""

    id: int
    codigo: str
    modelo: ModeloNegocio
    direccion: str
    unidad: str | None
    comuna: str
    alianza_id: int | None
    cantidad_hitos: int
    estados: list[EstadoNegocio]
    comision_total: Decimal
    comision_real_vp: Decimal


# ------------------------------------------------------------------- helpers


def _cargar(db: Session, negocio_id: int) -> Negocio:
    negocio = db.scalar(
        select(Negocio)
        .where(Negocio.id == negocio_id)
        .options(selectinload(Negocio.hitos), selectinload(Negocio.propiedad))
    )
    if negocio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe el negocio {negocio_id}.")
    return negocio


def _validar_referencias(db: Session, alianza_id, tipo_operacion_id) -> None:
    servicio.validar_catalogo(db, alianza_id, TipoCatalogo.ALIANZA, "alianza_id")
    servicio.validar_catalogo(db, tipo_operacion_id, TipoCatalogo.TIPO_OPERACION, "tipo_operacion_id")


def _aplicar_hito(db: Session, hito: NegocioHito, datos: dict, modelo: str) -> None:
    servicio.validar_etapa(db, datos.get("etapa", hito.etapa))
    servicio.validar_catalogo(
        db, datos.get("motivo_perdida_id", hito.motivo_perdida_id),
        TipoCatalogo.MOTIVO_PERDIDA, "motivo_perdida_id",
    )
    for campo, valor in datos.items():
        setattr(hito, campo, valor)
    servicio.refrescar_hito(db, hito, modelo)


# ------------------------------------------------------------------ endpoints


@router.get("/propiedades", response_model=list[PropiedadOut])
def buscar_propiedades(
    q: str = Query(min_length=2, description="Parte de la dirección"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Para que el alta ofrezca lo que ya existe antes de crear un duplicado."""
    return servicio.buscar_propiedades_parecidas(db, q)


@router.get("", response_model=list[NegocioResumen])
def listar(
    estado: EstadoNegocio | None = None,
    modelo: ModeloNegocio | None = None,
    alianza_id: int | None = None,
    codigo: str | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    consulta = select(Negocio).options(
        selectinload(Negocio.hitos), selectinload(Negocio.propiedad)
    )
    if modelo is not None:
        consulta = consulta.where(Negocio.modelo == modelo)
    if alianza_id is not None:
        consulta = consulta.where(Negocio.alianza_id == alianza_id)
    if codigo:
        consulta = consulta.where(Negocio.codigo.ilike(f"%{codigo}%"))

    negocios = db.scalars(consulta.order_by(Negocio.codigo)).all()
    if estado is not None:
        negocios = [n for n in negocios if any(h.estado == estado for h in n.hitos)]

    cero = Decimal("0")
    return [
        NegocioResumen(
            id=n.id,
            codigo=n.codigo,
            modelo=n.modelo,
            direccion=n.propiedad.direccion,
            unidad=n.propiedad.unidad,
            comuna=n.propiedad.comuna,
            alianza_id=n.alianza_id,
            cantidad_hitos=len(n.hitos),
            estados=[h.estado for h in n.hitos],
            # Sumar los hitos es la unica forma correcta de totalizar (D-020).
            comision_total=sum((h.comision_total or cero for h in n.hitos), cero),
            comision_real_vp=sum((h.comision_real_vp or cero for h in n.hitos), cero),
        )
        for n in negocios
    ]


@router.get("/{negocio_id}", response_model=NegocioOut)
def obtener(
    negocio_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return _cargar(db, negocio_id)


@router.post("", response_model=NegocioOut, status_code=status.HTTP_201_CREATED)
def crear(
    payload: NegocioIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    if db.scalar(select(Negocio).where(Negocio.codigo == payload.codigo)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe el negocio '{payload.codigo}'.")

    try:
        _validar_referencias(db, payload.alianza_id, payload.tipo_operacion_id)

        if payload.propiedad_id is not None:
            propiedad = db.get(Propiedad, payload.propiedad_id)
            if propiedad is None:
                raise NegocioError(f"No existe la propiedad {payload.propiedad_id}.")
        else:
            propiedad = servicio.obtener_o_crear_propiedad(db, payload.propiedad.model_dump())

        negocio = Negocio(
            codigo=payload.codigo,
            modelo=payload.modelo,
            propiedad=propiedad,
            alianza_id=payload.alianza_id,
            tipo_operacion_id=payload.tipo_operacion_id,
            vendedor_arrendador=payload.vendedor_arrendador,
            comprador_arrendatario=payload.comprador_arrendatario,
            corredor_agente=payload.corredor_agente,
            notas=payload.notas,
            observaciones=payload.observaciones,
        )
        # Se agrega antes de tocar los hitos: aplicarlos hace consultas (la UF,
        # la etapa, los catalogos) que disparan autoflush, y si el negocio no
        # esta en la sesion todavia, la cascada desde Propiedad.negocios no
        # alcanza a incluirlo.
        db.add(negocio)

        for datos_hito in payload.hitos:
            hito = NegocioHito(fecha_inicio=datos_hito.fecha_inicio, estado=datos_hito.estado)
            negocio.hitos.append(hito)
            _aplicar_hito(db, hito, datos_hito.model_dump(), payload.modelo.value)

        db.commit()
    except NegocioError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    return _cargar(db, negocio.id)


@router.patch("/{negocio_id}", response_model=NegocioOut)
def actualizar(
    negocio_id: int,
    payload: NegocioUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    negocio = _cargar(db, negocio_id)
    cambios = payload.model_dump(exclude_unset=True)

    try:
        _validar_referencias(
            db,
            cambios.get("alianza_id", negocio.alianza_id),
            cambios.get("tipo_operacion_id", negocio.tipo_operacion_id),
        )
        for campo, valor in cambios.items():
            setattr(negocio, campo, valor)

        # Cambiar el modelo cambia la formula, asi que hay que recalcular todo.
        if "modelo" in cambios:
            for hito in negocio.hitos:
                servicio.recalcular_comisiones(hito, negocio.modelo.value)

        db.commit()
    except NegocioError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    return _cargar(db, negocio_id)


@router.post("/{negocio_id}/hitos", response_model=HitoOut, status_code=status.HTTP_201_CREATED)
def crear_hito(
    negocio_id: int,
    payload: HitoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    negocio = _cargar(db, negocio_id)
    hito = NegocioHito(fecha_inicio=payload.fecha_inicio, estado=payload.estado)
    negocio.hitos.append(hito)
    try:
        _aplicar_hito(db, hito, payload.model_dump(), negocio.modelo.value)
        db.commit()
    except NegocioError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    db.refresh(hito)
    return hito


@router.patch("/{negocio_id}/hitos/{hito_id}", response_model=HitoOut)
def actualizar_hito(
    negocio_id: int,
    hito_id: int,
    payload: HitoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    negocio = _cargar(db, negocio_id)
    hito = next((h for h in negocio.hitos if h.id == hito_id), None)
    if hito is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"El hito {hito_id} no pertenece al negocio {negocio.codigo}.",
        )
    try:
        _aplicar_hito(db, hito, payload.model_dump(), negocio.modelo.value)
        db.commit()
    except NegocioError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    db.refresh(hito)
    return hito
