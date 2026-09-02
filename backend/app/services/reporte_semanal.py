"""Reporte semanal: cómo se movió el mes, semana a semana, contra los anteriores.

**El eje es la semana del mes, y los meses anteriores van superpuestos.** Es lo
que el usuario pidió: *«poder mostrar cómo van moviéndose los canjes y los
negocios semana a semana dentro del mes, y a la vez tener la opción de compararlo
con meses anteriores»*. La versión anterior de esta pantalla medía una ventana
móvil de semanas corridas y no permitía comparar nada.

**Cuatro bloques, y cada uno responde una pregunta**, que es la restricción que él
puso --*«que quien lo vea pueda entender lo que está viendo»*--:

| Bloque | La pregunta |
|---|---|
| `flujo` | cómo se movió el mes, semana a semana |
| `embudo` | por dónde avanzaron |
| `abiertos` | dónde está lo abierto hoy y cuánta plata hay ahí |
| `totales` | mes a mes, con promedio y tendencia |

**La tendencia va sobre los meses y no sobre las semanas.** Cinco puntos
semanales, con el último de tres días, no sostienen una curva: el ajuste bajaría
siempre al final por un artefacto del calendario. Sobre los meses comparados sí, y
aparece desde tres.

**Las señales que no se pueden medir se declaran en `sin_datos`.** En negocios,
«avanzaron» y «se cayeron» son cero por dos razones distintas del estado del
proyecto: el pipeline no tiene ni un movimiento registrado, y las diez
liquidaciones perdidas no tienen fecha de cierre. Dibujar una serie de ceros ahí
diría «no pasó nada», cuando lo que pasa es «no se sabe». La pantalla lo explica.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalogo import EstadoNegocio
from app.models.canje import CanjeEtapa
from app.models.catalogo import Etapa
from app.models.movimiento import EntityType, Movimiento
from app.models.negocio import NegocioHito
from app.services.metricas_periodo import (
    EtapaAbierta,
    EtapaDelEmbudo,
    FlujoDelMes,
    Semana,
    TotalDelMes,
    Tramo,
    abiertos_de_canjes,
    abiertos_de_negocios,
    embudo_de_canjes,
    embudo_de_negocios,
    flujo_de_canjes_por_tramo,
    flujo_de_negocios_por_tramo,
    instantes_de_carga,
    semanas_del_mes,
)
from app.services.reporte_mensual import (
    Tendencia,
    correr_meses,
    limites,
    _tendencia,
)
from app.services.uf import serie_completa

CERO = Decimal("0")

# Cuántos meses anteriores se pueden comparar. Uno es «solo este mes, sin
# comparación»; doce es el año hacia atrás.
MESES_VALIDOS = tuple(range(1, 13))
MESES_DEFECTO = 3

class ReporteDeDominio(BaseModel):
    semanas: list[Semana]
    # El mes elegido primero y después los anteriores, del más nuevo al más viejo.
    # La pantalla dibuja el primero destacado y el resto como referencia.
    flujo: list[FlujoDelMes]
    embudo: list[EtapaDelEmbudo]
    abiertos: list[EtapaAbierta]
    # Del más viejo al más nuevo, incluido el mes elegido: es el eje del bloque de
    # tendencia.
    totales: list[TotalDelMes]
    tendencias: dict[str, Tendencia]
    # Qué señales no se pueden medir en este dominio, por nombre de campo. La
    # pantalla las explica en vez de dibujar ceros.
    sin_datos: list[str]


class ReporteSemanal(BaseModel):
    anio: int
    mes: int
    # Cuántos meses hacia atrás se comparan, contando el elegido.
    meses: int
    canjes: ReporteDeDominio
    negocios: ReporteDeDominio


def _clave(anio: int, mes: int) -> str:
    return f"{anio:04d}-{mes:02d}"


def _meses_de_la_ventana(anio: int, mes: int, meses: int) -> list[tuple[int, int]]:
    """El mes elegido y los anteriores, del más viejo al más nuevo."""
    return [correr_meses(anio, mes, -(meses - 1 - i)) for i in range(meses)]


def _embudo(
    entradas_del_mes: dict[str, int],
    entradas_anteriores: list[dict[str, int]],
    etapas: list[str],
) -> list[EtapaDelEmbudo]:
    """El embudo del mes con el promedio de los meses anteriores al lado.

    **Todas las etapas del pipeline van, incluso en cero.** El embudo se lee por
    su forma --dónde se angosta-- y una etapa que desaparece porque nadie pasó por
    ella rompe esa lectura: parece que la etapa no existe.

    El promedio va como número y no como una segunda barra: es la referencia, y
    duplicar las barras es justo lo que recarga la pantalla.
    """
    salida = []
    for etapa in etapas:
        previos = [m.get(etapa, 0) for m in entradas_anteriores]
        promedio = (
            (Decimal(sum(previos)) / len(previos)).quantize(Decimal("0.1"))
            if previos
            else CERO
        )
        salida.append(
            EtapaDelEmbudo(
                etapa=etapa,
                entraron=entradas_del_mes.get(etapa, 0),
                promedio_anteriores=promedio,
            )
        )
    return salida


def _etapas_de_negocio(db: Session) -> list[str]:
    return list(db.scalars(select(Etapa.codigo).order_by(Etapa.orden)))


def _sin_datos_de_negocios(db: Session) -> list[str]:
    """Qué señales de negocios no tienen de dónde salir, medido y no supuesto.

    Se calcula en vez de escribirse fijo porque las dos condiciones se resuelven
    solas en cuanto alguien registre un avance o cierre una liquidación perdida
    con su fecha. Un aviso que envejece mal es peor que ninguno.
    """
    faltan = []
    avances = db.scalar(
        select(func.count()).where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.etapa_resultante.is_not(None),
        )
    )
    if not avances:
        faltan.append("avanzaron")

    caidas_con_fecha = db.scalar(
        select(func.count()).select_from(NegocioHito).where(
            NegocioHito.estado.in_((EstadoNegocio.PERDIDO, EstadoNegocio.DESISTIDO)),
            NegocioHito.fecha_cierre.is_not(None),
        )
    )
    if not caidas_con_fecha:
        faltan.append("se_cayeron")
    return faltan


def _tramos_de_semana(ventana: list[tuple[int, int]]) -> list[Tramo]:
    """Las semanas de todos los meses de la ventana, con el mes en la clave.

    La clave lleva el mes --`2026-08 / S1 1-7`-- porque las semanas de meses
    distintos comparten etiqueta y se pisarían en el reparto.
    """
    return [
        Tramo(clave=f"{a:04d}-{m:02d} / {s.etiqueta}", desde=s.desde, hasta=s.hasta)
        for a, m in ventana
        for s in semanas_del_mes(a, m)
    ]


def _tramos_de_mes(ventana: list[tuple[int, int]]) -> list[Tramo]:
    tramos = []
    for a, m in ventana:
        desde, hasta = limites(a, m)
        tramos.append(Tramo(clave=_clave(a, m), desde=desde, hasta=hasta))
    return tramos


def _armar_dominio(
    anio: int,
    mes: int,
    ventana: list[tuple[int, int]],
    por_semana: dict[str, tuple],
    por_mes: dict[str, tuple],
    embudos: list[dict[str, int]],
    etapas: list[str],
    abiertos: list[EtapaAbierta],
    dominio: str,
    sin_datos: list[str],
    plata_semanal: bool,
) -> ReporteDeDominio:
    """Arma la respuesta de un dominio a partir de los repartos ya calculados.

    Los dos dominios comparten esta función porque la forma de la respuesta es la
    misma; lo que cambia es de dónde salen los números, y eso ya se resolvió antes
    de llegar acá.
    """
    flujo = []
    for a, m in ventana:
        claves = [
            f"{a:04d}-{m:02d} / {s.etiqueta}" for s in semanas_del_mes(a, m)
        ]
        filas = [por_semana.get(c, (0, 0, 0, CERO, CERO, CERO)) for c in claves]
        flujo.append(
            FlujoDelMes(
                mes=_clave(a, m),
                entraron=[f[0] for f in filas],
                avanzaron=[f[1] for f in filas],
                se_cayeron=[f[2] for f in filas],
                # En negocios la plata se gana al cerrar, no al entrar, así que la
                # columna semanal de «lo que entró» no tiene de dónde salir y va en
                # cero: la plata de negocios vive en el bloque mensual.
                comision_entraron=[f[3] if plata_semanal else CERO for f in filas],
            )
        )
    # El mes elegido primero: la pantalla lo destaca y el resto es referencia.
    flujo.reverse()

    totales = []
    for a, m in ventana:
        f = por_mes.get(_clave(a, m), (0, 0, 0, CERO, CERO, CERO))
        totales.append(
            TotalDelMes(
                etiqueta=_clave(a, m),
                entraron=f[0],
                avanzaron=f[1],
                se_cayeron=f[2],
                comision=f[3],
                valor_venta=f[4],
                valor_arriendo=f[5],
            )
        )

    return ReporteDeDominio(
        semanas=semanas_del_mes(anio, mes),
        flujo=flujo,
        embudo=_embudo(embudos[-1], embudos[:-1], etapas),
        abiertos=abiertos,
        totales=totales,
        tendencias=_tendencias(totales, dominio),
        sin_datos=sin_datos,
    )


def _dominio_canjes(
    db: Session, anio: int, mes: int, meses: int, hoy: date, cache_uf: dict
) -> ReporteDeDominio:
    ventana = _meses_de_la_ventana(anio, mes, meses)
    cargas = instantes_de_carga(db, EntityType.canje)
    por_semana = flujo_de_canjes_por_tramo(
        db, _tramos_de_semana(ventana), cargas, hoy, cache_uf
    )
    por_mes = flujo_de_canjes_por_tramo(db, _tramos_de_mes(ventana), cargas, hoy, cache_uf)
    embudos = [embudo_de_canjes(db, *limites(a, m)) for a, m in ventana]

    return _armar_dominio(
        anio, mes, ventana, por_semana, por_mes, embudos,
        [e.value for e in CanjeEtapa],
        abiertos_de_canjes(db, hoy, cache_uf),
        "canjes",
        [],
        plata_semanal=True,
    )


def _dominio_negocios(
    db: Session, anio: int, mes: int, meses: int, hoy: date
) -> ReporteDeDominio:
    ventana = _meses_de_la_ventana(anio, mes, meses)
    por_semana = flujo_de_negocios_por_tramo(db, _tramos_de_semana(ventana))
    por_mes = flujo_de_negocios_por_tramo(db, _tramos_de_mes(ventana))
    embudos = [embudo_de_negocios(db, *limites(a, m)) for a, m in ventana]

    return _armar_dominio(
        anio, mes, ventana, por_semana, por_mes, embudos,
        _etapas_de_negocio(db),
        abiertos_de_negocios(db, hoy),
        "negocios",
        _sin_datos_de_negocios(db),
        plata_semanal=False,
    )


def _tendencias(totales: list[TotalDelMes], dominio: str) -> dict[str, Tendencia]:
    """La curva sobre los meses, para las señales y para la plata.

    Reusa el ajuste del reporte mensual --mismos grados por cantidad de puntos,
    misma regla de cuándo mostrarla-- en vez de escribir un segundo ajuste que
    habría que mantener en paralelo (`D-089`).
    """
    campos = (
        ("entraron", "Entraron"),
        ("avanzaron", "Avanzaron"),
        ("se_cayeron", "Se cayeron"),
        ("comision", "Comisión"),
        ("valor_venta", "Monto de las ventas"),
        ("valor_arriendo", "Monto de los arriendos"),
    )
    return {
        campo: _tendencia(totales, campo, nombre, dominio=dominio)
        for campo, nombre in campos
    }


def obtener_reporte_semanal(
    db: Session,
    anio: int | None = None,
    mes: int | None = None,
    meses: int = MESES_DEFECTO,
    hoy: date | None = None,
) -> ReporteSemanal:
    hoy = hoy or datetime.now(timezone.utc).date()
    anio = anio or hoy.year
    mes = mes or hoy.month
    if meses not in MESES_VALIDOS:
        raise ValueError(f"Los meses a comparar tienen que ser uno de {list(MESES_VALIDOS)}.")

    # La serie de UF entera, de una vez: la plata de canjes valoriza cada canje con
    # la UF de su propia fecha, y este reporte los recorre una vez por semana y por
    # mes comparado. Pidiéndolas de a una eran cientos de consultas (`D-098`).
    cache_uf = serie_completa(db)

    return ReporteSemanal(
        anio=anio,
        mes=mes,
        meses=meses,
        canjes=_dominio_canjes(db, anio, mes, meses, hoy, cache_uf),
        negocios=_dominio_negocios(db, anio, mes, meses, hoy),
    )
