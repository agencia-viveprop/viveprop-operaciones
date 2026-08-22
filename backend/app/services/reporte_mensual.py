"""Reporte mensual comparativo: el mes contra dos referencias.

**Tres períodos, no una serie.** La pregunta es "cómo venimos", y se responde
comparando el mes con dos cosas distintas: el **mes anterior**, que dice si la
tendencia corta sube o baja, y el **mismo mes del año anterior**, que dice si es
tendencia o es estacionalidad. Un gráfico de veinticuatro meses responde otra
pregunta y ya está cubierto por los de "por mes" del dashboard.

**La variación contra cero no es infinito: es "sin base".** Si el año pasado
hubo 0 cierres y este hay 3, eso no es "+300%" ni "+∞" -- no hay contra qué
comparar. Se devuelve nulo y la pantalla lo muestra como algo nuevo, no como un
número inventado. Es el caso que el criterio del sprint nombra: un mes sin datos
no puede romper la comparación.

**Cada dominio se mide por lo que le corresponde.** En negocios lo cerrado va
por `fecha_cierre` -- importa cuándo entró la plata -- y lo iniciado por
`fecha_inicio`, que es el indicador que se adelanta. En canjes las solicitudes
van por `fecha_solicitud` y los cierres por `fecha_cierre`.

**Los montos ya están en pesos.** Las columnas `comision_*` son `numeric(16,2)`
en CLP, resueltas al guardar con la UF congelada del hito. Acá no se convierte
nada.
"""
from calendar import monthrange
from datetime import date, datetime, time, timezone
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio
from app.models.negocio import Negocio, NegocioHito

CERO = Decimal("0")


class MetricasMes(BaseModel):
    """Lo que se mide en un mes. Sin totales cruzados entre dominios."""

    etiqueta: str  # '2026-08'

    # Negocios
    hitos_cerrados: int
    comision_real_vp: Decimal
    comision_total: Decimal
    negocios_iniciados: int

    # Canjes
    canjes_solicitados: int
    canjes_cerrados: int
    canjes_cancelados: int


class Variacion(BaseModel):
    """El cambio de una métrica contra una referencia.

    `pct` es nulo cuando la referencia es cero: ahí no hay porcentaje que
    calcular, y poner uno seria inventarlo.
    """

    metrica: str
    actual: Decimal
    referencia: Decimal
    absoluta: Decimal
    pct: Decimal | None


class Comparacion(BaseModel):
    contra: MetricasMes
    variaciones: list[Variacion]


class ReporteMensual(BaseModel):
    mes: MetricasMes
    mes_anterior: Comparacion
    mismo_mes_anio_anterior: Comparacion


# Qué se compara, y con qué nombre se muestra. El orden es el de lectura: la
# plata primero, el volumen despues.
METRICAS: tuple[tuple[str, str], ...] = (
    ("comision_real_vp", "Comisión real ViveProp"),
    ("comision_total", "Comisión total"),
    ("hitos_cerrados", "Liquidaciones cerradas"),
    ("negocios_iniciados", "Negocios iniciados"),
    ("canjes_solicitados", "Canjes solicitados"),
    ("canjes_cerrados", "Canjes cerrados"),
    ("canjes_cancelados", "Canjes cancelados"),
)


def limites(anio: int, mes: int) -> tuple[date, date]:
    """El primer y el último día del mes."""
    return date(anio, mes, 1), date(anio, mes, monthrange(anio, mes)[1])


def mes_anterior(anio: int, mes: int) -> tuple[int, int]:
    return (anio - 1, 12) if mes == 1 else (anio, mes - 1)


