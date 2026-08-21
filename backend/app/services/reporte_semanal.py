"""Reporte semanal: qué se cerró, qué avanzó, qué se cayó, qué está estancado.

Cubre los **dos dominios**. Un reporte de la semana que ignore los 194 canjes
abiertos sería medio reporte, y quien lo lee opera los dos.

**Es un reporte de movimiento, no de estado.** El dashboard responde "cómo
vamos"; esto responde "qué pasó esta semana". Por eso casi todo se calcula desde
`movimientos` y no desde el estado actual de las filas: el estado dice dónde
estamos, el movimiento dice qué cambió.

La excepción es lo cerrado, que se toma de `fecha_cierre`. Es la fecha en que
entró la plata y es más confiable que buscar el movimiento que la marcó.

**"Avanzó" es toda actividad registrada, no solo un cambio de etapa.** En un
reporte semanal lo que importa es donde hubo progreso, y registrar una
confirmacion por WhatsApp es progreso aunque la etapa no se mueva. Ademas los
movimientos migrados del Excel llevan `etapa_resultante` nulo a proposito
(D-030), asi que filtrar por cambio de etapa dejaria el reporte vacio sobre toda
la historia previa. Cuando el movimiento si mueve la etapa, se muestra.

**Estancado** no es un estado guardado, es una ausencia: algo abierto sin
movimiento en más de N días. El umbral entra por parámetro y no está en `CONFIG`
-- los 48/24 horas de ahí son para el semáforo diario de canjes, que mide otra
cosa. El default de 14 días es una estimación, no un dato del negocio.
"""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito

CERO = Decimal("0")
DIAS_ESTANCADO_DEFECTO = 14

# Tipos que significan "el negocio no prosperó".
CAIDA_NEGOCIO = ("NEG_PERDIDA", "NEG_DESISTIMIENTO")
CAIDA_CANJE = ("CANCELACION",)
TOPE_LISTA = 25


class ItemCerrado(BaseModel):
    referencia: str
    detalle: str | None = None
    fecha: date | None = None
    monto: Decimal | None = None


class ItemMovido(BaseModel):
    referencia: str
    detalle: str | None = None
    fecha: date
    etapa: str | None = None
    comentario: str | None = None


class ItemEstancado(BaseModel):
    referencia: str
    detalle: str | None = None
    etapa: str | None = None
    dias_sin_movimiento: int | None = None


class Seccion(BaseModel):
    cerrados: list[ItemCerrado]
    monto_cerrado: Decimal
    avanzados: list[ItemMovido]
    caidos: list[ItemMovido]
    estancados: list[ItemEstancado]
    # Los totales van aparte porque las listas están topeadas.
    total_cerrados: int
    total_avanzados: int
    total_caidos: int
    total_estancados: int


class ReporteSemanal(BaseModel):
    desde: date
    hasta: date
    dias_estancado: int
    negocios: Seccion
    canjes: Seccion


def semana_de(referencia: date) -> tuple[date, date]:
    """El lunes y el domingo de la semana que contiene esa fecha."""
    lunes = referencia - timedelta(days=referencia.weekday())
    return lunes, lunes + timedelta(days=6)


