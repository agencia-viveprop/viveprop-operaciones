"""Las piezas del reporte por período: semanas, flujo, embudo y la foto por etapa.

Viven acá y no en `reporte_semanal.py` para que ese módulo sea solo el armado de
la respuesta. Acá está el cálculo, y cada función responde una pregunta sobre un
rango de fechas.

**Las semanas se cuentan desde el día 1 del mes**, no de lunes a domingo. Del 1 al
7, del 8 al 14, y así, con la última cortada donde termina el mes: un mes de 31
días da cinco tramos y febrero da cuatro. Es la «cantidad de semanas reales de
cada mes» que se pidió. Con semanas calendario la primera y la última se meterían
en el mes vecino, y eso contradice que la base sea el mes.

**La última semana es parcial** --tres días en un mes de 31-- así que siempre va a
verse más baja. `dias` lo dice y la pantalla lo rotula, para que esa caída se lea
como lo que es y no como una caída de actividad.

**Qué se puede medir y qué no**, medido sobre los datos y no supuesto:

| Señal | Canjes | Negocios |
|---|---|---|
| Entraron | fecha de solicitud | fecha de inicio de la liquidación |
| Avanzaron | movimientos con etapa | **nada**: el pipeline no tiene movimientos |
| Se cayeron | cancelación + `fecha_cierre` (`D-086`) | **nada**: las 10 perdidas no tienen fecha |
| Plata por etapa | comisión de Dataprop | comisión real ViveProp |

Los dos huecos de negocios son del estado del proyecto, no del cálculo: se
informan en la pantalla en vez de dibujar una serie de ceros, que se leería como
«no pasó nada» cuando lo que pasa es «no se sabe».
"""
from calendar import monthrange
from datetime import date, datetime, time, timezone
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, OperacionTipo
from app.models.catalogo import Catalogo, EstadoNegocio
from app.models.movimiento import EntityType, Movimiento
# El mismo ajuste que usa la tendencia del reporte mensual: dos gráficos de la
# misma app no pueden decir «sube» con criterios distintos (`D-100`).
from app.services.reporte_mensual import ajustar_serie
from app.models.negocio import Negocio, NegocioHito
from app.services.comisiones_canjes import calcular
from app.services.plata_canjes import uf_del_canje

CERO = Decimal("0")

# Los estados de liquidación que cuentan como caída.
CAIDA_NEGOCIO = (EstadoNegocio.PERDIDO, EstadoNegocio.DESISTIDO)


class Semana(BaseModel):
    """Un tramo del mes. `dias` va porque el último es parcial."""

    etiqueta: str
    desde: date
    hasta: date
    dias: int


class FlujoDelMes(BaseModel):
    """El movimiento de un mes, semana por semana.

    Las tres listas tienen un valor por semana, en el orden de `Semana`. La plata
    acompaña a «entraron»: es la comisión esperada de lo que entró, que es la
    pregunta que se puede responder en el momento de entrar. La de «se cayeron» es
    la que no se concretó.
    """

    mes: str
    entraron: list[int]
    avanzaron: list[int]
    se_cayeron: list[int]
    comision_entraron: list[Decimal]


# Cuántos días tiene una semana entera. Los tramos del mes se cortan cada siete
# días, así que el único que puede venir corto es el último.
LARGO_DE_SEMANA = 7