def _metricas(db: Session, anio: int, mes: int) -> MetricasMes:
    desde, hasta = limites(anio, mes)
    # Los canjes guardan fecha con hora, así que el rango va como instantes para
    # que el último día entre completo.
    inicio = datetime.combine(desde, time.min, tzinfo=timezone.utc)
    fin = datetime.combine(hasta, time.max, tzinfo=timezone.utc)

    cerrados = db.execute(
        select(
            func.count(NegocioHito.id),
            func.coalesce(func.sum(NegocioHito.comision_real_vp), 0),
            func.coalesce(func.sum(NegocioHito.comision_total), 0),
        ).where(
            NegocioHito.estado == EstadoNegocio.CERRADO,
            NegocioHito.fecha_cierre >= desde,
            NegocioHito.fecha_cierre <= hasta,
        )
    ).one()

    # Un negocio se cuenta una vez, en el mes de su hito mas antiguo: `VVP-3`
    # tiene promesa y escritura en meses distintos y es un negocio, no dos.
    primeros = (
        select(
            NegocioHito.negocio_id.label("negocio_id"),
            func.min(NegocioHito.fecha_inicio).label("inicio"),
        )
        .group_by(NegocioHito.negocio_id)
        .subquery()
    )
    iniciados = db.scalar(
        select(func.count())
        .select_from(primeros)
        .join(Negocio, Negocio.id == primeros.c.negocio_id)
        .where(primeros.c.inicio >= desde, primeros.c.inicio <= hasta)
    )

    solicitados = db.scalar(
        select(func.count()).select_from(Canje).where(
            Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin
        )
    )
    canjes_cerrados = db.scalar(
        select(func.count()).select_from(Canje).where(
            Canje.etapa == CanjeEtapa.CERRADO,
            Canje.fecha_cierre >= inicio,
            Canje.fecha_cierre <= fin,
        )
    )
    # Los cancelados se cuentan por fecha de solicitud: `canjes` no guarda cuándo
    # se canceló, así que "cancelados en agosto" no se puede saber. Esto responde
    # "de los que entraron en agosto, cuántos terminaron cancelados", que es una
    # pregunta distinta y la única que el dato permite.
    cancelados = db.scalar(
        select(func.count()).select_from(Canje).where(
            Canje.estado == CanjeEstado.CANCELADO,
            Canje.fecha_solicitud >= inicio,
            Canje.fecha_solicitud <= fin,
        )
    )

    return MetricasMes(
        etiqueta=f"{anio:04d}-{mes:02d}",
        hitos_cerrados=cerrados[0],
        comision_real_vp=cerrados[1],
        comision_total=cerrados[2],
        negocios_iniciados=iniciados or 0,
        canjes_solicitados=solicitados or 0,
        canjes_cerrados=canjes_cerrados or 0,
        canjes_cancelados=cancelados or 0,
    )


def _comparar(actual: MetricasMes, referencia: MetricasMes) -> Comparacion:
    variaciones = []
    for campo, nombre in METRICAS:
        a = Decimal(getattr(actual, campo))
        r = Decimal(getattr(referencia, campo))
        variaciones.append(
            Variacion(
                metrica=nombre,
                actual=a,
                referencia=r,
                absoluta=a - r,
                # Sin base no hay porcentaje. Ni infinito ni cien por ciento:
                # nulo, y que la pantalla diga que no hay con qué comparar.
                pct=None if r == CERO else ((a - r) / r * 100).quantize(Decimal("0.1")),
            )
        )
    return Comparacion(contra=referencia, variaciones=variaciones)


def obtener_reporte_mensual(
    db: Session, anio: int | None = None, mes: int | None = None, hoy: date | None = None
) -> ReporteMensual:
    hoy = hoy or datetime.now(timezone.utc).date()
    anio = anio or hoy.year
    mes = mes or hoy.month

    actual = _metricas(db, anio, mes)
    anterior = _metricas(db, *mes_anterior(anio, mes))
    anio_pasado = _metricas(db, anio - 1, mes)

    return ReporteMensual(
        mes=actual,
        mes_anterior=_comparar(actual, anterior),
        mismo_mes_anio_anterior=_comparar(actual, anio_pasado),
    )
