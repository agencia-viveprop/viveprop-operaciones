"""Reporte mensual comparativo, con ventanas móviles.

**El mes calendario no es la unidad natural de este negocio.** Los procesos duran
de un mes a varios, así que un mes en cero no es un mes malo: es que ningún
proceso terminó de madurar. Medido sobre los datos reales: de 11 meses con
actividad, **4 estuvieron vacíos** (36%), y el ticket varía cuatro veces --entre
516.304 y 2.110.526--. Con ~1 cierre por mes y esa dispersión, la comparación mes
contra mes no mide desempeño, mide ruido.

Por eso el titular es una **ventana móvil** contra la ventana equivalente
anterior, y el mes calendario queda como detalle de "qué pasó". Sobre los mismos
datos, la serie mensual es 0 / 2,1M / 0 / 0 / 1,05M --ilegible-- y la de seis
meses cuenta algo: subió hasta 5,2M en diciembre y viene bajando a 2,8M.

**La ventana entra por parámetro** (3, 6 o 12 meses) porque el horizonte correcto
depende de qué se está mirando, y quien lee el reporte lo sabe mejor. El default
es 6.

**El acumulado del año va aparte**, contra el mismo tramo del año anterior. Es la
comparación que pide un cierre anual, y no es lo mismo que la ventana móvil.

**Lo que se descartó: el "mismo mes del año anterior" como titular.** La
estacionalidad necesita dos o tres años para ser medible; hoy compararía 1 contra
0. Y un gráfico de veinticuatro meses responde otra pregunta, ya cubierta por los
de "por mes" del dashboard.

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
    # Los dos lados van explícitos: la ventana móvil no coincide con el mes
    # calendario, así que `actual` no se puede deducir del resto del reporte.
    actual: MetricasMes
    contra: MetricasMes
    variaciones: list[Variacion]


class ReporteMensual(BaseModel):
    # El mes calendario, como detalle de "qué pasó". Ya no es el titular.
    mes: MetricasMes
    ventana_meses: int
    # El titular: la ventana móvil contra la ventana equivalente anterior.
    movil: Comparacion
    # El acumulado del año contra el mismo tramo del año anterior.
    anio_corrido: Comparacion
    # Cuántos meses de la ventana no tuvieron ni un cierre, y sobre cuántos.
    # Va calculado y no escrito en la pantalla: el texto que explica un mes en
    # cero decía "4 de 11 meses" a mano, y eso deja de ser cierto el mes
    # siguiente. Un dato que envejece mal es peor que ninguno, porque nadie se
    # entera de que dejó de valer.
    meses_sin_cierres: int
    meses_de_la_ventana: int


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


VENTANAS_VALIDAS = (3, 6, 12)
VENTANA_DEFECTO = 6


def correr_meses(anio: int, mes: int, cuantos: int) -> tuple[int, int]:
    """El mes que está `cuantos` meses antes (o después, si es positivo)."""
    total = (anio * 12 + (mes - 1)) + cuantos
    return total // 12, total % 12 + 1


def rango_ventana(anio: int, mes: int, meses: int) -> tuple[date, date]:
    """La ventana de N meses que **termina** en ese mes, con el mes incluido.

    Una ventana de 6 que termina en agosto va del 1 de marzo al 31 de agosto.
    """
    a_inicio, m_inicio = correr_meses(anio, mes, -(meses - 1))
    return date(a_inicio, m_inicio, 1), limites(anio, mes)[1]


def rango_anio_corrido(anio: int, mes: int) -> tuple[date, date]:
    """De enero al último día de ese mes.

    Se compara contra el **mismo tramo** del año anterior, no contra el año
    entero: enero-agosto contra enero-agosto. Comparar ocho meses contra doce
    diría que el año viene mal cuando solo viene incompleto.
    """
    return date(anio, 1, 1), limites(anio, mes)[1]


def _metricas(db: Session, desde: date, hasta: date, etiqueta: str) -> MetricasMes:
    """Las métricas de un rango cualquiera de fechas, con los dos bordes incluidos.

    Trabaja con un rango y no con un mes porque las ventanas móviles y el
    acumulado del año son rangos de varios meses. El mes calendario es un rango
    como cualquier otro.
    """
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
        etiqueta=etiqueta,
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
    return Comparacion(actual=actual, contra=referencia, variaciones=variaciones)


def _rotulo_ventana(desde: date, hasta: date) -> str:
    return f"{desde:%Y-%m} a {hasta:%Y-%m}"


def obtener_reporte_mensual(
    db: Session,
    anio: int | None = None,
    mes: int | None = None,
    ventana: int = VENTANA_DEFECTO,
    hoy: date | None = None,
) -> ReporteMensual:
    hoy = hoy or datetime.now(timezone.utc).date()
    anio = anio or hoy.year
    mes = mes or hoy.month
    if ventana not in VENTANAS_VALIDAS:
        raise ValueError(f"La ventana tiene que ser una de {VENTANAS_VALIDAS}.")

    # El mes calendario, como detalle.
    desde_mes, hasta_mes = limites(anio, mes)
    detalle = _metricas(db, desde_mes, hasta_mes, f"{anio:04d}-{mes:02d}")

    # La ventana móvil y la inmediatamente anterior, del mismo largo.
    desde_v, hasta_v = rango_ventana(anio, mes, ventana)
    a_prev, m_prev = correr_meses(anio, mes, -ventana)
    desde_p, hasta_p = rango_ventana(a_prev, m_prev, ventana)

    movil = _metricas(db, desde_v, hasta_v, _rotulo_ventana(desde_v, hasta_v))
    movil_prev = _metricas(db, desde_p, hasta_p, _rotulo_ventana(desde_p, hasta_p))

    # El año corrido contra el mismo tramo del año anterior.
    desde_a, hasta_a = rango_anio_corrido(anio, mes)
    desde_ap, hasta_ap = rango_anio_corrido(anio - 1, mes)
    corrido = _metricas(db, desde_a, hasta_a, _rotulo_ventana(desde_a, hasta_a))
    corrido_prev = _metricas(db, desde_ap, hasta_ap, _rotulo_ventana(desde_ap, hasta_ap))

    # Se recorre la ventana mes por mes solo para contar los vacíos. Son tres,
    # seis o doce consultas cortas; la alternativa era un GROUP BY por mes que
    # duplicaría la lógica de `_metricas`.
    vacios = 0
    for atras in range(ventana):
        a_i, m_i = correr_meses(anio, mes, -atras)
        d_i, h_i = limites(a_i, m_i)
        if _metricas(db, d_i, h_i, "").hitos_cerrados == 0:
            vacios += 1

    return ReporteMensual(
        mes=detalle,
        ventana_meses=ventana,
        movil=_comparar(movil, movil_prev),
        anio_corrido=_comparar(corrido, corrido_prev),
        meses_sin_cierres=vacios,
        meses_de_la_ventana=ventana,
    )
