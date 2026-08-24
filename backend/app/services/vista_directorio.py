"""Vista directorio: lo que se lleva a la reunión.

**Se armó con supuestos, no con un requerimiento.** Se preguntó cinco veces qué
quiere ver el directorio y no llegó la respuesta, así que esto es una primera
versión concreta para corregir, no una adivinanza presentada como certeza. Los
supuestos están acá arriba para que se puedan discutir uno por uno:

1. **Cuánto entró**, en año corrido y en los últimos 12 meses. No el mes: los
   procesos duran de un mes a varios y un mes suelto no dice nada (`D-043`).
2. **De dónde vino**: mezcla por modelo de negocio y por alianza.
3. **Qué hay por delante**: el pipeline abierto y cuánta plata representa.
4. **Qué se perdió y cuánto valía**, con la tasa de conversión.
5. **Una proyección, como rango.**

**La proyección va como rango y con el `n` a la vista, no como número.** La tasa
de conversión es 7 de 17, o sea 41%, pero con ese tamaño de muestra el intervalo
de confianza al 95% va de 18% a 65%. Multiplicar el pipeline por "41%" es en
realidad multiplicarlo por "algo entre un quinto y dos tercios". Un directorio
decide plata con esto: darle una cifra puntual sobre 17 casos sería darle falsa
precisión, y es peor que darle un rango honesto.

**Lo que no se puede proyectar, y se dice:** *cuándo* van a cerrar los negocios
abiertos. Eso necesita duración de ciclo y conversión por etapa, y hoy no existe
ni un dato -- los históricos traen la misma fecha de inicio y de cierre porque el
Excel tenía una sola, y no hay ni un movimiento de negocio registrado. Se informa
la carencia en vez de rellenarla con una estimación.

**No hay un total que sume los tres buckets** (`D-006`). Ganado, pipeline y
potencial perdido son plata, pero no la misma plata.
"""
import math
from datetime import date, datetime, timezone
from decimal import Decimal
from statistics import median

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import Catalogo, EstadoNegocio
from app.models.negocio import Negocio, NegocioHito
from app.services.reporte_mensual import (
    DOMINIOS,
    METRICAS,
    VENTANA_DEFECTO,
    VENTANA_HISTORICO,
    VENTANAS_VALIDAS,
    MetricasMes,
    PromedioMes,
    Tendencia,
    _inicio_por_dominio,
    _meses_entre,
    _metricas,
    _primer_mes_con_datos,
    _promedio,
    _serie_mensual,
    _tendencia,
    rango_anio_corrido,
    rango_ventana,
)

CERO = Decimal("0")

# Nivel de confianza del intervalo de la tasa de conversión. 1,96 es el z de 95%,
# que es la convención en reportería de negocio.
Z_95 = 1.96

# Cuántas categorías se listan en cada desglose de canjes. Nueve comunas ya
# ocupan media pantalla y la cola larga no informa: lo que importa es dónde está
# el volumen, no el listado completo.
TOPE_DESGLOSE = 8


class Monto(BaseModel):
    etiqueta: str
    valor: Decimal


class Bucket(BaseModel):
    hitos: int
    negocios: int
    comision_real_vp: Decimal


class Conversion(BaseModel):
    """La tasa de cierre y su margen de error real.

    `n` va a la vista a propósito: una tasa de 41% sobre 17 casos y otra sobre
    1.700 se leen igual y no valen lo mismo.
    """

    cerrados: int
    perdidos: int
    n: int
    tasa_pct: Decimal
    intervalo_bajo_pct: Decimal
    intervalo_alto_pct: Decimal


class Ticket(BaseModel):
    mediano: Decimal
    minimo: Decimal
    maximo: Decimal
    n: int


class Proyeccion(BaseModel):
    """El pipeline ponderado por la tasa de conversión, como rango.

    Los tres escenarios salen del intervalo de confianza, no de un criterio
    optimista o pesimista inventado: son el mismo dato con su margen de error.
    """

    pipeline: Decimal
    pesimista: Decimal
    esperado: Decimal
    optimista: Decimal
    # Lo que la proyección **no** puede decir, para que no se lo pregunten.
    sin_dato_de_plazo: bool
    nota: str


class Conteo(BaseModel):
    """Un desglose por categoría, en unidades. El equivalente de `Monto` cuando
    lo que se cuenta no es plata."""

    etiqueta: str
    cantidad: int


