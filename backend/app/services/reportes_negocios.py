"""Base de cálculo de la reportería de negocios (sprint 12).

Es la capa que consumen el dashboard y los reportes de los sprints 13 a 18. Su
razón de existir es una sola: **separar los tres buckets de forma estructural**,
no dejarlo como un filtro que alguien tenga que recordar aplicar.

Los tres son plata, pero no la misma plata:

- **Ganado** -- liquidaciones cerradas. Entró.
- **Pipeline** -- liquidaciones activas. Podría entrar.
- **Potencial perdido** -- liquidaciones perdidas o desistidas. No entró, y el
  monto se conserva a propósito porque saber cuánto se dejó de ganar sirve para
  analizar (D-006).

Sumar los tres da un número que no significa nada. Por eso no existe un campo
`total`: si alguien lo quiere, lo suma a mano y sabe lo que está haciendo.

Los montos ya están en pesos en la base -- las columnas `comision_*` son
`numeric(16,2)` en CLP, resueltas al guardar con la UF congelada del hito. Acá
no se convierte nada; solo se agrupa.
"""
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.catalogo import Catalogo, EstadoNegocio, Etapa
from app.models.negocio import Negocio, NegocioHito

CERO = Decimal("0")

# Qué estados caen en cada bucket. `DESISTIDO` va con lo perdido: no entró.
BUCKETS: dict[str, tuple[EstadoNegocio, ...]] = {
    "ganado": (EstadoNegocio.CERRADO,),
    "pipeline": (EstadoNegocio.ACTIVO,),
    "potencial_perdido": (EstadoNegocio.PERDIDO, EstadoNegocio.DESISTIDO),
}


class Bucket(BaseModel):
    hitos: int
    negocios: int
    valor_base: Decimal
    comision_total: Decimal
    comision_real_vp: Decimal
    rebate_concentrador: Decimal


class Corte(BaseModel):
    """Una fila de cualquier desglose: etiqueta más sus montos."""

    etiqueta: str
    hitos: int
    comision_total: Decimal
    comision_real_vp: Decimal


class ResumenNegocios(BaseModel):
    ganado: Bucket
    pipeline: Bucket
    potencial_perdido: Bucket
    # Los desgloses van sobre lo ganado, que es la plata real. El pipeline se
    # mira por etapa, que es donde está detenido.
    ganado_por_mes: list[Corte]
    ganado_por_alianza: list[Corte]
    ganado_por_modelo: list[Corte]
    pipeline_por_etapa: list[Corte]
    # Hitos sin valorizar: ni ganados ni perdidos en términos de plata, porque
    # todavía no tienen base. Se cuentan aparte para que no desaparezcan.
    hitos_sin_valorizar: int


def _con_estados(consulta: Select, estados: tuple[EstadoNegocio, ...]) -> Select:
    return consulta.where(NegocioHito.estado.in_(estados))


def _bucket(db: Session, estados: tuple[EstadoNegocio, ...]) -> Bucket:
    fila = db.execute(
        _con_estados(
            select(
                func.count(NegocioHito.id),
                func.count(func.distinct(NegocioHito.negocio_id)),
                func.coalesce(func.sum(func.coalesce(NegocioHito.valor_clp_manual, NegocioHito.valor_clp_calculado)), 0),
                func.coalesce(func.sum(NegocioHito.comision_total), 0),
                func.coalesce(func.sum(NegocioHito.comision_real_vp), 0),
                func.coalesce(func.sum(NegocioHito.rebate_concentrador), 0),
            ),
            estados,
        )
    ).one()
    return Bucket(
        hitos=fila[0],
        negocios=fila[1],
        valor_base=fila[2],
        comision_total=fila[3],
        comision_real_vp=fila[4],
        rebate_concentrador=fila[5],
    )


def _etiqueta(valor) -> str:
    """Los enums se muestran por su valor, no por su repr de Python."""
    if valor is None:
        return "Sin dato"
    return valor.value if hasattr(valor, "value") else str(valor)


def _cortes(db: Session, consulta: Select) -> list[Corte]:
    return [
        Corte(
            etiqueta=_etiqueta(etiqueta),
            hitos=hitos,
            comision_total=total,
            comision_real_vp=real,
        )
        for etiqueta, hitos, total, real in db.execute(consulta).all()
    ]


def _montos():
    return (
        func.count(NegocioHito.id),
        func.coalesce(func.sum(NegocioHito.comision_total), 0),
        func.coalesce(func.sum(NegocioHito.comision_real_vp), 0),
    )


def _por_mes(db: Session, estados: tuple[EstadoNegocio, ...]) -> list[Corte]:
    """Agrupa por mes de cierre: lo que importa es cuando entro la plata.

    El agrupamiento se hace en Python y no en SQL a proposito. `to_char` es
    exclusivo de Postgres y dejaria este calculo sin poder testearse contra la
    base en memoria. Con este volumen la diferencia es irrelevante, y tener el
    numero verificado vale mas que ahorrar una vuelta.
    """
    filas = db.execute(
        _con_estados(
            select(
                NegocioHito.fecha_cierre,
                NegocioHito.comision_total,
                NegocioHito.comision_real_vp,
            ),
            estados,
        )
    ).all()

    acumulado: dict[str, list] = {}
    for cierre, total, real in filas:
        clave = cierre.strftime("%Y-%m") if cierre is not None else "Sin fecha"
        fila = acumulado.setdefault(clave, [0, CERO, CERO])
        fila[0] += 1
        fila[1] += total or CERO
        fila[2] += real or CERO

    return [
        Corte(etiqueta=mes, hitos=n, comision_total=t, comision_real_vp=r)
        for mes, (n, t, r) in sorted(acumulado.items())
    ]


def obtener_resumen_negocios(db: Session) -> ResumenNegocios:
    ganado = BUCKETS["ganado"]

    por_alianza = _con_estados(
        select(Catalogo.nombre, *_montos())
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.alianza_id)
        .group_by(Catalogo.nombre)
        .order_by(func.sum(NegocioHito.comision_real_vp).desc()),
        ganado,
    )

    por_modelo = _con_estados(
        select(Negocio.modelo, *_montos())
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .group_by(Negocio.modelo)
        .order_by(func.sum(NegocioHito.comision_real_vp).desc()),
        ganado,
    )

    # El pipeline se mira por etapa: es donde esta detenido cada negocio.
    por_etapa = _con_estados(
        select(Etapa.codigo, *_montos())
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .outerjoin(Etapa, Etapa.codigo == Negocio.etapa)
        .group_by(Etapa.codigo, Etapa.orden)
        .order_by(Etapa.orden),
        BUCKETS["pipeline"],
    )

    sin_valorizar = db.scalar(
        select(func.count(NegocioHito.id)).where(
            NegocioHito.valor_clp_manual.is_(None),
            NegocioHito.valor_clp_calculado.is_(None),
        )
    )

    return ResumenNegocios(
        ganado=_bucket(db, ganado),
        pipeline=_bucket(db, BUCKETS["pipeline"]),
        potencial_perdido=_bucket(db, BUCKETS["potencial_perdido"]),
        ganado_por_mes=_por_mes(db, ganado),
        ganado_por_alianza=_cortes(db, por_alianza),
        ganado_por_modelo=_cortes(db, por_modelo),
        pipeline_por_etapa=_cortes(db, por_etapa),
        hitos_sin_valorizar=sin_valorizar or 0,
    )