def _rango_utc(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """El intervalo completo, con el último día incluido."""
    return (
        datetime.combine(desde, time.min, tzinfo=timezone.utc),
        datetime.combine(hasta, time.max, tzinfo=timezone.utc),
    )


def _ultimos_movimientos(db: Session, tipo: EntityType):
    return (
        select(
            Movimiento.entity_id.label("entity_id"),
            func.max(Movimiento.fecha).label("fecha"),
        )
        .where(Movimiento.entity_type == tipo)
        .group_by(Movimiento.entity_id)
        .subquery()
    )


def _dias(ahora: datetime, fecha) -> int | None:
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return (ahora - fecha).days


# --------------------------------------------------------------- negocios


def _seccion_negocios(db: Session, desde: date, hasta: date, dias: int, ahora: datetime) -> Seccion:
    inicio, fin = _rango_utc(desde, hasta)

    filas_cerradas = db.execute(
        select(Negocio.codigo, NegocioHito.nombre, NegocioHito.fecha_cierre, NegocioHito.comision_real_vp)
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .where(
            NegocioHito.estado == EstadoNegocio.CERRADO,
            NegocioHito.fecha_cierre >= desde,
            NegocioHito.fecha_cierre <= hasta,
        )
        .order_by(NegocioHito.fecha_cierre)
    ).all()
    cerrados = [
        ItemCerrado(referencia=cod, detalle=nombre, fecha=f, monto=monto or CERO)
        for cod, nombre, f, monto in filas_cerradas
    ]
    monto_cerrado = sum((c.monto or CERO for c in cerrados), CERO)

    movidos = db.execute(
        select(Negocio.codigo, Movimiento.fecha, Movimiento.etapa_resultante,
               Movimiento.comentario, Movimiento.tipo_movimiento)
        .join(Negocio, Negocio.id == Movimiento.entity_id)
        .where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
        .order_by(Movimiento.fecha)
    ).all()

    # Actividad que no sea una caida: esas se listan aparte y contarlas en las
    # dos columnas seria contar el mismo hecho dos veces.
    avanzados = [
        ItemMovido(referencia=cod, fecha=f.date(), etapa=etapa, comentario=com)
        for cod, f, etapa, com, tipo in movidos
        if tipo not in CAIDA_NEGOCIO
    ]
    caidos = [
        ItemMovido(referencia=cod, fecha=f.date(), etapa=None, comentario=com)
        for cod, f, etapa, com, tipo in movidos
        if tipo in CAIDA_NEGOCIO
    ]

    ultimos = _ultimos_movimientos(db, EntityType.negocio)
    filas_abiertas = db.execute(
        select(Negocio.codigo, Negocio.etapa, ultimos.c.fecha, NegocioHito.fecha_inicio)
        .join(NegocioHito, NegocioHito.negocio_id == Negocio.id)
        .outerjoin(ultimos, ultimos.c.entity_id == Negocio.id)
        .where(NegocioHito.estado == EstadoNegocio.ACTIVO)
    ).all()

    estancados = []
    vistos = set()
    for cod, etapa, ultima, inicio_hito in filas_abiertas:
        if cod in vistos:
            continue
        referencia = ultima or datetime.combine(inicio_hito, time.min, tzinfo=timezone.utc)
        transcurridos = _dias(ahora, referencia)
        if transcurridos is not None and transcurridos > dias:
            vistos.add(cod)
            estancados.append(
                ItemEstancado(
                    referencia=cod,
                    detalle="sin movimientos" if ultima is None else None,
                    etapa=etapa,
                    dias_sin_movimiento=transcurridos,
                )
            )
    estancados.sort(key=lambda e: -(e.dias_sin_movimiento or 0))

    return Seccion(
        cerrados=cerrados[:TOPE_LISTA],
        monto_cerrado=monto_cerrado,
        avanzados=avanzados[:TOPE_LISTA],
        caidos=caidos[:TOPE_LISTA],
        estancados=estancados[:TOPE_LISTA],
        total_cerrados=len(cerrados),
        total_avanzados=len(avanzados),
        total_caidos=len(caidos),
        total_estancados=len(estancados),
    )


# ----------------------------------------------------------------- canjes


def _seccion_canjes(db: Session, desde: date, hasta: date, dias: int, ahora: datetime) -> Seccion:
    inicio, fin = _rango_utc(desde, hasta)

    filas_cerradas = db.execute(
        select(Canje.id, Canje.corredor_solicitante_nombre, Canje.fecha_cierre)
        .where(
            Canje.etapa == CanjeEtapa.CERRADO,
            Canje.fecha_cierre >= inicio,
            Canje.fecha_cierre <= fin,
        )
        .order_by(Canje.fecha_cierre)
    ).all()
    cerrados = [
        ItemCerrado(referencia=f"#{cid}", detalle=corredor, fecha=f.date() if f else None)
        for cid, corredor, f in filas_cerradas
    ]

    movidos = db.execute(
        select(Movimiento.entity_id, Canje.comuna, Movimiento.fecha,
               Movimiento.etapa_resultante, Movimiento.comentario,
               Movimiento.tipo_movimiento, TipoMovimiento.nombre)
        .join(Canje, Canje.id == Movimiento.entity_id)
        .join(TipoMovimiento, TipoMovimiento.codigo == Movimiento.tipo_movimiento)
        .where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
        .order_by(Movimiento.fecha)
    ).all()

    avanzados = [
        ItemMovido(referencia=f"#{cid}", detalle=comuna, fecha=f.date(), etapa=etapa, comentario=nombre)
        for cid, comuna, f, etapa, com, tipo, nombre in movidos
        if tipo not in CAIDA_CANJE
    ]
    caidos = [
        ItemMovido(referencia=f"#{cid}", detalle=comuna, fecha=f.date(), etapa=None, comentario=com)
        for cid, comuna, f, etapa, com, tipo, nombre in movidos
        if tipo in CAIDA_CANJE
    ]

    # Abierto es lo mismo que en la bandeja: activo y con etapa distinta de
    # cerrada, para no contar como pendientes los 31 que arrastran el
    # desalineamiento del dato de Dataprop.
    ultimos = _ultimos_movimientos(db, EntityType.canje)
    filas_abiertas = db.execute(
        select(Canje.id, Canje.comuna, Canje.etapa, ultimos.c.fecha, Canje.fecha_solicitud)
        .outerjoin(ultimos, ultimos.c.entity_id == Canje.id)
        .where(Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO)
    ).all()

    estancados = []
    for cid, comuna, etapa, ultima, solicitud in filas_abiertas:
        referencia = ultima or solicitud
        transcurridos = _dias(ahora, referencia)
        if transcurridos is not None and transcurridos > dias:
            estancados.append(
                ItemEstancado(
                    referencia=f"#{cid}",
                    detalle=comuna if ultima is not None else f"{comuna or ''} · sin gestión".strip(" ·"),
                    etapa=etapa.value,
                    dias_sin_movimiento=transcurridos,
                )
            )
    estancados.sort(key=lambda e: -(e.dias_sin_movimiento or 0))

    return Seccion(
        cerrados=cerrados[:TOPE_LISTA],
        monto_cerrado=CERO,  # los canjes no llevan comisión propia en la app
        avanzados=avanzados[:TOPE_LISTA],
        caidos=caidos[:TOPE_LISTA],
        estancados=estancados[:TOPE_LISTA],
        total_cerrados=len(cerrados),
        total_avanzados=len(avanzados),
        total_caidos=len(caidos),
        total_estancados=len(estancados),
    )


def obtener_reporte_semanal(
    db: Session,
    desde: date | None = None,
    hasta: date | None = None,
    dias_estancado: int = DIAS_ESTANCADO_DEFECTO,
    ahora: datetime | None = None,
) -> ReporteSemanal:
    ahora = ahora or datetime.now(timezone.utc)
    if desde is None or hasta is None:
        desde, hasta = semana_de(ahora.date())

    return ReporteSemanal(
        desde=desde,
        hasta=hasta,
        dias_estancado=dias_estancado,
        negocios=_seccion_negocios(db, desde, hasta, dias_estancado, ahora),
        canjes=_seccion_canjes(db, desde, hasta, dias_estancado, ahora),
    )