class CanjesDirectorio(BaseModel):
    """La mitad de canjes de la vista, que es de volumen y no de plata.

    **No tiene ticket ni proyección, y no es un olvido.** Canjes sí genera
    comisión --la de administración de Dataprop-- pero se calcula sobre la
    comisión de los corredores participantes, que está sin cargar en las 297
    filas; y `valor_prop` no sirve de reemplazo porque su moneda está equivocada
    en ~138 de ellas (`D-054`). Sin plata no hay ticket mediano ni pipeline
    ponderado que valga.

    Lo que sí se puede decir de un programa de intercambio es cuánto volumen
    entra, de dónde viene y cuánto sobrevive.
    """

    # Del período elegido: son conteos de un rango, así que la ventana los manda.
    solicitados: int
    activos: int
    cancelados: int
    # Los totales de toda la historia, para que el número de la ventana tenga
    # contra qué leerse.
    solicitados_historicos: int
    activos_historicos: int
    # La tasa de cierre va sobre la historia completa y sobre los **resueltos**,
    # igual que en negocios: los que siguen abiertos no cuentan a favor ni en
    # contra porque todavía no terminaron.
    cerrados_historicos: int
    resueltos_historicos: int
    tasa_cierre_pct: Decimal

    por_operacion: list[Conteo]
    por_tipo_inmueble: list[Conteo]
    por_comuna: list[Conteo]


class VistaDirectorio(BaseModel):
    generado: date
    # La ventana elegida. Manda sobre lo que es temporal --la ventana móvil, la
    # serie y la tendencia-- y no sobre los buckets, la tasa de cierre, el ticket
    # ni la proyección: un negocio abierto está abierto, no pertenece a un mes, y
    # una tasa sobre uno o dos casos resueltos no es una tasa.
    ventana_meses: int
    anio_corrido: MetricasMes
    anio_corrido_anterior: MetricasMes
    ventana_movil: MetricasMes

    ganado: Bucket
    pipeline: Bucket
    potencial_perdido: Bucket

    por_modelo: list[Monto]
    por_alianza: list[Monto]

    conversion: Conversion
    ticket: Ticket | None
    proyeccion: Proyeccion

    # Mes por mes de la ventana, con su promedio y su tendencia. Es lo mismo que
    # el reporte mensual: se reusan sus funciones en vez de recalcular acá.
    serie: list[MetricasMes]
    # `true` con la ventana histórica: la pantalla la rotula así y esconde la
    # comparación contra la ventana anterior, que no existe.
    es_historico: bool
    inicio_por_dominio: dict[str, str | None]
    promedio: PromedioMes
    tendencias: dict[str, Tendencia]

    canjes: CanjesDirectorio


def _bucket(db: Session, estados: tuple[EstadoNegocio, ...]) -> Bucket:
    fila = db.execute(
        select(
            func.count(NegocioHito.id),
            func.count(func.distinct(NegocioHito.negocio_id)),
            func.coalesce(func.sum(NegocioHito.comision_real_vp), 0),
        ).where(NegocioHito.estado.in_(estados))
    ).one()
    return Bucket(hitos=fila[0], negocios=fila[1], comision_real_vp=fila[2])


def _montos_por_modelo(db: Session) -> list[Monto]:
    """Lo ganado por modelo de negocio. Solo lo cerrado: es la plata que entró."""
    filas = db.execute(
        select(Negocio.modelo, func.coalesce(func.sum(NegocioHito.comision_real_vp), 0))
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .where(NegocioHito.estado == EstadoNegocio.CERRADO)
        .group_by(Negocio.modelo)
        .order_by(func.sum(NegocioHito.comision_real_vp).desc())
    ).all()
    return [
        Monto(etiqueta=(e.value if hasattr(e, "value") else (e or "Sin dato")), valor=v)
        for e, v in filas
    ]


def _montos_por_alianza(db: Session) -> list[Monto]:
    """Igual, por alianza, con el **nombre** y no el id.

    Un directorio no lee `alianza_id = 3`, así que se resuelve el nombre acá en
    vez de dejar que la pantalla lo cruce.
    """
    filas = db.execute(
        select(Catalogo.nombre, func.coalesce(func.sum(NegocioHito.comision_real_vp), 0))
        .select_from(NegocioHito)
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.alianza_id)
        .where(NegocioHito.estado == EstadoNegocio.CERRADO)
        .group_by(Catalogo.nombre)
        .order_by(func.sum(NegocioHito.comision_real_vp).desc())
    ).all()
    return [Monto(etiqueta=nombre or "Sin alianza", valor=v) for nombre, v in filas]


