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
    # Los negocios se cuentan aparte de las liquidaciones porque son dos
    # unidades distintas y ninguna reemplaza a la otra: un negocio puede tener
    # la promesa y la escritura, así que 7 liquidaciones pueden ser 6 negocios.
    negocios: int
    comision_total: Decimal
    comision_real_vp: Decimal


class CorteMes(BaseModel):
    """Un mes con cuántos negocios arrancaron y cuánta comisión real llevan."""

    etiqueta: str
    negocios: int
    comision_real_vp: Decimal


class NegociosPorMes(BaseModel):
    meses: list[CorteMes]
    total_negocios: int
    # Cuántos de esos negocios tienen la fecha de inicio igual a la de cierre.
    # En los migrados del Excel el origen traía **una sola fecha**, así que caen
    # en el mes en que cerraron y no en el que realmente empezaron. Se cuenta y
    # se dice en la pantalla: el gráfico sigue siendo lo mejor que se puede
    # armar con el dato, pero quien lo lee tiene que saber qué está mirando. El
    # número baja solo a medida que entran negocios con fechas de verdad.
    con_inicio_aproximado: int = 0
    # Se devuelven los filtros aplicados para que el front pueda mostrar qué se
    # está mirando sin tener que reconstruirlo desde su propio estado.
    modelo: str | None = None
    tipo_operacion: str | None = None


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
    # El universo completo, para que la pantalla pueda decir "2 de 18" sin
    # sumar los tres buckets. Sumarlos **no** da el total de negocios: un
    # negocio con la promesa ganada y la escritura abierta está en dos, así que
    # la suma lo cuenta dos veces. En liquidaciones sí cierra exacto, porque
    # cada una tiene un estado y uno solo.
    total_negocios: int
    total_hitos: int
    # Ganadas sobre resueltas --ganadas más no concretadas--. Deja afuera las
    # abiertas a propósito: todavía no se sabe en qué van a terminar, y meterlas
    # en el denominador haría que la tasa baje sola cuando entra un negocio
    # nuevo, que es exactamente lo contrario de lo que uno quiere leer.
    tasa_cierre_pct: float


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
            negocios=negocios,
            comision_total=total,
            comision_real_vp=real,
        )
        for etiqueta, hitos, negocios, total, real in db.execute(consulta).all()
    ]