class TendenciaSemanal(BaseModel):
    """Una sola curva por gráfico: cómo se mueve el mes por dentro, semana a semana.

    **Se ajusta sobre el promedio de cada semana en toda la ventana comparada**, no
    sobre el mes elegido solo: es lo que pidió el usuario --«debería considerar la
    ventana de comparación que se está mirando»--. Con tres meses, el punto de la
    S2 es el promedio de las tres S2. Así una semana rara de un mes no define la
    forma, y ampliar la ventana hace la curva más firme en vez de agregarle líneas.

    **La semana parcial queda fuera del ajuste, y por eso `semanas` puede ser menor
    que los tramos del mes.** La última tiene tres días en un mes de 31, así que su
    nivel es más bajo por calendario: metiéndola, la curva bajaría al final
    *siempre*, en todos los meses y todas las métricas, y eso no es una tendencia
    sino el artefacto de un mes que no se divide en siete. Normalizarla a «ritmo de
    siete días» era la otra salida y se descartó: pondría en el gráfico un valor
    proyectado al lado de barras de días reales, y quien compare la curva con la
    barra de esa semana leería un número que no ocurrió.

    Con eso quedan cuatro semanas completas en cualquier mes, y el grado que
    sostienen cuatro puntos es **1**: una recta (ver `_grado_de_tendencia`). Con
    cuatro, una curva pasa por todos los puntos y deja de ser una tendencia --es el
    dato redibujado--. Es la misma regla que ya rige la del reporte mensual
    (`D-089`), y por eso las dos usan `ajustar_serie`.

    `curva` trae un valor por semana completa, en orden desde la primera.
    """

    # Cuántas semanas completas sostienen el ajuste.
    semanas: int
    # Cuántos meses de la ventana entraron en el promedio de cada semana.
    meses: int
    grado: int
    curva: list[Decimal]
    # sube | baja | plana
    direccion: str
    pct_por_semana: Decimal | None
    mostrar: bool


def tendencia_de_las_semanas(
    semanas: list[Semana],
    flujo: list[FlujoDelMes],
    señal: str,
) -> TendenciaSemanal:
    """El promedio de cada semana completa en la ventana, ajustado.

    `flujo` viene con el mes elegido primero y los anteriores después; los usa a
    todos, porque la ventana que se está mirando es la que tiene que pesar.
    """
    completas = [i for i, s in enumerate(semanas) if s.dias >= LARGO_DE_SEMANA]

    promedios: list[Decimal] = []
    for i in completas:
        # Un mes puede tener menos tramos que otro --febrero tiene cuatro-- así que
        # se salta el que no llega a esa semana en vez de contarla como cero.
        valores = [getattr(f, señal)[i] for f in flujo if i < len(getattr(f, señal))]
        if valores:
            promedios.append(Decimal(sum(valores)) / len(valores))

    ajuste = ajustar_serie(promedios)
    return TendenciaSemanal(
        semanas=ajuste.puntos,
        meses=len(flujo),
        grado=ajuste.grado,
        curva=ajuste.curva,
        direccion=ajuste.direccion,
        pct_por_semana=ajuste.pct_por_paso,
        mostrar=ajuste.mostrar,
    )


class EtapaDelEmbudo(BaseModel):
    """Cuántos entraron a una etapa en el mes, contra el promedio de los anteriores."""

    etapa: str
    entraron: int
    promedio_anteriores: Decimal


class EtapaAbierta(BaseModel):
    """Dónde está lo que sigue abierto, cuánta plata hay ahí y cuánto lleva.

    `n` va siempre a la vista: con siete canjes repartidos en cuatro etapas, el
    promedio de una etapa puede ser un solo caso, y sin el `n` se lee como una
    tendencia.

    `sin_historia` son los que no tienen movimiento que registre la entrada a la
    etapa; ahí el reloj se cuenta desde el inicio, que no es lo mismo.
    """

    etapa: str
    casos: int
    comision: Decimal
    dias_promedio: int
    dias_min: int
    dias_max: int
    sin_historia: int


class TotalDelMes(BaseModel):
    """El mes entero, para el bloque de tendencia.

    El campo se llama `etiqueta` y no `mes` para poder pasar la lista por la
    maquinaria de tendencia del reporte mensual sin un adaptador en medio: esa
    función lee `etiqueta` de cada punto.
    """

    etiqueta: str
    entraron: int
    avanzaron: int
    se_cayeron: int
    comision: Decimal
    valor_venta: Decimal
    valor_arriendo: Decimal


def semanas_del_mes(anio: int, mes: int) -> list[Semana]:
    ultimo = monthrange(anio, mes)[1]
    semanas, dia, numero = [], 1, 1
    while dia <= ultimo:
        fin = min(dia + 6, ultimo)
        semanas.append(
            Semana(
                etiqueta=f"S{numero} {dia}-{fin}",
                desde=date(anio, mes, dia),
                hasta=date(anio, mes, fin),
                dias=fin - dia + 1,
            )
        )
        dia, numero = fin + 1, numero + 1
    return semanas