def _conversion(db: Session) -> Conversion:
    cerrados = db.scalar(
        select(func.count()).select_from(NegocioHito)
        .where(NegocioHito.estado == EstadoNegocio.CERRADO)
    ) or 0
    perdidos = db.scalar(
        select(func.count()).select_from(NegocioHito)
        .where(NegocioHito.estado.in_((EstadoNegocio.PERDIDO, EstadoNegocio.DESISTIDO)))
    ) or 0

    n = cerrados + perdidos
    if n == 0:
        return Conversion(
            cerrados=0, perdidos=0, n=0,
            tasa_pct=CERO, intervalo_bajo_pct=CERO, intervalo_alto_pct=CERO,
        )

    p = cerrados / n
    # Intervalo normal sobre una proporcion. Con n chico es ancho, y eso es
    # justamente lo que hay que mostrar en vez de esconder.
    error = Z_95 * math.sqrt(p * (1 - p) / n)
    return Conversion(
        cerrados=cerrados,
        perdidos=perdidos,
        n=n,
        tasa_pct=Decimal(p * 100).quantize(Decimal("0.1")),
        intervalo_bajo_pct=Decimal(max(0.0, p - error) * 100).quantize(Decimal("0.1")),
        intervalo_alto_pct=Decimal(min(1.0, p + error) * 100).quantize(Decimal("0.1")),
    )


def _ticket(db: Session) -> Ticket | None:
    valores = [
        Decimal(v or 0)
        for v in db.execute(
            select(NegocioHito.comision_real_vp)
            .where(NegocioHito.estado == EstadoNegocio.CERRADO)
        ).scalars()
    ]
    if not valores:
        return None
    return Ticket(
        mediano=median(valores), minimo=min(valores), maximo=max(valores), n=len(valores)
    )


def _hay_dato_de_plazo(db: Session) -> bool:
    """Si se puede saber cuánto tardan los negocios en cerrar.

    Hacen falta dos cosas y hoy no está ninguna: hitos cerrados con fecha de
    inicio distinta de la de cierre, y movimientos que registren el paso por las
    etapas.
    """
    con_duracion = db.scalar(
        select(func.count()).select_from(NegocioHito).where(
            NegocioHito.estado == EstadoNegocio.CERRADO,
            NegocioHito.fecha_cierre.is_not(None),
            NegocioHito.fecha_cierre != NegocioHito.fecha_inicio,
        )
    ) or 0
    return con_duracion >= 3


def _proyeccion(db: Session, pipeline: Bucket, conversion: Conversion) -> Proyeccion:
    base = pipeline.comision_real_vp
    cien = Decimal("100")

    if conversion.n == 0:
        nota = (
            "Todavía no hay negocios resueltos, así que no hay tasa de conversión "
            "con la que ponderar el pipeline."
        )
    elif not _hay_dato_de_plazo(db):
        nota = (
            f"El rango sale de la tasa de conversión ({conversion.tasa_pct}% sobre "
            f"{conversion.n} negocios resueltos) y su margen de error. **No dice "
            "cuándo** va a entrar: eso necesita duración de ciclo y conversión por "
            "etapa, y hoy no hay ni un dato — los históricos traen la misma fecha "
            "de inicio y de cierre, y no hay movimientos de negocio registrados."
        )
    else:
        nota = (
            f"El rango sale de la tasa de conversión ({conversion.tasa_pct}% sobre "
            f"{conversion.n} negocios resueltos) y su margen de error."
        )

    return Proyeccion(
        pipeline=base,
        pesimista=(base * conversion.intervalo_bajo_pct / cien).quantize(Decimal("1")),
        esperado=(base * conversion.tasa_pct / cien).quantize(Decimal("1")),
        optimista=(base * conversion.intervalo_alto_pct / cien).quantize(Decimal("1")),
        sin_dato_de_plazo=not _hay_dato_de_plazo(db),
        nota=nota,
    )


def _conteos(db: Session, columna, tope: int | None = None) -> list[Conteo]:
    """Cuántos canjes hay por cada valor de una columna, de mayor a menor.

    Se salta los nulos en vez de agruparlos en "Sin dato": en un desglose de
    origen, una categoría "Sin dato" grande empuja hacia abajo a las reales y no
    dice de dónde vino nada.
    """
    filas = db.execute(
        select(columna, func.count())
        .where(columna.is_not(None))
        .group_by(columna)
        .order_by(func.count().desc())
    ).all()
    conteos = [
        Conteo(etiqueta=str(v.value if hasattr(v, "value") else v), cantidad=n)
        for v, n in filas
    ]
    return conteos[:tope] if tope else conteos


