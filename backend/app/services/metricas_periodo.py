"""Las métricas nuevas del reporte por período: etapas, plata de canjes y duraciones.

Viven acá y no en `reporte_mensual.py` porque ese módulo ya tiene 950 líneas de
maquinaria de ventanas, series, promedios y tendencias. Esto es otra cosa: son
consultas sobre un rango de fechas, sin nada de ventana. `reporte_mensual` las
llama y las mete en la serie.

**Tres grupos, y cada uno responde una pregunta distinta.**

| Grupo | Pregunta | Eje |
|---|---|---|
| Etapas y estados | de lo que entró en el período, cómo está | rango + foto de hoy |
| Plata de canjes | cuánto valen y cuánto comisionan | rango |
| Duraciones | cuánto llevan los abiertos donde están | foto de hoy |

**Las etapas se cuentan con la foto de hoy, no con la del cierre del período.**
De los canjes solicitados en junio, cuántos están hoy en cada etapa. La otra
pregunta --en qué etapa estaban al 30 de junio-- pide reconstruir el pasado
movimiento por movimiento, y el dato para hacerlo existe solo desde que el
pipeline se usa en la app. Cuando haya historia se puede agregar; hoy sería una
serie inventada.

**Las duraciones son una foto y no una serie.** «Cuántos días llevan los canjes
abiertos en la etapa en que están» no tiene versión mensual: los abiertos son los
de hoy. Por eso este bloque no entra en la serie del reporte y va aparte, con el
**n a la vista**: con siete canjes en cuatro etapas, un promedio es de uno o dos
casos y sin el n se lee como una tendencia.
"""
from datetime import date, datetime, time, timezone
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, OperacionTipo
from app.models.catalogo import EstadoNegocio
from app.models.movimiento import EntityType, Movimiento
from app.models.negocio import Negocio, NegocioHito
from app.services.comisiones_canjes import calcular
from app.services.plata_canjes import uf_del_canje

CERO = Decimal("0")


class PlataDeCanjes(BaseModel):
    """El valor de las propiedades y la comisión de Dataprop, de un rango.

    **Venta y arriendo van separados y no se suman nunca.** En una venta el valor
    es el precio de la propiedad --cientos de millones-- y en un arriendo es un mes
    de renta. Sumarlos da un número sin significado, que es la misma razón por la
    que el reporte mensual parte los montos de negocios en dos (`D-054`).

    **La comisión sí se suma**, porque las dos son pesos de comisión: la regla de
    Dataprop es 6/5/4% del corretaje en venta según el tramo en UF y 8% en
    arriendo, y el resultado es plata comparable.

    `sin_valorizar` es de cuántos canjes no se pudo calcular: les falta el valor,
    la moneda, el tipo de operación, o la UF de su fecha. Contarlos como cero
    bajaría los totales con datos que no existen, así que se informan aparte.
    """

    canjes: int
    valor_venta: Decimal = CERO
    valor_arriendo: Decimal = CERO
    comision_dataprop: Decimal = CERO
    sin_valorizar: int = 0


class ConteoEtapa(BaseModel):
    """Cuántas entidades hay en una etapa. El código lo rotula la pantalla, que ya
    tiene los nombres de las dos escalas."""

    etapa: str | None
    cantidad: int


class DuracionEtapa(BaseModel):
    """Cuánto llevan en su etapa los que están abiertos.

    `n` va siempre y la pantalla lo muestra: con siete canjes repartidos en cuatro
    etapas, el promedio de una etapa puede ser un solo caso.

    `sin_historia` son los que no tienen ningún movimiento que registre la entrada
    a la etapa. Ahí se mide desde la solicitud --es lo que se sabe-- y se dice
    cuántos son, porque no es lo mismo que haberlo medido de verdad.
    """

    etapa: str | None
    n: int
    dias_promedio: int
    dias_min: int
    dias_max: int
    sin_historia: int


def _instantes(desde: date, hasta: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(desde, time.min, tzinfo=timezone.utc),
        datetime.combine(hasta, time.max, tzinfo=timezone.utc),
    )


# --------------------------------------------------------------- plata de canjes


def plata_de_canjes(
    db: Session,
    desde: date,
    hasta: date,
    hoy: date | None = None,
    cache_uf: dict | None = None,
) -> PlataDeCanjes:
    """Valor por tipo de operación y comisión de Dataprop de los canjes del rango.

    Se cuenta por **fecha de solicitud**, el mismo eje que usan los conteos del
    reporte: «de los que entraron en junio, cuánto valían y cuánto comisionan».

    La UF de cada canje sale de `uf_del_canje`, que es la política única del
    proyecto --la del cierre para un cerrado, la de hoy para uno abierto, la de la
    solicitud para un cancelado-- y no la de hoy para todos. Duplicar esa política
    ya dejó pasar un error una vez (`D-095`).
    """
    inicio, fin = _instantes(desde, hasta)
    hoy = hoy or datetime.now(timezone.utc).date()

    canjes = list(
        db.scalars(
            select(Canje).where(Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin)
        )
    )
    salida = PlataDeCanjes(canjes=len(canjes))
    for canje in canjes:
        uf = uf_del_canje(db, canje, hoy, cache_uf)
        calculo = calcular(canje.tipo_operacion, canje.valor_prop, canje.moneda_valor, uf) if uf else None
        if calculo is None:
            salida.sin_valorizar += 1
            continue
        if canje.tipo_operacion == OperacionTipo.ARRIENDO:
            salida.valor_arriendo += calculo.valor_clp
        else:
            salida.valor_venta += calculo.valor_clp
        salida.comision_dataprop += calculo.comision_dataprop
    return salida


