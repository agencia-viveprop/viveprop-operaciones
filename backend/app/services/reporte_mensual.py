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
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import Catalogo, EstadoNegocio
from app.models.negocio import Negocio, NegocioHito

CERO = Decimal("0")
CENTAVO = Decimal("0.01")
DECIMA = Decimal("0.1")


class MetricasMes(BaseModel):
    """Lo que se mide en un mes. Sin totales cruzados entre dominios."""

    etiqueta: str  # '2026-08'

    # Negocios
    hitos_cerrados: int
    # El valor de los negocios cerrados en el mes, **partido por operación**.
    #
    # Van separados porque no son la misma unidad. En una venta la base es el
    # precio de la propiedad --cientos de millones--; en un arriendo es **un mes
    # de renta**, del orden del millón. Tanto que en los dos arriendos del
    # histórico la base coincide exactamente con la comisión total, porque en
    # arriendo la comisión es 50% + 50% de un mes: o sea, un mes.
    #
    # Sumarlos daría el mismo número sin sentido que hizo descartar `valor_prop`
    # en canjes (`D-054`): un total que mezcla precio de venta con renta mensual.
    # Y en un gráfico juntos el arriendo es invisible, porque son dos órdenes de
    # magnitud de diferencia.
    #
    # La venta va además **45 veces** por encima de su propia comisión, así que
    # tampoco comparte eje con las de abajo: se sirve para dibujarla aparte.
    #
    # Un negocio sin tipo de operación cae en venta, que es el caso dominante
    # --17 de 19-- y hoy no hay ninguno así. Es la única forma de que las dos
    # sumas den el total sin descartar filas en silencio.
    valor_venta: Decimal
    valor_arriendo: Decimal
    comision_total: Decimal
    # El reparto de esa comisión. Verificado liquidación por liquidación:
    #
    #     comision_total + rebate = broker + tercero + equipo + real_vp
    #
    # Cierra en 18 de las 19 del histórico. Seis se van por un centavo, porque
    # los siete montos se redondean cada uno por su lado. Y `VVP-2` se va por
    # 903.802,94, que es el descuadre conocido y todavía sin resolver.
    #
    # El rebate no es una tajada de la comisión: es plata que **entra** desde
    # afuera --la paga el concentrador por lo que le cobró al vendedor-- y por
    # eso está del lado izquierdo de la identidad y no del derecho (`D-018`).
    comision_broker: Decimal
    comision_equipo: Decimal
    comision_tercero: Decimal
    rebate_concentrador: Decimal
    comision_real_vp: Decimal
    negocios_iniciados: int

    # Canjes
    canjes_solicitados: int
    canjes_cerrados: int
    canjes_cancelados: int
    # Los que siguen vivos, contados como los cancelados: por su mes de solicitud.
    #
    # `canjes_solicitados = canjes_activos + canjes_cancelados` **exacto**, porque
    # el estado solo tiene esos dos valores. Esa identidad es la que permite
    # dibujarlos apilados: el total de la barra es la solicitud y el activo es un
    # segmento propio, en vez de una barra de 1 al lado de una de 28 donde no se ve.
    canjes_activos: int


class PromedioMes(BaseModel):
    """El promedio mensual de la ventana. **Todos los campos son decimales.**

    No reusa `MetricasMes` porque ahí los conteos son enteros, y el promedio de un
    conteo no lo es: cuatro liquidaciones en seis meses son 0,67 por mes, no 0.
    La primera versión lo truncaba con `int()` y el resultado era que el reporte
    afirmaba un promedio de **cero** liquidaciones habiendo cuatro, y que la línea
    de referencia de los canjes activos desaparecía por quedar en cero.

    Un promedio truncado no es un promedio: es un promedio equivocado.
    """

    etiqueta: str
    hitos_cerrados: Decimal
    valor_venta: Decimal
    valor_arriendo: Decimal
    comision_total: Decimal
    comision_broker: Decimal
    comision_equipo: Decimal
    comision_tercero: Decimal
    rebate_concentrador: Decimal
    comision_real_vp: Decimal
    negocios_iniciados: Decimal
    canjes_solicitados: Decimal
    canjes_cerrados: Decimal
    canjes_cancelados: Decimal
    canjes_activos: Decimal


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
    # Si se muestra en pesos o como conteo. Por el mismo motivo que `dominio`:
    # la pantalla lo resolvía con un conjunto de **nombres visibles**, así que
    # renombrar "Comisión total" la dejaba mostrando 34842291.97 sin signo de
    # peso y sin fallar en ninguna parte. El catálogo de métricas es el único
    # lugar donde esto se sabe, así que sale de ahí.
    es_plata: bool
    actual: Decimal
    referencia: Decimal
    absoluta: Decimal
    pct: Decimal | None