def _canjes(db: Session, desde: date, hasta: date) -> CanjesDirectorio:
    """La mitad de canjes: volumen del período, de dónde viene, y cuánto sobrevive.

    **Los conteos del período van por fecha de solicitud**, los tres, para que
    sumen entre sí: `solicitados = activos + cancelados`. Es la misma regla que el
    reporte mensual, y la que permite dibujarlos apilados (`D-055`).

    **La tasa de cierre va sobre la historia completa y sobre los resueltos.**
    Igual que en negocios: los que siguen abiertos no cuentan ni a favor ni en
    contra porque todavía no terminaron. Hoy da cero, y es cierto -- ningún canje
    se ha cerrado con éxito (`D-054`).
    """
    inicio = datetime.combine(desde, datetime.min.time(), tzinfo=timezone.utc)
    fin = datetime.combine(hasta, datetime.max.time(), tzinfo=timezone.utc)

    def en_ventana(*condiciones) -> int:
        return db.scalar(
            select(func.count()).select_from(Canje).where(
                Canje.fecha_solicitud >= inicio, Canje.fecha_solicitud <= fin, *condiciones
            )
        ) or 0

    def historico(*condiciones) -> int:
        return db.scalar(
            select(func.count()).select_from(Canje).where(*condiciones)
        ) or 0

    cerrados = historico(Canje.etapa == CanjeEtapa.CERRADO, Canje.estado == CanjeEstado.ACTIVO)
    cancelados_hist = historico(Canje.estado == CanjeEstado.CANCELADO)
    resueltos = cerrados + cancelados_hist

    return CanjesDirectorio(
        solicitados=en_ventana(),
        activos=en_ventana(Canje.estado == CanjeEstado.ACTIVO),
        cancelados=en_ventana(Canje.estado == CanjeEstado.CANCELADO),
        solicitados_historicos=historico(),
        activos_historicos=historico(Canje.estado == CanjeEstado.ACTIVO),
        cerrados_historicos=cerrados,
        resueltos_historicos=resueltos,
        tasa_cierre_pct=(
            CERO
            if resueltos == 0
            else (Decimal(cerrados) / Decimal(resueltos) * 100).quantize(Decimal("0.1"))
        ),
        por_operacion=_conteos(db, Canje.tipo_operacion),
        por_tipo_inmueble=_conteos(db, Canje.tipo_inmueble, TOPE_DESGLOSE),
        por_comuna=_conteos(db, Canje.comuna, TOPE_DESGLOSE),
    )


def obtener_vista_directorio(
    db: Session, hoy: date | None = None, ventana: int = VENTANA_DEFECTO
) -> VistaDirectorio:
    """La vista de directorio, separada por dominio y con la ventana elegible.

    **La ventana solo manda sobre lo temporal**: la ventana móvil, la serie, la
    tendencia y los conteos de canjes del período. Los buckets --ganado, en
    proceso, no concretado--, la tasa de cierre, el ticket y la proyección siguen
    siendo históricos, y eso es deliberado: un negocio abierto está abierto y no
    pertenece a un mes, y una tasa de cierre calculada sobre uno o dos casos
    resueltos daría un intervalo de 2,5% a 100%, que es peor que no darla.
    """
    if ventana not in VENTANAS_VALIDAS:
        raise ValueError(f"La ventana tiene que ser una de {VENTANAS_VALIDAS}.")

    hoy = hoy or datetime.now(timezone.utc).date()
    anio, mes = hoy.year, hoy.month

    # La histórica se resuelve al número real de meses, igual que en el mensual.
    es_historico = ventana == VENTANA_HISTORICO
    if es_historico:
        ventana = _meses_entre(_primer_mes_con_datos(db), (anio, mes))
    inicios = _inicio_por_dominio(db)

    desde_a, hasta_a = rango_anio_corrido(anio, mes)
    desde_ap, hasta_ap = rango_anio_corrido(anio - 1, mes)
    desde_v, hasta_v = rango_ventana(anio, mes, ventana)

    pipeline = _bucket(db, (EstadoNegocio.ACTIVO,))
    conversion = _conversion(db)
    serie = _serie_mensual(db, anio, mes, ventana)

    return VistaDirectorio(
        generado=hoy,
        ventana_meses=ventana,
        anio_corrido=_metricas(db, desde_a, hasta_a, f"{desde_a:%Y-%m} a {hasta_a:%Y-%m}"),
        anio_corrido_anterior=_metricas(
            db, desde_ap, hasta_ap, f"{desde_ap:%Y-%m} a {hasta_ap:%Y-%m}"
        ),
        ventana_movil=_metricas(db, desde_v, hasta_v, f"{desde_v:%Y-%m} a {hasta_v:%Y-%m}"),
        ganado=_bucket(db, (EstadoNegocio.CERRADO,)),
        pipeline=pipeline,
        potencial_perdido=_bucket(db, (EstadoNegocio.PERDIDO, EstadoNegocio.DESISTIDO)),
        por_modelo=_montos_por_modelo(db),
        por_alianza=_montos_por_alianza(db),
        conversion=conversion,
        ticket=_ticket(db),
        proyeccion=_proyeccion(db, pipeline, conversion),
        serie=serie,
        es_historico=es_historico,
        inicio_por_dominio={
            dom: (f"{v[0]:04d}-{v[1]:02d}" if v else None) for dom, v in inicios.items()
        },
        promedio=_promedio(serie, inicios),
        tendencias={
            campo: _tendencia(serie, campo, nombre, inicios.get(DOMINIOS[campo]))
            for campo, nombre in METRICAS
        },
        canjes=_canjes(db, desde_v, hasta_v),
    )
