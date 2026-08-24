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
    # A qué reporte pertenece. Va como dato y no se deduce del nombre porque la
    # pantalla se separó en dos: filtrar por el texto visible se rompería al
    # renombrar una métrica, y sin fallar.
    dominio: str
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
    # Mes por mes de la ventana, del más viejo al más nuevo. Es lo que permite ver
    # si el mes actual avanza, se estanca o retrocede contra los que vinieron
    # antes: la comparación de la ventana contra la ventana anterior dice cuánto
    # cambió, pero no en qué dirección venía.
    serie: list[MetricasMes]
    # El promedio mensual de la ventana, para la línea de referencia del gráfico y
    # para la frase que compara el mes actual contra su propia normalidad.
    promedio: MetricasMes


# Qué se compara, y con qué nombre se muestra. El orden es el de lectura: la
# plata primero, el volumen despues.
# Se declaran por dominio y no en una lista sola porque la pantalla se separó en
# dos. Mezclarlas obligaría al frontend a filtrar por nombre, que es la clase de
# acoplamiento que se rompe en silencio al renombrar una métrica.
METRICAS_NEGOCIOS: tuple[tuple[str, str], ...] = (
    ("comision_real_vp", "Comisión real ViveProp"),
    ("comision_total", "Comisión total"),
    ("hitos_cerrados", "Liquidaciones cerradas"),
    ("negocios_iniciados", "Negocios iniciados"),
)

# Canjes no tiene eje de plata, y no es un olvido. Sí genera comisión --la de
# administración de Dataprop, 6/5/4% en venta según el tramo en UF u 8% en
# arriendo-- pero se calcula sobre la comisión de los corredores participantes,
# que está en cero en las 297 filas. Y `valor_prop`, que sería la alternativa, no
# se puede sumar: la moneda está equivocada en ~138 de las 297 filas --pesos
# etiquetados UF y UF etiquetados CLP-- y el campo mezcla precio de venta con
# arriendo mensual. Ver `D-054`.
METRICAS_CANJES: tuple[tuple[str, str], ...] = (
    ("canjes_solicitados", "Canjes solicitados"),
    ("canjes_cerrados", "Canjes cerrados"),
    ("canjes_cancelados", "Canjes cancelados"),
)

METRICAS: tuple[tuple[str, str], ...] = METRICAS_NEGOCIOS + METRICAS_CANJES


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


def _clave(f) -> str:
    """'2026-08' desde una fecha o un instante."""
    d = f.date() if isinstance(f, datetime) else f
    return f"{d.year:04d}-{d.month:02d}"