class Tendencia(BaseModel):
    """La recta que mejor ajusta la serie, por mínimos cuadrados.

    **Qué agrega sobre el promedio.** El promedio dice si el mes está por encima o
    por debajo de lo normal; la tendencia dice **hacia dónde va la ventana**. Son
    preguntas distintas y las dos hacen falta: una ventana puede estar toda sobre
    su promedio y venir cayendo.

    `desde` y `hasta` son el valor ajustado en el primer y el último mes. Van
    calculados acá para que la pantalla dibuje la recta con dos puntos y no tenga
    que repetir el ajuste --y para que el ajuste tenga tests, que es donde este
    proyecto los tiene.

    **Con tres meses una tendencia es casi una anécdota.** Se calcula igual porque
    la ventana la elige quien lee, pero `puntos` viaja con el resto para que la
    pantalla pueda decir sobre cuántos meses se trazó.
    """

    metrica: str
    dominio: str
    puntos: int
    # Cuánto cambia por mes, en las unidades de la métrica.
    pendiente: Decimal
    # La pendiente como porcentaje del promedio de la serie. Nulo si el promedio
    # es cero: ahí no hay porcentaje que calcular, igual que en `Variacion`.
    pct_por_mes: Decimal | None
    direccion: str  # 'sube' | 'baja' | 'plana'
    desde: Decimal
    hasta: Decimal


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
    # Cuántos meses de la ventana **ya tenían negocios**, que no siempre es el
    # largo de la ventana: en la histórica, los meses previos al primer negocio no
    # cuentan. Se llamaba `meses_de_la_ventana` y el nombre dejó de ser cierto
    # cuando la histórica entró, así que se renombró en vez de dejarlo mintiendo.
    meses_con_negocios: int
    # Mes por mes de la ventana, del más viejo al más nuevo. Es lo que permite ver
    # si el mes actual avanza, se estanca o retrocede contra los que vinieron
    # antes: la comparación de la ventana contra la ventana anterior dice cuánto
    # cambió, pero no en qué dirección venía.
    serie: list[MetricasMes]
    # `true` cuando la ventana es la histórica. La pantalla lo necesita para dos
    # cosas: rotularla "Histórico" en vez de "46 meses", y **no** mostrar la
    # comparación contra la ventana anterior, porque antes del primer registro no
    # hay nada con qué comparar y la tabla saldría toda en "sin base".
    es_historico: bool
    # Desde qué mes existe cada dominio, en formato '2025-08'. Es desde donde se
    # promedia y se traza la tendencia de sus métricas: en la ventana histórica,
    # los meses previos al primer negocio no son meses malos, son meses sin
    # negocio, y promediarlos dejaría la referencia cuatro veces más baja.
    inicio_por_dominio: dict[str, str | None]
    # El promedio mensual de la ventana, para la línea de referencia del gráfico y
    # para la frase que compara el mes actual contra su propia normalidad.
    promedio: PromedioMes
    # La tendencia de cada métrica sobre la ventana, indexada por su campo.
    tendencias: dict[str, Tendencia]


