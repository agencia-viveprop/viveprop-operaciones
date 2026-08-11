from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa


class ConteoEtiqueta(BaseModel):
    etiqueta: str
    cantidad: int


class ResumenCanjes(BaseModel):
    total: int
    activos: int
    cancelados: int
    tasa_activos_pct: float
    por_etapa: list[ConteoEtiqueta]
    por_mes: list[ConteoEtiqueta]
    por_tipo_inmueble: list[ConteoEtiqueta]
    por_operacion: list[ConteoEtiqueta]


ETAPA_LABELS = {
    CanjeEtapa.SIN_ETAPA: "Sin etapa",
    CanjeEtapa.EN_REVISION: "En revisión",
    CanjeEtapa.PROCESO_DE_ACUERDO: "Proceso de acuerdo",
    CanjeEtapa.EN_OFERTA: "En oferta",
    CanjeEtapa.EN_NEGOCIO: "En negocio",
    CanjeEtapa.CERRADO: "Cerrado",
}


def obtener_resumen_canjes(db: Session) -> ResumenCanjes:
    total = db.scalar(select(func.count()).select_from(Canje)) or 0
    activos = db.scalar(select(func.count()).select_from(Canje).where(Canje.estado == CanjeEstado.ACTIVO)) or 0
    cancelados = db.scalar(select(func.count()).select_from(Canje).where(Canje.estado == CanjeEstado.CANCELADO)) or 0
    tasa_activos_pct = round((activos / total * 100), 1) if total else 0.0

    filas_etapa = db.execute(select(Canje.etapa, func.count()).group_by(Canje.etapa)).all()
    conteos_etapa = dict(filas_etapa)
    por_etapa = [
        ConteoEtiqueta(etiqueta=ETAPA_LABELS[e], cantidad=conteos_etapa.get(e, 0)) for e in CanjeEtapa
    ]

    # Se usa el alias "periodo" en GROUP BY/ORDER BY en vez de repetir la
    # expresion to_char(...) tres veces -- repetirla generaba un parametro
    # ligado distinto por ocurrencia y Postgres no reconocia que era la
    # misma expresion (GroupingError), aunque el valor fuera igual siempre.
    filas_mes = db.execute(
        text(
            """
            SELECT to_char(fecha_solicitud, 'YYYY-MM') AS periodo, count(*) AS cantidad
            FROM canjes
            GROUP BY periodo
            ORDER BY periodo
            """
        )
    ).all()
    por_mes = [ConteoEtiqueta(etiqueta=periodo, cantidad=cant) for periodo, cant in filas_mes]

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
        cancelados=cancelados,
        tasa_activos_pct=tasa_activos_pct,
        por_etapa=por_etapa,
        por_mes=por_mes,
        por_tipo_inmueble=por_tipo_inmueble,
        por_operacion=por_operacion,
    )