def _instantes(desde: date, hasta: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(desde, time.min, tzinfo=timezone.utc),
        datetime.combine(hasta, time.max, tzinfo=timezone.utc),
    )


def _dias(desde, hasta: date) -> int:
    if isinstance(desde, datetime):
        desde = desde.astimezone(timezone.utc).date() if desde.tzinfo else desde.date()
    return max((hasta - desde).days, 0)


# ------------------------------------------------------------------- canjes


def instantes_de_carga(db: Session, tipo: EntityType) -> set[datetime]:
    """Los `creado_en` que comparte más de un movimiento: una carga masiva.

    Dos movimientos con el mismo timestamp **al microsegundo** entraron en la
    misma transacción; esa coincidencia exacta no pasa por casualidad. Se usa para
    descartar las caídas cuya fecha la inventó un script (`D-085`).
    """
    return {
        instante
        for (instante,) in db.execute(
            select(Movimiento.creado_en)
            .where(Movimiento.entity_type == tipo)
            .group_by(Movimiento.creado_en)
            .having(func.count() > 1)
        ).all()
    }


def fecha_puesta_por_la_carga(fecha, creado_en, cargas: set[datetime]) -> bool:
    """Si la fecha de ese movimiento la estampó el proceso que lo cargó.

    Hacen falta las **dos** condiciones. La limpieza que canceló 215 canjes les
    puso la fecha del día en que corrió, y contarlas como caídas de ese día daba
    215 en una semana. Pero las 11 cancelaciones migradas del Excel traen fechas
    reales y sí pertenecen a su período. Lo que las distingue no es cómo entraron
    sino si la fecha es un dato o un subproducto: el script estampó «hoy»
    (`D-085`).

    Y tampoco alcanza con mirar la coincidencia de fechas: una cancelación que
    alguien registra hoy en la app también tiene fecha de hoy, y es una gestión
    real. Lo que la separa es que su `creado_en` no lo comparte nadie.
    """
    if creado_en is None or creado_en not in cargas:
        return False
    f = fecha.date() if isinstance(fecha, datetime) else fecha
    c = creado_en.date() if isinstance(creado_en, datetime) else creado_en
    return f == c


class Tramo(BaseModel):
    """Un pedazo de tiempo con nombre: una semana del mes o un mes entero.

    Existe para que el flujo se calcule **de una vez para toda la ventana**. La
    primera versión pedía los canjes una vez por semana y una vez por mes, y con
    tres meses comparados eran sesenta consultas contra Neon: el reporte tardaba
    24 segundos. Ahora cada señal se trae en una consulta sobre el rango completo y
    se reparte en Python (`D-098`).
    """

    clave: str
    desde: date
    hasta: date


def _reparto(tramos: list[Tramo]) -> dict[str, list]:
    return {tr.clave: [] for tr in tramos}


def _tramo_de(tramos: list[Tramo], cuando) -> str | None:
    """A qué tramo pertenece una fecha. `None` si cae fuera de todos.

    Los tramos no se solapan --las semanas de un mes, o los meses de la ventana--
    así que el primero que la contenga es el único.
    """
    if cuando is None:
        return None
    f = cuando.date() if isinstance(cuando, datetime) else cuando
    for tr in tramos:
        if tr.desde <= f <= tr.hasta:
            return tr.clave
    return None


def _extremos(tramos: list[Tramo]) -> tuple[date, date]:
    return min(tr.desde for tr in tramos), max(tr.hasta for tr in tramos)


