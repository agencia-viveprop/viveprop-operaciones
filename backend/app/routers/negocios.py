from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.canje import MonedaTipo
from app.models.catalogo import EstadoNegocio, ModeloNegocio, TipoCatalogo
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.models.usuario import RolUsuario, Usuario
from app.services import negocios as servicio
from app.services.movimientos import MovimientoError, crear_movimiento_negocio
from app.services.negocios import NegocioError
from app.services.bandeja_negocios import (
    BandejaNegocios,
    Duraciones,
    duraciones_de,
    obtener_bandeja_negocios,
    ultimos_movimientos,
)
from app.services.importar_negocios import (
    ArchivoInvalido,
    ResumenCargaNegocios,
    cargar_desde_xlsx,
)
from app.services.estructura_archivo import EstructuraArchivo
from app.services.plantilla_negocios import estructura_plantilla, generar_plantilla
from app.services.reportes_negocios import (
    NegociosPorMes,
    ResumenNegocios,
    negocios_por_mes,
    obtener_resumen_negocios,
)

router = APIRouter(prefix="/negocios", tags=["negocios"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _hoy_utc() -> date:
    return datetime.now(timezone.utc).date()


def _ultimos_movimientos_negocio(db: Session):
    """Reusa el cálculo de la bandeja para no tener dos versiones del mismo dato."""
    return ultimos_movimientos(db)


def _inicio_de(negocio: Negocio) -> date | None:
    """El hito más antiguo. Un negocio empieza cuando empieza su primer hito."""
    return min((h.fecha_inicio for h in negocio.hitos if h.fecha_inicio), default=None)


def _esta_abierto(negocio: Negocio) -> bool:
    """Si le queda alguna liquidación sin resolver.

    Un negocio sin hitos también cuenta como abierto: existe y no terminó.
    """
    return not negocio.hitos or any(h.estado == EstadoNegocio.ACTIVO for h in negocio.hitos)


def _cierre_de(negocio: Negocio) -> date | None:
    """La fecha de cierre solo si **todos** los hitos cerraron.

    Con una liquidación abierta el negocio sigue en curso, aunque la promesa ya
    esté cobrada. Y un negocio perdido no tiene fecha de cierre: la migración
    `d1f4a72b6e59` la limpió justamente porque era una copia de la de inicio.
    """
    if _esta_abierto(negocio):
        return None
    cierres = [h.fecha_cierre for h in negocio.hitos if h.fecha_cierre]
    return max(cierres) if cierres else None


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

    # No es un campo del hito: es el "si, estoy seguro" de la guarda de mas abajo.
    # Se excluye del model_dump que asigna atributos (ver `_datos_del_hito`).
    confirmar_cambio_de_monto: bool = False

    @model_validator(mode="after")
    def _el_cierre_va_con_el_estado(self):
        """La fecha de cierre existe si y solo si el hito esta cerrado.

        Sin esto se cuelan dos inconsistencias silenciosas. Un hito CERRADO sin
        fecha suma en el bucket de ganado --que filtra por estado-- pero no
        aparece en ningun mes, porque toda la reporteria mensual agrupa por
        `fecha_cierre`: la plata existiria y no estaria en ninguna parte. Y al
        reves, un hito perdido con fecha de cierre es la contradiccion que la
        migracion `d1f4a72b6e59` tuvo que limpiar en 12 filas; sin validacion se
        puede volver a introducir desde la API.
        """
        if self.estado == EstadoNegocio.CERRADO and self.fecha_cierre is None:
            raise ValueError(
                "Un hito cerrado necesita fecha de cierre: sin ella no aparece en "
                "ningun reporte mensual."
            )
        if self.estado != EstadoNegocio.CERRADO and self.fecha_cierre is not None:
            raise ValueError(
                f"Un hito en estado {self.estado.value} no puede tener fecha de cierre."
            )
        if self.fecha_cierre is not None and self.fecha_cierre < self.fecha_inicio:
            raise ValueError("La fecha de cierre es anterior a la de inicio.")
        return self


class HitoOut(BaseModel):
    id: int
    nombre: str | None
    fecha_inicio: date
    fecha_cierre: date | None
    estado: EstadoNegocio

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

    # Las tasas tienen que salir: son la **entrada** del calculo, y el formulario
    # de edicion las necesita para poder mostrarlas. Sin ellas, abrir un hito para
    # cerrarlo y guardar mandaria las tasas en nulo y borraria en silencio la base
    # sobre la que se calculo la comision. Hay un test que exige que sobrevivan a
    # una vuelta completa de lectura y guardado.
    pct_lado_vendedor: Decimal | None
    pct_lado_comprador: Decimal | None
    pct_rebate_concentrador: Decimal | None
    pct_broker_vendedor: Decimal | None
    pct_broker_comprador: Decimal | None
    pct_vp_vendedor: Decimal | None
    pct_vp_comprador: Decimal | None
    pct_equipo: Decimal | None
    pct_tercero: Decimal | None

    nombre_tercero: str | None
    motivo_perdida_id: int | None
    motivo_perdida_detalle: str | None

    model_config = {"from_attributes": True}


class NegocioIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=40)
    modelo: ModeloNegocio
    propiedad_id: int | None = None
    propiedad: PropiedadIn | None = None
    etapa: str | None = None
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
    etapa: str | None = None
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
    etapa: str | None
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
    etapa: str | None
    direccion: str
    unidad: str | None
    comuna: str
    alianza_id: int | None
    cantidad_hitos: int
    estados: list[EstadoNegocio]
    comision_total: Decimal
    comision_real_vp: Decimal
    # Las duraciones van en el listado para que la tabla pueda mostrar antigüedad
    # y última gestión: antes no tenía ninguna columna de fecha, así que no se
    # podía saber si un negocio llevaba una semana o siete meses.
    fecha_inicio: date | None
    duraciones: Duraciones


class MovimientoOut(BaseModel):
    id: int
    tipo_movimiento: str
    tipo_nombre: str
    etapa_resultante: str | None
    fecha: datetime
    autor_nombre: str | None
    comentario: str | None


class MovimientoIn(BaseModel):
    tipo_movimiento: str
    comentario: str | None = None
    fecha: datetime | None = None


class TipoMovimientoOut(BaseModel):
    codigo: str
    nombre: str
    etapa_resultante: str | None
    orden: int | None
    responsable_default: str | None


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


def _datos_del_hito(payload: "HitoIn") -> dict:
    """Los campos que se asignan al hito, sin la bandera de confirmacion."""
    return payload.model_dump(exclude={"confirmar_cambio_de_monto"})


def _aplicar_hito(db: Session, hito: NegocioHito, datos: dict, modelo: str) -> None:
    servicio.validar_catalogo(
        db, datos.get("motivo_perdida_id", hito.motivo_perdida_id),
        TipoCatalogo.MOTIVO_PERDIDA, "motivo_perdida_id",
    )
    for campo, valor in datos.items():
        setattr(hito, campo, valor)
    servicio.refrescar_hito(db, hito, modelo)


# Un peso: por debajo de eso es redondeo, no un cambio.
TOLERANCIA_MONTO = Decimal("1")

# Los siete montos que el motor persiste. Se vigilan todos, no solo la comision
# real: `VVP-2` se desvia en `comision_total` --903.803-- y dejaba la real intacta,
# asi que mirar una sola columna dejaba pasar justamente el caso mas grande.
MONTOS_DEL_MOTOR = (
    "comision_total", "comision_broker", "rebate_concentrador", "comision_vp_bruta",
    "comision_equipo", "comision_tercero", "comision_real_vp",
)


def _montos_de(hito: NegocioHito) -> dict[str, Decimal | None]:
    return {c: getattr(hito, c) for c in MONTOS_DEL_MOTOR}


def _vigilar_monto_cerrado(
    hito: NegocioHito,
    antes: dict[str, Decimal | None],
    ya_estaba_cerrado: bool,
    confirmado: bool,
) -> None:
    """Impide que guardar una liquidacion cerrada le mueva la plata sin avisar.

    **Por que existe.** Los 19 negocios del Excel se cargaron con los montos tal
    cual (`D-026`) y la API los pasa por el motor en cada guardado. Cuando las
    entradas guardadas no reproducen el monto guardado, abrir el formulario y
    apretar Guardar --sin tocar nada-- cambiaba la comision. Medido: `VVP-17`
    bajaba de 774.691,95 a 759.166,55, y `VVP-2` subia su total en 903.803. La
    migracion `f5a92c3d81e6` dejo esas filas consistentes, pero eso arregla los
    datos que hay, no la clase de problema: cualquier carga futura puede traer
    otra fila asi.

    **Solo mira las que ya estaban cerradas**, y a proposito. Cerrar un negocio
    calcula la comision por primera vez: ahi el cambio es el objetivo. Y mover la
    plata de un negocio abierto es trabajo normal de pipeline. Lo que no puede
    pasar en silencio es que cambie un monto que ya se facturo.

    No es un bloqueo: `confirmar_cambio_de_monto` lo deja pasar. La diferencia
    entre eso y el estado anterior es que ahora hay que verla y aceptarla.
    """
    if not ya_estaba_cerrado or confirmado:
        return

    despues = _montos_de(hito)
    movidos = {
        campo: (antes[campo], despues[campo])
        for campo in MONTOS_DEL_MOTOR
        if antes[campo] is not None
        and despues[campo] is not None
        and abs(despues[campo] - antes[campo]) >= TOLERANCIA_MONTO
    }
    if not movidos:
        return

    # Se informa la comision real si se movio, y si no, el primer monto que si.
    # Es el numero que la pantalla necesita para poder preguntar algo concreto.
    principal = "comision_real_vp" if "comision_real_vp" in movidos else next(iter(movidos))
    actual, nuevo = movidos[principal]
    raise HTTPException(
        status.HTTP_409_CONFLICT,
        {
            "motivo": "cambio_de_monto",
            "campo": principal,
            "mensaje": (
                "Esta liquidación está cerrada y guardarla cambiaría "
                f"{principal.replace('_', ' ')} de {actual} a {nuevo}. Si el monto "
                "nuevo es el correcto, confirma el cambio para continuar."
            ),
            "comision_actual": str(actual),
            "comision_nueva": str(nuevo),
            "montos_que_cambian": {c: [str(a), str(d)] for c, (a, d) in movidos.items()},
        },
    )


# ------------------------------------------------------------------ endpoints


@router.get("/propiedades", response_model=list[PropiedadOut])
def buscar_propiedades(
    q: str = Query(min_length=2, description="Parte de la dirección"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Para que el alta ofrezca lo que ya existe antes de crear un duplicado."""
    return servicio.buscar_propiedades_parecidas(db, q)


@router.get("/plantilla")
def descargar_plantilla(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    """El .xlsx vacío para la carga masiva, con los códigos válidos de esta base."""
    contenido = generar_plantilla(db)
    return Response(
        content=contenido,
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="plantilla-negocios.xlsx"'},
    )


@router.get("/plantilla/estructura", response_model=EstructuraArchivo)
def estructura_de_la_plantilla(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    """Qué columnas espera el archivo, para poder verlo sin bajarlo y abrirlo.

    Sale de la misma definición que pinta la plantilla, así que la pantalla no
    puede quedar describiendo columnas que el Excel ya no trae.
    """
    return estructura_plantilla(db)


@router.post("/importar", response_model=ResumenCargaNegocios)
async def importar(
    archivo: UploadFile,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    """Carga masiva. Si hay un solo error no se escribe nada.

    Los errores de contenido vuelven en el cuerpo con 200, no como 4xx: son
    decenas de mensajes por fila y el front los lista. Un 400 obligaría a
    inventar una forma aparte de transportarlos.
    """
    try:
        return cargar_desde_xlsx(db, await archivo.read())
    except ArchivoInvalido as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/reportes/resumen", response_model=ResumenNegocios)
def reportes_resumen(
    db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)
):
    """Base de calculo de la reporteria (sprint 12).

    Los tres buckets vienen separados a proposito y no hay un campo `total`:
    sumar ganado, pipeline y perdido da un numero que no significa nada.
    """
    return obtener_resumen_negocios(db)


# Va antes de "/{negocio_id}": FastAPI resuelve por orden de registro, y si
# esta ruta quedara despues, "tipos-movimiento" se interpretaria como un id.
@router.get("/bandeja", response_model=BandejaNegocios)
def bandeja(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Qué negocio hay que tocar hoy, ordenado por urgencia.

    El equivalente de la bandeja de canjes, con umbrales en días en vez de horas:
    acá los procesos duran de un mes a varios, así que medir en horas no
    distingue nada.
    """
    return obtener_bandeja_negocios(db)


@router.get("/reportes/por-mes", response_model=NegociosPorMes)
def reporte_por_mes(
    modelo: ModeloNegocio | None = Query(None, description="Filtra por modelo de negocio."),
    tipo_operacion: str | None = Query(None, description="Código del catálogo: VENTA, ARRIENDO."),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Cuántos negocios arrancaron cada mes.

    Es el equivalente de "solicitudes por mes" en canjes: mide cuánto entró, no
    cuánto se cobró. Lo cobrado está en `/reportes/resumen`, en `ganado_por_mes`,
    que agrupa por fecha de cierre y responde otra pregunta.
    """
    return negocios_por_mes(db, modelo.value if modelo else None, tipo_operacion)


@router.get("/tipos-movimiento", response_model=list[TipoMovimientoOut])
def listar_tipos_movimiento(
    db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)
):
    """Los pasos posibles del pipeline, para que el front no los hardcodee."""
    return db.scalars(
        select(TipoMovimiento)
        .where(
            TipoMovimiento.entity_type == EntityType.negocio,
            TipoMovimiento.activo.is_(True),
        )
        .order_by(TipoMovimiento.orden)
    ).all()


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
    hoy = _hoy_utc()
    ultimo_mov, ultimo_etapa = _ultimos_movimientos_negocio(db)
    return [
        NegocioResumen(
            id=n.id,
            codigo=n.codigo,
            modelo=n.modelo,
            etapa=n.etapa,
            direccion=n.propiedad.direccion,
            unidad=n.propiedad.unidad,
            comuna=n.propiedad.comuna,
            alianza_id=n.alianza_id,
            cantidad_hitos=len(n.hitos),
            estados=[h.estado for h in n.hitos],
            # Sumar los hitos es la unica forma correcta de totalizar (D-020).
            comision_total=sum((h.comision_total or cero for h in n.hitos), cero),
            comision_real_vp=sum((h.comision_real_vp or cero for h in n.hitos), cero),
            fecha_inicio=_inicio_de(n),
            duraciones=duraciones_de(
                _inicio_de(n),
                _cierre_de(n),
                ultimo_mov.get(n.id),
                ultimo_etapa.get(n.id),
                hoy,
                abierto=_esta_abierto(n),
            ),
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

        servicio.validar_etapa(db, payload.etapa)
        negocio = Negocio(
            codigo=payload.codigo,
            modelo=payload.modelo,
            etapa=payload.etapa,
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
        if "etapa" in cambios:
            servicio.validar_etapa(db, cambios["etapa"])
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
        _aplicar_hito(db, hito, _datos_del_hito(payload), negocio.modelo.value)
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
    # Se leen antes de aplicar: despues el objeto ya viene recalculado.
    montos_antes = _montos_de(hito)
    ya_estaba_cerrado = hito.estado == EstadoNegocio.CERRADO

    try:
        _aplicar_hito(db, hito, _datos_del_hito(payload), negocio.modelo.value)
        _vigilar_monto_cerrado(
            hito, montos_antes, ya_estaba_cerrado, payload.confirmar_cambio_de_monto
        )
        db.commit()
    except NegocioError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except HTTPException:
        # La guarda ya recalculo el hito en memoria: sin rollback, la sesion se
        # llevaria el cambio rechazado al siguiente commit.
        db.rollback()
        raise
    db.refresh(hito)
    return hito




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
    )


@router.get("/{negocio_id}/movimientos", response_model=list[MovimientoOut])
def listar_movimientos(
    negocio_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    _cargar(db, negocio_id)
    movimientos = db.scalars(
        select(Movimiento)
        .where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.entity_id == negocio_id,
        )
        .order_by(Movimiento.fecha.desc())
    ).all()
    return [_a_movimiento_out(db, m) for m in movimientos]


@router.post(
    "/{negocio_id}/movimientos",
    response_model=MovimientoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_movimiento(
    negocio_id: int,
    payload: MovimientoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    # Un negocio inexistente es un 404, no un 400: el recurso no esta, no es que
    # el cuerpo venga mal. El servicio igual lo valida, porque
    # `movimientos.entity_id` no puede tener clave foranea.
    _cargar(db, negocio_id)
    try:
        movimiento = crear_movimiento_negocio(
            db, negocio_id, payload.tipo_movimiento, usuario.id, payload.comentario, payload.fecha
        )
    except MovimientoError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return _a_movimiento_out(db, movimiento)