# Qué se compara, y con qué nombre se muestra. El orden es el de lectura: la
# plata primero, el volumen despues.
# Se declaran por dominio y no en una lista sola porque la pantalla se separó en
# dos. Mezclarlas obligaría al frontend a filtrar por nombre, que es la clase de
# acoplamiento que se rompe en silencio al renombrar una métrica.
METRICAS_NEGOCIOS: tuple[tuple[str, str, bool], ...] = (
    ("valor_venta", "Monto de las ventas", True),
    ("valor_arriendo", "Monto de los arriendos", True),
    ("comision_total", "Comisión total", True),
    ("comision_broker", "Comisión de los corredores", True),
    ("comision_equipo", "Comisión del equipo ViveProp", True),
    ("comision_tercero", "Comisión de terceros", True),
    ("rebate_concentrador", "Rebate de los concentradores", True),
    ("comision_real_vp", "Comisión real ViveProp", True),
    ("hitos_cerrados", "Liquidaciones cerradas", False),
    ("negocios_iniciados", "Negocios iniciados", False),
)

# Canjes no tiene eje de plata, y no es un olvido. Sí genera comisión --la de
# administración de Dataprop, 6/5/4% en venta según el tramo en UF u 8% en
# arriendo-- pero se calcula sobre la comisión de los corredores participantes,
# que está en cero en las 297 filas. Y `valor_prop`, que sería la alternativa, no
# se puede sumar: la moneda está equivocada en ~138 de las 297 filas --pesos
# etiquetados UF y UF etiquetados CLP-- y el campo mezcla precio de venta con
# arriendo mensual. Ver `D-054`.
METRICAS_CANJES: tuple[tuple[str, str, bool], ...] = (
    ("canjes_solicitados", "Canjes solicitados", False),
    ("canjes_activos", "Canjes activos", False),
    ("canjes_cerrados", "Canjes cerrados", False),
    ("canjes_cancelados", "Canjes cancelados", False),
)

METRICAS: tuple[tuple[str, str, bool], ...] = METRICAS_NEGOCIOS + METRICAS_CANJES

# Las columnas de plata de una liquidación, con el nombre del campo de
# `MetricasMes` que alimentan. `valor_base` es híbrida: el manual manda cuando
# existe, si no la conversión por UF (`D-017`), y es la misma regla que usa el
# motor de comisiones para calcular sobre ella.
PLATA_DEL_HITO: tuple[str, ...] = (
    "valor_venta",
    "valor_arriendo",
    "comision_total",
    "comision_broker",
    "comision_equipo",
    "comision_tercero",
    "rebate_concentrador",
    "comision_real_vp",
)


def _columnas_de_plata():
    """Las ocho columnas de plata, en el orden de `PLATA_DEL_HITO`.

    Las consultas que las usan tienen que traer `Negocio` y su catálogo de
    operación: las dos primeras dependen de si el negocio es venta o arriendo.
    """
    base = func.coalesce(NegocioHito.valor_clp_manual, NegocioHito.valor_clp_calculado, 0)
    es_arriendo = Catalogo.codigo == "ARRIENDO"
    return (
        case((es_arriendo, 0), else_=base),
        case((es_arriendo, base), else_=0),
        func.coalesce(NegocioHito.comision_total, 0),
        func.coalesce(NegocioHito.comision_broker, 0),
        func.coalesce(NegocioHito.comision_equipo, 0),
        func.coalesce(NegocioHito.comision_tercero, 0),
        func.coalesce(NegocioHito.rebate_concentrador, 0),
        func.coalesce(NegocioHito.comision_real_vp, 0),
    )


def limites(anio: int, mes: int) -> tuple[date, date]:
    """El primer y el último día del mes."""
    return date(anio, mes, 1), date(anio, mes, monthrange(anio, mes)[1])


def mes_anterior(anio: int, mes: int) -> tuple[int, int]:
    return (anio - 1, 12) if mes == 1 else (anio, mes - 1)


# Cero significa "histórico": toda la serie, desde el primer registro.
#
# Va como centinela y no como una ventana de N meses porque el largo lo decide el
# dato, no quien pregunta: hoy son 46 meses --canjes arrancan en noviembre de
# 2022-- y el mes que viene serán 47. El servicio lo resuelve al número real y lo
# devuelve en `ventana_meses`, así que el resto del cálculo no cambia.
VENTANA_HISTORICO = 0

VENTANAS_VALIDAS = (VENTANA_HISTORICO, 3, 6, 12)
VENTANA_DEFECTO = 6