def flujo_de_canjes_por_tramo(
    db: Session,
    tramos: list[Tramo],
    cargas: set[datetime],
    hoy: date,
    cache_uf: dict | None = None,
) -> dict[str, tuple[int, int, int, Decimal, Decimal, Decimal]]:
    """Por tramo: entraron, avanzaron, se cayeron, comisión, valor venta y arriendo.

    Cuatro consultas para toda la ventana, no cuatro por tramo. El valor y la
    comisión salen del mismo recorrido de los canjes que entraron, porque las tres
    cifras se calculan del mismo cálculo.
    """
    if not tramos:
        return {}
    desde, hasta = _extremos(tramos)
    inicio, fin = _instantes(desde, hasta)

    entraron = {tr.clave: 0 for tr in tramos}
    comision = {tr.clave: CERO for tr in tramos}
    venta = {tr.clave: CERO for tr in tramos}
    arriendo = {tr.clave: CERO for tr in tramos}
    for canje in db.scalars(
        select(Canje).where(Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin)
    ):
        clave = _tramo_de(tramos, canje.fecha_solicitud)
        if clave is None:
            continue
        entraron[clave] += 1
        uf = uf_del_canje(db, canje, hoy, cache_uf)
        calculo = (
            calcular(canje.tipo_operacion, canje.valor_prop, canje.moneda_valor, uf)
            if uf
            else None
        )
        if not calculo:
            continue
        comision[clave] += calculo.comision_dataprop
        if canje.tipo_operacion == OperacionTipo.ARRIENDO:
            arriendo[clave] += calculo.valor_clp
        else:
            venta[clave] += calculo.valor_clp

    # Avanzaron: canjes distintos por tramo. Se cuentan canjes y no movimientos --
    # dos avances del mismo canje en la semana son un canje que avanzó.
    avanzaron_ids: dict[str, set[int]] = {tr.clave: set() for tr in tramos}
    for canje_id, fecha in db.execute(
        select(Movimiento.entity_id, Movimiento.fecha).where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.etapa_resultante.is_not(None),
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
    ).all():
        clave = _tramo_de(tramos, fecha)
        if clave:
            avanzaron_ids[clave].add(canje_id)

    # Se cayeron: las dos fuentes de `D-086`, sin contar dos veces.
    cayeron_ids: dict[str, set[int]] = {tr.clave: set() for tr in tramos}
    for canje_id, fecha, creado_en in db.execute(
        select(Movimiento.entity_id, Movimiento.fecha, Movimiento.creado_en).where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.tipo_movimiento == "CANCELACION",
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
    ).all():
        if fecha_puesta_por_la_carga(fecha, creado_en, cargas):
            continue
        clave = _tramo_de(tramos, fecha)
        if clave:
            cayeron_ids[clave].add(canje_id)
    for canje_id, cierre in db.execute(
        select(Canje.id, Canje.fecha_cierre).where(
            Canje.estado == CanjeEstado.CANCELADO,
            Canje.fecha_cierre >= inicio,
            Canje.fecha_cierre <= fin,
        )
    ).all():
        clave = _tramo_de(tramos, cierre)
        if clave:
            cayeron_ids[clave].add(canje_id)

    return {
        tr.clave: (
            entraron[tr.clave],
            len(avanzaron_ids[tr.clave]),
            len(cayeron_ids[tr.clave]),
            comision[tr.clave],
            venta[tr.clave],
            arriendo[tr.clave],
        )
        for tr in tramos
    }


