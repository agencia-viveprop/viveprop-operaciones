from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import ETAPA_LABELS, Canje, CanjeEstado, CanjeEtapa


class ConteoEtiqueta(BaseModel):
    etiqueta: str
    cantidad: int


class ConteoEtapa(BaseModel):
    """Una etapa con su total y el desglose por estado.

    Los tres números vienen juntos para que la pantalla pueda filtrar sin volver a
    consultar: son seis etapas por dos estados, no vale una ida al servidor por
    cada clic en el selector.
    """

    etiqueta: str
    cantidad: int
    activos: int
    cerrados: int
    cancelados: int


class ResumenCanjes(BaseModel):
    total: int
    activos: int
    # Los que se concretaron. Cero en todo el historico: el estado no existia
    # hasta ahora, y los 31 que llegaron a la etapa de cierre se cayeron.
    cerrados: int
    cancelados: int
    tasa_activos_pct: float
    # Cerrados sobre resueltos. Las abiertas quedan afuera del denominador.
    tasa_cierre_pct: float
    # Los que están ACTIVO pero con la etapa en Cerrado. El tile de «Activos» los
    # excluye --un canje cerrado no está activo, aunque su estado no se haya
    # actualizado-- así que sin este número la suma del desglose por etapa no
    # cuadraría con el tile y no habría forma de explicar la diferencia.
    activos_con_etapa_cerrada: int
    por_etapa: list[ConteoEtapa]
    por_mes: list[ConteoEtiqueta]
    por_tipo_inmueble: list[ConteoEtiqueta]
    por_operacion: list[ConteoEtiqueta]




def obtener_resumen_canjes(db: Session) -> ResumenCanjes:
    total = db.scalar(select(func.count()).select_from(Canje)) or 0
    activos = (
        db.scalar(
            select(func.count())
            .select_from(Canje)
            .where(Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO)
        )
        or 0
    )
    cerrados = db.scalar(
        select(func.count()).select_from(Canje).where(Canje.estado == CanjeEstado.CERRADO)
    ) or 0
    cancelados = db.scalar(select(func.count()).select_from(Canje).where(Canje.estado == CanjeEstado.CANCELADO)) or 0
    tasa_activos_pct = round((activos / total * 100), 1) if total else 0.0
    # Cerrados sobre resueltos, no sobre el total: un canje que sigue abierto
    # todavia no fallo, y meterlo en el denominador haria que la tasa de cierre
    # baje sola cuando entra una solicitud nueva. Es el mismo criterio que la tasa
    # de cierre de negocios (`D-063`).
    resueltos = cerrados + cancelados
    tasa_cierre_pct = round((cerrados / resueltos * 100), 1) if resueltos else 0.0

    # Una sola consulta agrupada por las dos columnas: el desglose por estado sale
    # de acá, no de dos consultas más por etapa.
    filas_etapa = db.execute(
        select(Canje.etapa, Canje.estado, func.count()).group_by(Canje.etapa, Canje.estado)
    ).all()
    conteos: dict[tuple, int] = {(etapa, estado): n for etapa, estado, n in filas_etapa}
    por_etapa = [
        ConteoEtapa(
            etiqueta=ETAPA_LABELS[e],
            cantidad=sum(n for (etapa, _), n in conteos.items() if etapa == e),
            activos=conteos.get((e, CanjeEstado.ACTIVO), 0),
            cerrados=conteos.get((e, CanjeEstado.CERRADO), 0),
            cancelados=conteos.get((e, CanjeEstado.CANCELADO), 0),
        )
        for e in CanjeEtapa
    ]
    activos_con_etapa_cerrada = conteos.get((CanjeEtapa.CERRADO, CanjeEstado.ACTIVO), 0)

    # El agrupado por mes se hace en Python, no en SQL, y eso es deliberado.
    #
    # Antes era `to_char(fecha_solicitud, 'YYYY-MM')` en SQL crudo, que es una
    # funcion de Postgres: **dejaba todo este resumen sin poder probarse**, porque
    # los tests corren sobre SQLite y ahi `to_char` no existe. Por eso el
    # dashboard de canjes no tenia ni un test, y por eso este archivo llego a
    # producirse sin red.
    #
    # El costo es traer una fecha por canje en vez de un agregado. Son 297 filas y
    # crecen al ritmo en que Dataprop recibe solicitudes; a diez mil sigue siendo
    # una consulta y un bucle. Se gana poder probarlo y no depender del dialecto.
    fechas = db.scalars(select(Canje.fecha_solicitud)).all()
    conteo_mes: dict[str, int] = {}
    for f in fechas:
        clave = f"{f.year:04d}-{f.month:02d}"
        conteo_mes[clave] = conteo_mes.get(clave, 0) + 1
    por_mes = [
        ConteoEtiqueta(etiqueta=periodo, cantidad=conteo_mes[periodo])
        for periodo in sorted(conteo_mes)
    ]

    filas_tipo = db.execute(
        select(Canje.tipo_inmueble, func.count())
        .where(Canje.tipo_inmueble.is_not(None))
        .group_by(Canje.tipo_inmueble)
        .order_by(func.count().desc())
    ).all()
    por_tipo_inmueble = [ConteoEtiqueta(etiqueta=t or "Sin dato", cantidad=c) for t, c in filas_tipo]

    filas_operacion = db.execute(
        select(Canje.tipo_operacion, func.count())
        .where(Canje.tipo_operacion.is_not(None))
        .group_by(Canje.tipo_operacion)
    ).all()
    por_operacion = [ConteoEtiqueta(etiqueta=op.value if op else "Sin dato", cantidad=c) for op, c in filas_operacion]

    return ResumenCanjes(
        total=total,
        activos=activos,
        cerrados=cerrados,
        cancelados=cancelados,
        tasa_activos_pct=tasa_activos_pct,
        tasa_cierre_pct=tasa_cierre_pct,
        activos_con_etapa_cerrada=activos_con_etapa_cerrada,
        por_etapa=por_etapa,
        por_mes=por_mes,
        por_tipo_inmueble=por_tipo_inmueble,
        por_operacion=por_operacion,
    )