def _montos():
    return (
        func.count(NegocioHito.id),
        func.count(func.distinct(NegocioHito.negocio_id)),
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
                NegocioHito.negocio_id,
                NegocioHito.comision_total,
                NegocioHito.comision_real_vp,
            ),
            estados,
        )
    ).all()

    # Los negocios del mes van en un conjunto: dos liquidaciones del mismo
    # negocio cerradas el mismo mes son un negocio, no dos.
    acumulado: dict[str, list] = {}
    for cierre, negocio_id, total, real in filas:
        clave = cierre.strftime("%Y-%m") if cierre is not None else "Sin fecha"
        fila = acumulado.setdefault(clave, [0, set(), CERO, CERO])
        fila[0] += 1
        fila[1].add(negocio_id)
        fila[2] += total or CERO
        fila[3] += real or CERO

    return [
        Corte(etiqueta=mes, hitos=n, negocios=len(ids), comision_total=t, comision_real_vp=r)
        for mes, (n, ids, t, r) in sorted(acumulado.items())
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

    ganadas = db.scalar(
        select(func.count(NegocioHito.id)).where(NegocioHito.estado.in_(ganado))
    ) or 0
    no_concretadas = db.scalar(
        select(func.count(NegocioHito.id)).where(
            NegocioHito.estado.in_(BUCKETS["potencial_perdido"])
        )
    ) or 0
    resueltas = ganadas + no_concretadas

    return ResumenNegocios(
        ganado=_bucket(db, ganado),
        pipeline=_bucket(db, BUCKETS["pipeline"]),
        potencial_perdido=_bucket(db, BUCKETS["potencial_perdido"]),
        ganado_por_mes=_por_mes(db, ganado),
        ganado_por_alianza=_cortes(db, por_alianza),
        ganado_por_modelo=_cortes(db, por_modelo),
        pipeline_por_etapa=_cortes(db, por_etapa),
        hitos_sin_valorizar=sin_valorizar or 0,
        total_negocios=db.scalar(select(func.count(Negocio.id))) or 0,
        total_hitos=db.scalar(select(func.count(NegocioHito.id))) or 0,
        tasa_cierre_pct=round(ganadas * 100 / resueltas, 1) if resueltas else 0.0,
    )


def negocios_por_mes(
    db: Session,
    modelo: str | None = None,
    tipo_operacion: str | None = None,
) -> NegociosPorMes:
    """Cuántos negocios arrancaron cada mes, con filtros por modelo y operación.

    **Cuenta negocios, no liquidaciones**, y cada uno cae en el mes de su hito
    más antiguo. `VVP-3` tiene una promesa y una escritura en meses distintos;
    contarlo dos veces diría que hubo dos negocios cuando hubo uno.

    **Ojo con la calidad de `fecha_inicio` en los migrados.** En los negocios que
    vienen del Excel esa fecha coincide con la de cierre, porque el origen traía
    una sola: caen en el mes en que cerraron y no en el que empezaron. No se
    corrige --no hay dato con el que corregirlo-- pero se **cuenta** en
    `con_inicio_aproximado` y la pantalla lo dice. El número baja solo a medida
    que entran negocios con fechas de verdad.

    **Mira `fecha_inicio`, no `fecha_cierre`.** Es el equivalente de "solicitudes
    por mes" en canjes: mide cuánto entró, no cuánto se cobró. Lo cobrado ya está
    en `ganado_por_mes`, que agrupa por cierre y responde otra pregunta.

    **Incluye todos los estados**, ganados, activos y perdidos. Un negocio que se
    perdió igual entró ese mes, y sacarlo haría que el pasado se encogiera cada
    vez que algo se cae.

    El agrupamiento va en Python por la misma razón que en `_por_mes`: `to_char`
    es de Postgres y dejaría esto sin poder testearse contra SQLite.
    """
    consulta = (
        select(
            Negocio.id,
            NegocioHito.fecha_inicio,
            func.coalesce(NegocioHito.comision_real_vp, 0),
            NegocioHito.fecha_cierre,
        )
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
    )
    if modelo:
        consulta = consulta.where(Negocio.modelo == modelo)
    if tipo_operacion:
        consulta = consulta.join(
            Catalogo, Catalogo.id == Negocio.tipo_operacion_id
        ).where(Catalogo.codigo == tipo_operacion)

    # Por negocio: su fecha mas antigua y la suma de lo que lleva cobrado.
    por_negocio: dict[int, list] = {}
    # Los que arrastran el problema de la fecha unica del Excel.
    aproximados: set[int] = set()
    for negocio_id, inicio, real, cierre in db.execute(consulta).all():
        if inicio is not None and cierre == inicio:
            aproximados.add(negocio_id)
        fila = por_negocio.setdefault(negocio_id, [inicio, CERO])
        if inicio is not None and (fila[0] is None or inicio < fila[0]):
            fila[0] = inicio
        fila[1] += real or CERO

    acumulado: dict[str, list] = {}
    for inicio, real in por_negocio.values():
        clave = inicio.strftime("%Y-%m") if inicio is not None else "Sin fecha"
        fila = acumulado.setdefault(clave, [0, CERO])
        fila[0] += 1
        fila[1] += real

    return NegociosPorMes(
        meses=[
            CorteMes(etiqueta=mes, negocios=n, comision_real_vp=r)
            for mes, (n, r) in sorted(acumulado.items())
        ],
        total_negocios=len(por_negocio),
        con_inicio_aproximado=len(aproximados & set(por_negocio)),
        modelo=modelo,
        tipo_operacion=tipo_operacion,
    )