def flujo_de_negocios_por_tramo(
    db: Session, tramos: list[Tramo]
) -> dict[str, tuple[int, int, int, Decimal, Decimal, Decimal]]:
    """Lo mismo para negocios: entraron, avanzaron, se cayeron y la plata cerrada.

    **La plata va por fecha de cierre y las entradas por fecha de inicio**, y son
    dos ejes distintos a propósito: la comisión se gana al cerrar, y un negocio que
    entra todavía no generó nada.
    """
    if not tramos:
        return {}
    desde, hasta = _extremos(tramos)
    inicio, fin = _instantes(desde, hasta)

    entraron = {tr.clave: 0 for tr in tramos}
    for (fecha_inicio,) in db.execute(
        select(NegocioHito.fecha_inicio).where(
            NegocioHito.fecha_inicio >= desde, NegocioHito.fecha_inicio <= hasta
        )
    ).all():
        clave = _tramo_de(tramos, fecha_inicio)
        if clave:
            entraron[clave] += 1

    avanzaron_ids: dict[str, set[int]] = {tr.clave: set() for tr in tramos}
    for negocio_id, fecha in db.execute(
        select(Movimiento.entity_id, Movimiento.fecha).where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.etapa_resultante.is_not(None),
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
    ).all():
        clave = _tramo_de(tramos, fecha)
        if clave:
            avanzaron_ids[clave].add(negocio_id)

    cayeron = {tr.clave: 0 for tr in tramos}
    venta = {tr.clave: CERO for tr in tramos}
    arriendo = {tr.clave: CERO for tr in tramos}
    comision = {tr.clave: CERO for tr in tramos}
    base = func.coalesce(NegocioHito.valor_clp_manual, NegocioHito.valor_clp_calculado, 0)
    for estado, cierre, valor, real_vp, operacion in db.execute(
        select(
            NegocioHito.estado,
            NegocioHito.fecha_cierre,
            base,
            func.coalesce(NegocioHito.comision_real_vp, 0),
            Catalogo.codigo,
        )
        .select_from(NegocioHito)
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.tipo_operacion_id)
        .where(NegocioHito.fecha_cierre >= desde, NegocioHito.fecha_cierre <= hasta)
    ).all():
        clave = _tramo_de(tramos, cierre)
        if clave is None:
            continue
        if estado in CAIDA_NEGOCIO:
            cayeron[clave] += 1
            continue
        if estado != EstadoNegocio.CERRADO:
            continue
        comision[clave] += Decimal(real_vp)
        if operacion == "ARRIENDO":
            arriendo[clave] += Decimal(valor or 0)
        else:
            venta[clave] += Decimal(valor or 0)

    return {
        tr.clave: (
            entraron[tr.clave],
            len(avanzaron_ids[tr.clave]),
            cayeron[tr.clave],
            comision[tr.clave],
            venta[tr.clave],
            arriendo[tr.clave],
        )
        for tr in tramos
    }


def flujo_de_canjes(
    db: Session,
    desde: date,
    hasta: date,
    cargas: set[datetime],
    hoy: date,
    cache_uf: dict | None = None,
) -> tuple[int, int, int, Decimal]:
    """(entraron, avanzaron, se_cayeron, comisión de lo que entró) en el rango."""
    inicio, fin = _instantes(desde, hasta)

    entrantes = list(
        db.scalars(
            select(Canje).where(Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin)
        )
    )
    comision = CERO
    for canje in entrantes:
        uf = uf_del_canje(db, canje, hoy, cache_uf)
        calculo = (
            calcular(canje.tipo_operacion, canje.valor_prop, canje.moneda_valor, uf)
            if uf
            else None
        )
        if calculo:
            comision += calculo.comision_dataprop

    # Avanzaron: canjes distintos con al menos un movimiento que los dejó en una
    # etapa. Se cuentan canjes y no movimientos: dos avances del mismo canje en
    # la semana son un canje que avanzó, no dos.
    avanzaron = db.scalar(
        select(func.count(func.distinct(Movimiento.entity_id))).where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.etapa_resultante.is_not(None),
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
    )

    # Se cayeron: las dos fuentes de `D-086`, sumadas sin contar dos veces.
    con_movimiento = set()
    for canje_id, fecha, creado_en in db.execute(
        select(Movimiento.entity_id, Movimiento.fecha, Movimiento.creado_en).where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.tipo_movimiento == "CANCELACION",
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
    ).all():
        if not fecha_puesta_por_la_carga(fecha, creado_en, cargas):
            con_movimiento.add(canje_id)

    solo_fecha = db.scalars(
        select(Canje.id).where(
            Canje.estado == CanjeEstado.CANCELADO,
            Canje.fecha_cierre >= inicio,
            Canje.fecha_cierre <= fin,
        )
    ).all()
    se_cayeron = len(con_movimiento | set(solo_fecha))

    return len(entrantes), avanzaron or 0, se_cayeron, comision


def embudo_de_canjes(db: Session, desde: date, hasta: date) -> dict[str, int]:
    """Cuántos canjes distintos entraron a cada etapa en el rango."""
    inicio, fin = _instantes(desde, hasta)
    filas = db.execute(
        select(Movimiento.etapa_resultante, func.count(func.distinct(Movimiento.entity_id)))
        .where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.etapa_resultante.is_not(None),
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
        .group_by(Movimiento.etapa_resultante)
    ).all()
    return {etapa: n for etapa, n in filas}