def plata_de_canjes_por_clave(
    db: Session,
    desde: date,
    hasta: date,
    clave_de,
    hoy: date | None = None,
    cache_uf: dict | None = None,
) -> dict[str, PlataDeCanjes]:
    """La plata de canjes de un rango, repartida en los tramos que diga `clave_de`.

    **Una sola consulta para toda la serie.** La alternativa era llamar
    `plata_de_canjes` una vez por tramo, y con una ventana de doce meses eso son
    doce consultas de canjes por cada serie --y el reporte arma dos, la de la
    ventana y la de comparación--. Acá los canjes del rango se traen una vez y se
    reparten en Python.

    `clave_de` recibe la fecha de solicitud y devuelve el tramo: el mes `'2026-08'`
    o la semana del mes. Es la misma función que usa el resto de la serie, así que
    los tramos coinciden por construcción y no por coincidencia.
    """
    inicio, fin = _instantes(desde, hasta)
    hoy = hoy or datetime.now(timezone.utc).date()

    salida: dict[str, PlataDeCanjes] = {}
    canjes = db.scalars(
        select(Canje).where(Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin)
    )
    for canje in canjes:
        tramo = salida.setdefault(clave_de(canje.fecha_solicitud), PlataDeCanjes(canjes=0))
        tramo.canjes += 1
        uf = uf_del_canje(db, canje, hoy, cache_uf)
        calculo = (
            calcular(canje.tipo_operacion, canje.valor_prop, canje.moneda_valor, uf)
            if uf
            else None
        )
        if calculo is None:
            tramo.sin_valorizar += 1
            continue
        if canje.tipo_operacion == OperacionTipo.ARRIENDO:
            tramo.valor_arriendo += calculo.valor_clp
        else:
            tramo.valor_venta += calculo.valor_clp
        tramo.comision_dataprop += calculo.comision_dataprop
    return salida


# ------------------------------------------------------------ etapas y estados


def canjes_por_etapa(db: Session, desde: date, hasta: date) -> list[ConteoEtapa]:
    """Los canjes solicitados en el rango, por la etapa en que están hoy."""
    inicio, fin = _instantes(desde, hasta)
    filas = db.execute(
        select(Canje.etapa, func.count())
        .where(Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin)
        .group_by(Canje.etapa)
    ).all()
    orden = {e: i for i, e in enumerate(CanjeEtapa)}
    return [
        ConteoEtapa(etapa=etapa.value if etapa else None, cantidad=n)
        for etapa, n in sorted(filas, key=lambda f: orden.get(f[0], len(orden)))
    ]


def negocios_por_etapa(db: Session, desde: date, hasta: date) -> list[ConteoEtapa]:
    """Los negocios iniciados en el rango, por la etapa en que están hoy.

    Un negocio se cuenta una vez, por su liquidación más antigua: `VVP-3` tiene
    promesa y escritura en meses distintos y es un negocio, no dos. Es el mismo
    criterio que usa `negocios_iniciados` en el reporte.
    """
    primeros = (
        select(
            NegocioHito.negocio_id.label("negocio_id"),
            func.min(NegocioHito.fecha_inicio).label("inicio"),
        )
        .group_by(NegocioHito.negocio_id)
        .subquery()
    )
    filas = db.execute(
        select(Negocio.etapa, func.count())
        .select_from(primeros)
        .join(Negocio, Negocio.id == primeros.c.negocio_id)
        .where(primeros.c.inicio >= desde, primeros.c.inicio <= hasta)
        .group_by(Negocio.etapa)
    ).all()
    return [
        ConteoEtapa(etapa=etapa, cantidad=n)
        for etapa, n in sorted(filas, key=lambda f: f[0] or "")
    ]


def hitos_por_estado(db: Session, desde: date, hasta: date) -> list[ConteoEtapa]:
    """Las liquidaciones iniciadas en el rango, por su estado.

    Van por liquidación y no por negocio porque el estado vive en la liquidación:
    un negocio con la promesa cerrada y la escritura activa está en los dos
    estados a la vez, y forzarlo a uno sería elegir por él.
    """
    filas = db.execute(
        select(NegocioHito.estado, func.count())
        .where(NegocioHito.fecha_inicio >= desde, NegocioHito.fecha_inicio <= hasta)
        .group_by(NegocioHito.estado)
    ).all()
    orden = {e: i for i, e in enumerate(EstadoNegocio)}
    return [
        ConteoEtapa(etapa=estado.value if estado else None, cantidad=n)
        for estado, n in sorted(filas, key=lambda f: orden.get(f[0], len(orden)))
    ]