def _serie_mensual(db: Session, anio: int, mes: int, ventana: int) -> list[MetricasMes]:
    """Los meses de la ventana, uno por uno, con **cuatro consultas** en total.

    La forma obvia --llamar a `_metricas` una vez por mes-- costaría cinco
    consultas por mes, o sesenta para una ventana de doce. Acá se traen las filas
    del rango completo de una vez y se agrupan en Python. Es la misma decisión que
    `D-051` tomó para el agrupado por mes del dashboard, por el mismo motivo:
    contra Neon lo que cuesta es la latencia, no el trabajo.

    **Los meses vacíos van en cero, no se omiten.** Un mes sin cierres es
    justamente el dato que hay que ver --el negocio los tiene, ver el encabezado
    de este módulo-- y saltearlo dejaría un gráfico con seis barras un mes y cinco
    al siguiente.
    """
    a_ini, m_ini = correr_meses(anio, mes, -(ventana - 1))
    desde, _ = limites(a_ini, m_ini)
    _, hasta = limites(anio, mes)
    inicio = datetime.combine(desde, time.min, tzinfo=timezone.utc)
    fin = datetime.combine(hasta, time.max, tzinfo=timezone.utc)

    claves = []
    for i in range(ventana):
        ai, mi = correr_meses(a_ini, m_ini, i)
        claves.append(f"{ai:04d}-{mi:02d}")

    cerrados: dict[str, tuple[int, Decimal, Decimal]] = {}
    for fecha, real, total in db.execute(
        select(
            NegocioHito.fecha_cierre,
            func.coalesce(NegocioHito.comision_real_vp, 0),
            func.coalesce(NegocioHito.comision_total, 0),
        ).where(
            NegocioHito.estado == EstadoNegocio.CERRADO,
            NegocioHito.fecha_cierre >= desde,
            NegocioHito.fecha_cierre <= hasta,
        )
    ).all():
        k = _clave(fecha)
        n, r, tt = cerrados.get(k, (0, CERO, CERO))
        cerrados[k] = (n + 1, r + Decimal(real), tt + Decimal(total))

    # Un negocio se cuenta una vez, en el mes de su hito mas antiguo.
    primeros = (
        select(
            NegocioHito.negocio_id.label("negocio_id"),
            func.min(NegocioHito.fecha_inicio).label("inicio"),
        )
        .group_by(NegocioHito.negocio_id)
        .subquery()
    )
    iniciados: dict[str, int] = {}
    for (fecha,) in db.execute(
        select(primeros.c.inicio)
        .join(Negocio, Negocio.id == primeros.c.negocio_id)
        .where(primeros.c.inicio >= desde, primeros.c.inicio <= hasta)
    ).all():
        k = _clave(fecha)
        iniciados[k] = iniciados.get(k, 0) + 1

    # Solicitados y cancelados salen del mismo recorrido: los dos se cuentan por
    # fecha de solicitud, porque `canjes` no guarda cuándo se canceló.
    solicitados: dict[str, int] = {}
    cancelados: dict[str, int] = {}
    for fecha, estado in db.execute(
        select(Canje.fecha_solicitud, Canje.estado).where(
            Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin
        )
    ).all():
        k = _clave(fecha)
        solicitados[k] = solicitados.get(k, 0) + 1
        if estado == CanjeEstado.CANCELADO:
            cancelados[k] = cancelados.get(k, 0) + 1

    canjes_cerrados: dict[str, int] = {}
    for (fecha,) in db.execute(
        select(Canje.fecha_cierre).where(
            Canje.etapa == CanjeEtapa.CERRADO,
            Canje.fecha_cierre >= inicio,
            Canje.fecha_cierre <= fin,
        )
    ).all():
        k = _clave(fecha)
        canjes_cerrados[k] = canjes_cerrados.get(k, 0) + 1

    serie = []
    for k in claves:
        n, real, total = cerrados.get(k, (0, CERO, CERO))
        serie.append(
            MetricasMes(
                etiqueta=k,
                hitos_cerrados=n,
                comision_real_vp=real,
                comision_total=total,
                negocios_iniciados=iniciados.get(k, 0),
                canjes_solicitados=solicitados.get(k, 0),
                canjes_cerrados=canjes_cerrados.get(k, 0),
                canjes_cancelados=cancelados.get(k, 0),
            )
        )
    return serie


def _promedio(serie: list[MetricasMes]) -> MetricasMes:
    """El promedio mensual de la ventana.

    Es la referencia contra la que se lee el mes actual: "agosto está 47% bajo el
    promedio de los últimos 3 meses" dice si hay avance o retroceso, cosa que el
    número del mes solo no dice.

    **Incluye los meses en cero**, porque son parte de la normalidad de este
    negocio --de 11 meses con actividad, 4 estuvieron vacíos-- y excluirlos
    inflaría la referencia justo en el sentido que hace ver retroceso donde no hay.
    """
    n = len(serie) or 1

    def prom(campo: str) -> Decimal:
        total = sum((Decimal(getattr(m, campo)) for m in serie), CERO)
        return (total / n).quantize(Decimal("0.01"))

    return MetricasMes(
        etiqueta=f"promedio de {len(serie)} meses",
        hitos_cerrados=int(prom("hitos_cerrados")),
        comision_real_vp=prom("comision_real_vp"),
        comision_total=prom("comision_total"),
        negocios_iniciados=int(prom("negocios_iniciados")),
        canjes_solicitados=int(prom("canjes_solicitados")),
        canjes_cerrados=int(prom("canjes_cerrados")),
        canjes_cancelados=int(prom("canjes_cancelados")),
    )


DOMINIOS = {campo: "negocios" for campo, _ in METRICAS_NEGOCIOS} | {
    campo: "canjes" for campo, _ in METRICAS_CANJES
}


def _comparar(actual: MetricasMes, referencia: MetricasMes) -> Comparacion:
    variaciones = []
    for campo, nombre in METRICAS:
        a = Decimal(getattr(actual, campo))
        r = Decimal(getattr(referencia, campo))
        variaciones.append(
            Variacion(
                metrica=nombre,
                dominio=DOMINIOS[campo],
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

    # La serie reemplazó al bucle que contaba los meses vacíos: los vacíos salen
    # de ella, así que ya no hace falta recorrer la ventana dos veces.
    serie = _serie_mensual(db, anio, mes, ventana)

    return ReporteMensual(
        mes=detalle,
        ventana_meses=ventana,
        movil=_comparar(movil, movil_prev),
        anio_corrido=_comparar(corrido, corrido_prev),
        meses_sin_cierres=sum(1 for m in serie if m.hitos_cerrados == 0),
        meses_de_la_ventana=ventana,
        serie=serie,
        promedio=_promedio(serie),
    )