def abiertos_de_canjes(
    db: Session, hoy: date, cache_uf: dict | None = None
) -> list[EtapaAbierta]:
    """Dónde están los canjes abiertos, cuánta comisión hay ahí y cuánto llevan.

    Abierto es activo y con etapa distinta de cerrada, igual que en la bandeja: los
    que arrastran el desalineamiento del dato de Dataprop no son trabajo pendiente.

    El reloj arranca en el movimiento más reciente que dejó al canje **en la etapa
    que tiene hoy**, no en el último cambio cualquiera: si pasó a «En oferta» y
    después volvió, importa la última entrada.
    """
    abiertos = list(
        db.scalars(
            select(Canje).where(
                Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO
            )
        )
    )
    if not abiertos:
        return []

    entradas: dict[tuple[int, str], datetime] = {}
    for canje_id, etapa, fecha in db.execute(
        select(Movimiento.entity_id, Movimiento.etapa_resultante, Movimiento.fecha)
        .where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.entity_id.in_([c.id for c in abiertos]),
            Movimiento.etapa_resultante.is_not(None),
        )
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all():
        entradas[(canje_id, etapa)] = fecha

    por_etapa: dict[str, list[tuple[int, bool, Decimal]]] = {}
    for canje in abiertos:
        etapa = canje.etapa.value if canje.etapa else "SIN_ETAPA"
        entrada = entradas.get((canje.id, etapa))
        uf = uf_del_canje(db, canje, hoy, cache_uf)
        calculo = (
            calcular(canje.tipo_operacion, canje.valor_prop, canje.moneda_valor, uf)
            if uf
            else None
        )
        por_etapa.setdefault(etapa, []).append(
            (
                _dias(entrada or canje.fecha_solicitud, hoy),
                entrada is None,
                calculo.comision_dataprop if calculo else CERO,
            )
        )

    orden = {e.value: i for i, e in enumerate(CanjeEtapa)}
    return sorted(_armar(por_etapa), key=lambda e: orden.get(e.etapa, len(orden)))


def _armar(por_etapa: dict[str, list[tuple[int, bool, Decimal]]]) -> list[EtapaAbierta]:
    salida = []
    for etapa, items in por_etapa.items():
        dias = [d for d, _, _ in items]
        salida.append(
            EtapaAbierta(
                etapa=etapa,
                casos=len(items),
                comision=sum((c for _, _, c in items), CERO),
                dias_promedio=round(sum(dias) / len(dias)),
                dias_min=min(dias),
                dias_max=max(dias),
                sin_historia=sum(1 for _, estimado, _ in items if estimado),
            )
        )
    return salida


def plata_de_canjes(
    db: Session, desde: date, hasta: date, hoy: date, cache_uf: dict | None = None
) -> tuple[Decimal, Decimal]:
    """(valor de las ventas, valor de los arriendos) de los canjes del rango.

    **Separados y nunca sumados**: un precio de venta y un mes de renta no son la
    misma unidad, que es la razón por la que el reporte mensual parte los montos de
    negocios en dos (`D-054`).
    """
    inicio, fin = _instantes(desde, hasta)
    venta = arriendo = CERO
    for canje in db.scalars(
        select(Canje).where(Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin)
    ):
        uf = uf_del_canje(db, canje, hoy, cache_uf)
        calculo = (
            calcular(canje.tipo_operacion, canje.valor_prop, canje.moneda_valor, uf)
            if uf
            else None
        )
        if not calculo:
            continue
        if canje.tipo_operacion == OperacionTipo.ARRIENDO:
            arriendo += calculo.valor_clp
        else:
            venta += calculo.valor_clp
    return venta, arriendo


# ----------------------------------------------------------------- negocios