def _primer_mes_con_datos(db: Session) -> tuple[int, int]:
    """El mes más viejo con algo registrado, mirando los dos dominios.

    Es el arranque de la ventana histórica. Si no hay ni un dato devuelve el mes
    actual, que da una ventana de un mes: vacía, pero no una serie de largo cero
    que rompería el promedio y la tendencia.
    """
    fechas = [
        db.scalar(select(func.min(NegocioHito.fecha_inicio))),
        db.scalar(select(func.min(Canje.fecha_solicitud))),
    ]
    concretas = [f.date() if isinstance(f, datetime) else f for f in fechas if f is not None]
    if not concretas:
        hoy = datetime.now(timezone.utc).date()
        return hoy.year, hoy.month
    primera = min(concretas)
    return primera.year, primera.month


def _meses_entre(desde: tuple[int, int], hasta: tuple[int, int]) -> int:
    """Cuántos meses cubre el rango, con los dos extremos incluidos."""
    (a1, m1), (a2, m2) = desde, hasta
    return (a2 - a1) * 12 + (m2 - m1) + 1


# El primer mes con actividad de cada dominio, para que el promedio y la tendencia
# no se diluyan con meses en los que ese dominio no existía.
#
# **Por qué hace falta.** Negocios arranca en agosto de 2025 y canjes en noviembre
# de 2022. Promediar la comisión sobre los 46 meses históricos la reparte entre 34
# meses en los que ViveProp no tenía ni un negocio cargado: el promedio queda
# cuatro veces más bajo de lo real y un mes malo se lee como bueno contra él. La
# referencia tiene que empezar donde empieza el dominio.
def _inicio_por_dominio(db: Session) -> dict[str, tuple[int, int] | None]:
    def mes_de(valor) -> tuple[int, int] | None:
        if valor is None:
            return None
        d = valor.date() if isinstance(valor, datetime) else valor
        return d.year, d.month

    return {
        "negocios": mes_de(db.scalar(select(func.min(NegocioHito.fecha_inicio)))),
        "canjes": mes_de(db.scalar(select(func.min(Canje.fecha_solicitud)))),
    }


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
            *(func.coalesce(func.sum(c), 0) for c in _columnas_de_plata()),
        )
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.tipo_operacion_id)
        .where(
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
    # pregunta distinta y la única que el dato permite. Los activos van con el
    # mismo criterio, para que sumen con los cancelados el total de solicitados.
    cancelados = db.scalar(
        select(func.count()).select_from(Canje).where(
            Canje.estado == CanjeEstado.CANCELADO,
            Canje.fecha_solicitud >= inicio,
            Canje.fecha_solicitud <= fin,
        )
    )
    activos = db.scalar(
        select(func.count()).select_from(Canje).where(
            Canje.estado == CanjeEstado.ACTIVO,
            Canje.fecha_solicitud >= inicio,
            Canje.fecha_solicitud <= fin,
        )
    )

    return MetricasMes(
        etiqueta=etiqueta,
        hitos_cerrados=cerrados[0],
        **{campo: cerrados[i + 1] for i, campo in enumerate(PLATA_DEL_HITO)},
        negocios_iniciados=iniciados or 0,
        canjes_solicitados=solicitados or 0,
        canjes_cerrados=canjes_cerrados or 0,
        canjes_cancelados=cancelados or 0,
        canjes_activos=activos or 0,
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

    # Por mes: cuántas liquidaciones cerraron y las siete sumas de plata. Van
    # todas en el mismo recorrido porque salen de las mismas filas; separarlas
    # serían siete consultas para leer dos veces lo mismo.
    cerrados: dict[str, tuple[int, dict[str, Decimal]]] = {}
    for fila in db.execute(
        select(NegocioHito.fecha_cierre, *_columnas_de_plata())
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.tipo_operacion_id)
        .where(
            NegocioHito.estado == EstadoNegocio.CERRADO,
            NegocioHito.fecha_cierre >= desde,
            NegocioHito.fecha_cierre <= hasta,
        )
    ).all():
        k = _clave(fila[0])
        n, plata = cerrados.get(k, (0, {campo: CERO for campo in PLATA_DEL_HITO}))
        cerrados[k] = (
            n + 1,
            {campo: plata[campo] + Decimal(fila[i + 1]) for i, campo in enumerate(PLATA_DEL_HITO)},
        )

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
    activos: dict[str, int] = {}
    for fecha, estado in db.execute(
        select(Canje.fecha_solicitud, Canje.estado).where(
            Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin
        )
    ).all():
        k = _clave(fecha)
        solicitados[k] = solicitados.get(k, 0) + 1
        if estado == CanjeEstado.CANCELADO:
            cancelados[k] = cancelados.get(k, 0) + 1
        else:
            activos[k] = activos.get(k, 0) + 1

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
        n, plata = cerrados.get(k, (0, {campo: CERO for campo in PLATA_DEL_HITO}))
        serie.append(
            MetricasMes(
                etiqueta=k,
                hitos_cerrados=n,
                **plata,
                negocios_iniciados=iniciados.get(k, 0),
                canjes_solicitados=solicitados.get(k, 0),
                canjes_cerrados=canjes_cerrados.get(k, 0),
                canjes_cancelados=cancelados.get(k, 0),
                canjes_activos=activos.get(k, 0),
            )
        )
    return serie


def _desde_el_inicio(
    serie: list[MetricasMes], inicio: tuple[int, int] | None
) -> list[MetricasMes]:
    """La parte de la serie a partir del mes en que ese dominio empezó a existir.

    En una ventana de 3, 6 o 12 meses no recorta nada --el dominio ya existía en
    todo el tramo-- así que solo cambia algo en la histórica, que es donde hace
    falta: ahí los 34 meses previos al primer negocio no son meses malos, son
    meses sin negocio.

    Si el dominio no tiene ni un registro se devuelve la serie entera: el promedio
    dará cero y eso es lo correcto.
    """
    if inicio is None:
        return serie
    clave = f"{inicio[0]:04d}-{inicio[1]:02d}"
    return [m for m in serie if m.etiqueta >= clave] or serie


def _promedio(
    serie: list[MetricasMes], inicios: dict[str, tuple[int, int] | None] | None = None
) -> PromedioMes:
    """El promedio mensual de la ventana.

    Es la referencia contra la que se lee el mes actual: "agosto está 47% bajo el
    promedio de los últimos 3 meses" dice si hay avance o retroceso, cosa que el
    número del mes solo no dice.

    **Incluye los meses en cero**, porque son parte de la normalidad de este
    negocio --de 11 meses con actividad, 4 estuvieron vacíos-- y excluirlos
    inflaría la referencia justo en el sentido que hace ver retroceso donde no hay.

    **No redondea a entero.** Ver `PromedioMes`: el promedio de un conteo es
    fraccionario, y truncarlo dio un promedio de cero liquidaciones habiendo cuatro.
    """
    inicios = inicios or {}

    def prom(campo: str) -> Decimal:
        # Cada métrica promedia sobre los meses en que su dominio ya existía. En
        # las ventanas de 3, 6 y 12 eso es toda la serie; en la histórica no.
        tramo = _desde_el_inicio(serie, inicios.get(DOMINIOS[campo]))
        total = sum((Decimal(getattr(m, campo)) for m in tramo), CERO)
        return (total / (len(tramo) or 1)).quantize(CENTAVO)

    return PromedioMes(
        etiqueta=f"promedio de {len(serie)} meses",
        **{campo: prom(campo) for campo, _, _ in METRICAS},
    )


# A qué reporte pertenece cada métrica. Se deriva de las dos listas por dominio
# en vez de escribirse de nuevo: una tercera copia de la misma partición es una
# tercera cosa que se puede desincronizar.
DOMINIOS = {campo: "negocios" for campo, _, _ in METRICAS_NEGOCIOS} | {
    campo: "canjes" for campo, _, _ in METRICAS_CANJES
}

# Si cada métrica se muestra en pesos. Sale del catálogo por el mismo motivo
# que `DOMINIOS`: es el único lugar donde el dato se conoce de verdad.
ES_PLATA = {campo: plata for campo, _, plata in METRICAS}


# Debajo de este porcentaje mensual la serie se declara plana. Con volúmenes de
# ~1 cierre por mes, una pendiente chica es ruido y llamarla tendencia sería
# darle una lectura que el dato no aguanta.
UMBRAL_PLANA = Decimal("3")


def _tendencia(
    serie: list[MetricasMes],
    campo: str,
    nombre: str,
    inicio: tuple[int, int] | None = None,
) -> Tendencia:
    """Mínimos cuadrados sobre los meses de la ventana.

    Los meses van como 0, 1, 2... así que la pendiente sale directamente en
    unidades por mes. Con un solo punto no hay recta: se devuelve plana en su
    propio valor, que es lo único cierto.
    """
    # Igual que el promedio: la recta arranca donde arranca el dominio. Ajustarla
    # sobre 34 meses en cero seguidos de 12 con datos daría una pendiente que
    # describe el nacimiento del negocio, no su tendencia.
    serie = _desde_el_inicio(serie, inicio)
    n = len(serie)
    ys = [Decimal(getattr(m, campo)) for m in serie]
    media_y = sum(ys, CERO) / n if n else CERO

    if n < 2:
        return Tendencia(
            metrica=nombre,
            dominio=DOMINIOS[campo],
            puntos=n,
            pendiente=CERO,
            pct_por_mes=None,
            direccion="plana",
            desde=media_y.quantize(CENTAVO),
            hasta=media_y.quantize(CENTAVO),
        )

    media_x = Decimal(n - 1) / 2
    numerador = sum(
        ((Decimal(i) - media_x) * (y - media_y) for i, y in enumerate(ys)), CERO
    )
    denominador = sum(((Decimal(i) - media_x) ** 2 for i in range(n)), CERO)
    pendiente = (numerador / denominador) if denominador else CERO
    intercepto = media_y - pendiente * media_x

    pct = None if media_y == CERO else (pendiente / media_y * 100).quantize(DECIMA)
    if pct is None or abs(pct) < UMBRAL_PLANA:
        direccion = "plana"
    else:
        direccion = "sube" if pendiente > CERO else "baja"

    return Tendencia(
        metrica=nombre,
        dominio=DOMINIOS[campo],
        puntos=n,
        pendiente=pendiente.quantize(CENTAVO),
        pct_por_mes=pct,
        direccion=direccion,
        # La recta se recorta en cero: una proyección negativa de un conteo o de
        # una comisión no existe, y dibujarla bajo el eje sugeriría que sí.
        desde=max(intercepto, CERO).quantize(CENTAVO),
        hasta=max(intercepto + pendiente * Decimal(n - 1), CERO).quantize(CENTAVO),
    )


def _comparar(actual: MetricasMes, referencia: MetricasMes) -> Comparacion:
    variaciones = []
    for campo, nombre, _ in METRICAS:
        a = Decimal(getattr(actual, campo))
        r = Decimal(getattr(referencia, campo))
        variaciones.append(
            Variacion(
                metrica=nombre,
                dominio=DOMINIOS[campo],
                es_plata=ES_PLATA[campo],
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

    # La histórica se resuelve al número real de meses acá, una sola vez, y de ahí
    # en adelante el cálculo es el mismo que para cualquier otra ventana.
    es_historico = ventana == VENTANA_HISTORICO
    if es_historico:
        ventana = _meses_entre(_primer_mes_con_datos(db), (anio, mes))

    inicios = _inicio_por_dominio(db)

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
        # Los dos van sobre el tramo en que negocios ya existía: "39 de los
        # últimos 46 meses estuvieron vacíos" sería cierto y engañoso, porque 33
        # de esos meses no tenían ni un negocio cargado.
        meses_sin_cierres=sum(
            1 for m in _desde_el_inicio(serie, inicios.get("negocios"))
            if m.hitos_cerrados == 0
        ),
        meses_con_negocios=len(_desde_el_inicio(serie, inicios.get("negocios"))),
        serie=serie,
        es_historico=es_historico,
        inicio_por_dominio={
            dom: (f"{v[0]:04d}-{v[1]:02d}" if v else None) for dom, v in inicios.items()
        },
        promedio=_promedio(serie, inicios),
        tendencias={
            campo: _tendencia(serie, campo, nombre, inicios.get(DOMINIOS[campo]))
            for campo, nombre, _ in METRICAS
        },
    )