# ------------------------------------------------------------------ duraciones


def _dias(desde, hasta: date) -> int:
    if isinstance(desde, datetime):
        desde = desde.astimezone(timezone.utc).date() if desde.tzinfo else desde.date()
    return max((hasta - desde).days, 0)


def _agrupar(medidas: dict[str | None, list[tuple[int, bool]]]) -> list[DuracionEtapa]:
    salida = []
    for etapa, items in medidas.items():
        dias = [d for d, _ in items]
        salida.append(
            DuracionEtapa(
                etapa=etapa,
                n=len(dias),
                dias_promedio=round(sum(dias) / len(dias)),
                dias_min=min(dias),
                dias_max=max(dias),
                sin_historia=sum(1 for _, estimado in items if estimado),
            )
        )
    return salida


def duracion_de_canjes_por_etapa(
    db: Session, hoy: date | None = None
) -> list[DuracionEtapa]:
    """Cuántos días llevan los canjes **abiertos** en la etapa en que están.

    Abierto es lo mismo que en la bandeja: activo y con etapa distinta de cerrada,
    para no contar como pendientes los que arrastran el desalineamiento del dato de
    Dataprop.

    El reloj arranca en el movimiento más reciente que **dejó al canje en su etapa
    actual**, no en el último cambio de etapa cualquiera: si un canje pasó a «En
    oferta» y después volvió, lo que importa es cuándo entró la última vez. Sin
    movimiento que lo diga se mide desde la solicitud y se cuenta en
    `sin_historia`.
    """
    hoy = hoy or datetime.now(timezone.utc).date()
    abiertos = list(
        db.scalars(
            select(Canje).where(
                Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO
            )
        )
    )
    if not abiertos:
        return []

    # El último movimiento que dejó a cada canje en la etapa que tiene hoy.
    entradas: dict[int, datetime] = {}
    for canje_id, etapa, fecha in db.execute(
        select(Movimiento.entity_id, Movimiento.etapa_resultante, Movimiento.fecha)
        .where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.entity_id.in_([c.id for c in abiertos]),
            Movimiento.etapa_resultante.is_not(None),
        )
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all():
        # Ascendente: la última asignación de cada canje es la más nueva, y se
        # guarda solo si coincide con su etapa actual.
        entradas[(canje_id, etapa)] = fecha

    medidas: dict[str | None, list[tuple[int, bool]]] = {}
    for canje in abiertos:
        entrada = entradas.get((canje.id, canje.etapa.value if canje.etapa else None))
        referencia = entrada or canje.fecha_solicitud
        medidas.setdefault(canje.etapa.value if canje.etapa else None, []).append(
            (_dias(referencia, hoy), entrada is None)
        )
    orden = {e.value: i for i, e in enumerate(CanjeEtapa)}
    return sorted(_agrupar(medidas), key=lambda d: orden.get(d.etapa, len(orden)))


def duracion_de_negocios_por_etapa(
    db: Session, hoy: date | None = None
) -> list[DuracionEtapa]:
    """Lo mismo para los negocios con liquidación abierta.

    **Hoy devuelve la lista vacía o todo estimado**, y es un dato del estado del
    proyecto y no un error: el pipeline de negocios no tiene ni un movimiento
    registrado, así que no existe historia de cuándo entró cada negocio a su etapa.
    Se mide desde el inicio de la liquidación y se dice en `sin_historia`. La
    pantalla lo explica en vez de esconder el panel.
    """
    hoy = hoy or datetime.now(timezone.utc).date()
    filas = db.execute(
        select(Negocio.id, Negocio.etapa, func.min(NegocioHito.fecha_inicio))
        .join(NegocioHito, NegocioHito.negocio_id == Negocio.id)
        .where(NegocioHito.estado == EstadoNegocio.ACTIVO)
        .group_by(Negocio.id, Negocio.etapa)
    ).all()
    if not filas:
        return []

    entradas: dict[tuple[int, str | None], datetime] = {}
    for negocio_id, etapa, fecha in db.execute(
        select(Movimiento.entity_id, Movimiento.etapa_resultante, Movimiento.fecha)
        .where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.entity_id.in_([f[0] for f in filas]),
            Movimiento.etapa_resultante.is_not(None),
        )
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all():
        entradas[(negocio_id, etapa)] = fecha

    medidas: dict[str | None, list[tuple[int, bool]]] = {}
    for negocio_id, etapa, inicio in filas:
        entrada = entradas.get((negocio_id, etapa))
        referencia = entrada or inicio
        if referencia is None:
            continue
        medidas.setdefault(etapa, []).append((_dias(referencia, hoy), entrada is None))
    return sorted(_agrupar(medidas), key=lambda d: d.etapa or "")