def flujo_de_negocios(db: Session, desde: date, hasta: date) -> tuple[int, int, int]:
    """(entraron, avanzaron, se_cayeron) en el rango.

    **`se_cayeron` es siempre cero y no es un error del cálculo**: las 10
    liquidaciones perdidas no tienen fecha de cierre, así que no se puede saber
    cuándo se cayeron. La pantalla lo dice en vez de dibujar ceros.

    `avanzaron` es cero por la misma clase de razón: el pipeline de negocios no
    tiene ni un movimiento registrado.
    """
    entraron = db.scalar(
        select(func.count()).select_from(NegocioHito).where(
            NegocioHito.fecha_inicio >= desde, NegocioHito.fecha_inicio <= hasta
        )
    )
    inicio, fin = _instantes(desde, hasta)
    avanzaron = db.scalar(
        select(func.count(func.distinct(Movimiento.entity_id))).where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.etapa_resultante.is_not(None),
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
    )
    se_cayeron = db.scalar(
        select(func.count()).select_from(NegocioHito).where(
            NegocioHito.estado.in_(CAIDA_NEGOCIO),
            NegocioHito.fecha_cierre >= desde,
            NegocioHito.fecha_cierre <= hasta,
        )
    )
    return entraron or 0, avanzaron or 0, se_cayeron or 0


def embudo_de_negocios(db: Session, desde: date, hasta: date) -> dict[str, int]:
    inicio, fin = _instantes(desde, hasta)
    filas = db.execute(
        select(Movimiento.etapa_resultante, func.count(func.distinct(Movimiento.entity_id)))
        .where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.etapa_resultante.is_not(None),
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
        .group_by(Movimiento.etapa_resultante)
    ).all()
    return {etapa: n for etapa, n in filas}


def abiertos_de_negocios(db: Session, hoy: date) -> list[EtapaAbierta]:
    """Los negocios con liquidación abierta, con su comisión real VP en juego.

    La comisión sale de la liquidación abierta, que es la plata que está en juego
    en esa etapa. El reloj se cuenta desde el inicio de la liquidación porque no
    hay movimientos de pipeline que digan cuándo entró a su etapa; eso se informa
    en `sin_historia`.
    """
    filas = db.execute(
        select(
            Negocio.id,
            Negocio.etapa,
            func.min(NegocioHito.fecha_inicio),
            func.coalesce(func.sum(NegocioHito.comision_real_vp), 0),
        )
        .join(NegocioHito, NegocioHito.negocio_id == Negocio.id)
        .where(NegocioHito.estado == EstadoNegocio.ACTIVO)
        .group_by(Negocio.id, Negocio.etapa)
    ).all()
    if not filas:
        return []

    por_etapa: dict[str, list[tuple[int, bool, Decimal]]] = {}
    for _negocio_id, etapa, inicio, comision in filas:
        if inicio is None:
            continue
        por_etapa.setdefault(etapa or "SIN_ETAPA", []).append(
            (_dias(inicio, hoy), True, Decimal(comision))
        )
    return sorted(_armar(por_etapa), key=lambda e: e.etapa)


def plata_de_negocios(db: Session, desde: date, hasta: date) -> tuple[Decimal, Decimal, Decimal]:
    """(valor venta, valor arriendo, comisión real VP) de lo **cerrado** en el rango.

    Va por fecha de cierre y no de inicio: la comisión se gana al cerrar. Y el
    valor se parte por operación porque venta y arriendo no comparten unidad
    (`D-054`).
    """
    base = func.coalesce(NegocioHito.valor_clp_manual, NegocioHito.valor_clp_calculado, 0)
    es_arriendo = Catalogo.codigo == "ARRIENDO"
    fila = db.execute(
        select(
            func.coalesce(func.sum(func.coalesce(base, 0)).filter(~es_arriendo), 0),
            func.coalesce(func.sum(func.coalesce(base, 0)).filter(es_arriendo), 0),
            func.coalesce(func.sum(NegocioHito.comision_real_vp), 0),
        )
        .select_from(NegocioHito)
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.tipo_operacion_id)
        .where(
            NegocioHito.estado == EstadoNegocio.CERRADO,
            NegocioHito.fecha_cierre >= desde,
            NegocioHito.fecha_cierre <= hasta,
        )
    ).one()
    return Decimal(fila[0]), Decimal(fila[1]), Decimal(fila[2])
