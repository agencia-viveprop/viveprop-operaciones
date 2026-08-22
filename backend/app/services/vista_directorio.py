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
    MetricasMes,
    rango_anio_corrido,
    rango_ventana,
)

CERO = Decimal("0")

# Nivel de confianza del intervalo de la tasa de conversión. 1,96 es el z de 95%,
# que es la convención en reportería de negocio.
Z_95 = 1.96

# Meses de la ventana larga que acompaña al año corrido. Doce da la lectura
# anualizada sin depender de en qué mes del año estemos.
VENTANA_LARGA = 12


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


class VistaDirectorio(BaseModel):
    generado: date
    anio_corrido: MetricasMes
    anio_corrido_anterior: MetricasMes
    ultimos_12_meses: MetricasMes

    ganado: Bucket
    pipeline: Bucket
    potencial_perdido: Bucket

    por_modelo: list[Monto]
    por_alianza: list[Monto]

    conversion: Conversion
    ticket: Ticket | None
    proyeccion: Proyeccion

    canjes_vigentes: int
    canjes_historicos: int


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


def obtener_vista_directorio(db: Session, hoy: date | None = None) -> VistaDirectorio:
    from app.services.reporte_mensual import _metricas

    hoy = hoy or datetime.now(timezone.utc).date()
    anio, mes = hoy.year, hoy.month

    desde_a, hasta_a = rango_anio_corrido(anio, mes)
    desde_ap, hasta_ap = rango_anio_corrido(anio - 1, mes)
    desde_v, hasta_v = rango_ventana(anio, mes, VENTANA_LARGA)

    pipeline = _bucket(db, (EstadoNegocio.ACTIVO,))
    conversion = _conversion(db)

    return VistaDirectorio(
        generado=hoy,
        anio_corrido=_metricas(db, desde_a, hasta_a, f"{desde_a:%Y-%m} a {hasta_a:%Y-%m}"),
        anio_corrido_anterior=_metricas(
            db, desde_ap, hasta_ap, f"{desde_ap:%Y-%m} a {hasta_ap:%Y-%m}"
        ),
        ultimos_12_meses=_metricas(db, desde_v, hasta_v, f"{desde_v:%Y-%m} a {hasta_v:%Y-%m}"),
        ganado=_bucket(db, (EstadoNegocio.CERRADO,)),
        pipeline=pipeline,
        potencial_perdido=_bucket(db, (EstadoNegocio.PERDIDO, EstadoNegocio.DESISTIDO)),
        por_modelo=_montos_por_modelo(db),
        por_alianza=_montos_por_alianza(db),
        conversion=conversion,
        ticket=_ticket(db),
        proyeccion=_proyeccion(db, pipeline, conversion),
        canjes_vigentes=db.scalar(
            select(func.count()).select_from(Canje).where(
                Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO
            )
        ) or 0,
        canjes_historicos=db.scalar(select(func.count()).select_from(Canje)) or 0,
    )
