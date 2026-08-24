from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio


class MovimientoError(Exception):
    pass


# Margen para el desfase entre el reloj del navegador y el del servidor. Sin él,
# registrar un movimiento "ahora" desde una máquina un minuto adelantada se
# rechazaría por venir del futuro.
HOLGURA_RELOJ = timedelta(minutes=5)


def _etapa_vigente(db: Session, tipo: EntityType, entity_id: int) -> str | None:
    """La etapa del movimiento **más reciente** que traiga una, no la del último
    que se guardó.

    **Por qué no es lo mismo.** Desde que la fecha del movimiento se puede
    atrasar, el último que se inserta no es necesariamente el más nuevo. Sin esto,
    anotar el lunes una gestión del día 10 en un canje que el día 20 ya había
    pasado a «En negocio» lo devolvía a «En revisión»: la etapa retrocedía sola,
    contra un movimiento posterior que seguía ahí. Medido antes de arreglarlo.

    Se resuelve leyendo, no acumulando: la etapa vigente es una consecuencia de la
    línea de tiempo, así que se deriva de ella.
    """
    return db.scalar(
        select(Movimiento.etapa_resultante)
        .where(
            Movimiento.entity_type == tipo,
            Movimiento.entity_id == entity_id,
            Movimiento.etapa_resultante.is_not(None),
        )
        .order_by(Movimiento.fecha.desc(), Movimiento.id.desc())
        .limit(1)
    )


def _validar_fecha(fecha: datetime | None, minimo: datetime | None, que_es_el_minimo: str) -> None:
    """La fecha de un movimiento se puede atrasar, no adelantar.

    **Por qué hace falta.** La pantalla dejó de fijar la fecha en "ahora" para que
    se pueda registrar gestión de días pasados, que es el caso real: uno anota el
    lunes lo que pasó el viernes. Pero la API acepta cualquier `datetime`, y una
    fecha futura envenena el reloj de la bandeja --`horas_sin_gestion` es
    `ahora - ultimo_movimiento`, así que daría **horas negativas** en pantalla-- y
    con ella el semáforo y el reporte semanal.

    Y una fecha anterior a que la cosa existiera tampoco es un dato: es un error
    de tipeo. Se rechaza con el mínimo a la vista, para que se vea cuál era.
    """
    if fecha is None:
        return

    # Una fecha sin zona viene del navegador ya convertida a UTC; se asume así en
    # vez de rechazarla, que es lo que hace el resto del proyecto.
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)

    ahora = datetime.now(timezone.utc)
    if fecha > ahora + HOLGURA_RELOJ:
        raise MovimientoError(
            f"La fecha del movimiento no puede ser futura: {fecha:%d-%m-%Y %H:%M}. "
            "La gestión se registra después de que pasa, no antes."
        )

    if minimo is not None:
        if minimo.tzinfo is None:
            minimo = minimo.replace(tzinfo=timezone.utc)
        if fecha < minimo:
            raise MovimientoError(
                f"La fecha del movimiento ({fecha:%d-%m-%Y}) es anterior a "
                f"{que_es_el_minimo} ({minimo:%d-%m-%Y})."
            )


def crear_movimiento_canje(
    db: Session,
    canje_id: int,
    tipo_codigo: str,
    autor_id: int | None,
    comentario: str | None = None,
    fecha: datetime | None = None,
) -> Movimiento:
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise MovimientoError("Canje no encontrado")

    tipo = db.get(TipoMovimiento, tipo_codigo)
    if tipo is None or tipo.entity_type != EntityType.canje:
        raise MovimientoError("Tipo de movimiento inválido para Canjes")

    _validar_fecha(fecha, canje.fecha_solicitud, "la fecha de solicitud del canje")

    movimiento = Movimiento(
        entity_type=EntityType.canje,
        entity_id=canje_id,
        tipo_movimiento=tipo.codigo,
        etapa_resultante=tipo.etapa_resultante,
        autor_id=autor_id,
        comentario=comentario,
        **({"fecha": fecha} if fecha is not None else {}),
    )
    db.add(movimiento)

    # Se necesita el movimiento en la base para que entre en la comparacion de
    # fechas; el commit viene despues igual.
    db.flush()
    vigente = _etapa_vigente(db, EntityType.canje, canje_id)
    if vigente is not None:
        canje.etapa = CanjeEtapa(vigente)

    # La cancelacion no se recalcula desde la linea de tiempo: un canje que se
    # canceló quedó cancelado, y que despues alguien anote otra gestion no lo
    # revive. Deshacerlo es una edicion manual, no un movimiento.
    if tipo.codigo == "CANCELACION":
        canje.estado = CanjeEstado.CANCELADO
    canje.gestionado_en_app = True

    db.commit()
    db.refresh(movimiento)
    return movimiento


# Estos tipos no mueven el negocio en el pipeline, cambian el desenlace de sus
# liquidaciones abiertas. El estado vive en el hito (ver D-027), asi que se
# aplica ahi y no en el negocio.
DESENLACES = {
    "NEG_PERDIDA": EstadoNegocio.PERDIDO,
    "NEG_DESISTIMIENTO": EstadoNegocio.DESISTIDO,
}


def crear_movimiento_negocio(
    db: Session,
    negocio_id: int,
    tipo_codigo: str,
    autor_id: int | None,
    comentario: str | None = None,
    fecha: datetime | None = None,
) -> Movimiento:
    """Registra un movimiento y, si el tipo lo dice, avanza el negocio de etapa.

    `movimientos.entity_id` no tiene ni puede tener clave foranea porque apunta a
    dos tablas (canje o negocio). Por eso la existencia del negocio se verifica
    aca, igual que hace `crear_movimiento_canje` con el canje.
    """
    negocio = db.get(Negocio, negocio_id)
    if negocio is None:
        raise MovimientoError(f"No existe el negocio {negocio_id}")

    tipo = db.get(TipoMovimiento, tipo_codigo)
    if tipo is None or tipo.entity_type != EntityType.negocio:
        raise MovimientoError(f"Tipo de movimiento invalido para Negocios: '{tipo_codigo}'")

    # El mínimo es el hito más antiguo: un negocio empieza cuando empieza su
    # primera liquidación. Sin hitos no hay mínimo que exigir, solo el futuro.
    inicio = min((h.fecha_inicio for h in negocio.hitos if h.fecha_inicio), default=None)
    _validar_fecha(
        fecha,
        datetime.combine(inicio, datetime.min.time(), tzinfo=timezone.utc) if inicio else None,
        "la fecha de inicio del negocio",
    )

    movimiento = Movimiento(
        entity_type=EntityType.negocio,
        entity_id=negocio_id,
        tipo_movimiento=tipo.codigo,
        etapa_resultante=tipo.etapa_resultante,
        autor_id=autor_id,
        comentario=comentario,
        **({"fecha": fecha} if fecha is not None else {}),
    )
    db.add(movimiento)

    db.flush()
    vigente = _etapa_vigente(db, EntityType.negocio, negocio_id)
    if vigente is not None:
        negocio.etapa = vigente

    if tipo.codigo in DESENLACES:
        nuevo = DESENLACES[tipo.codigo]
        # Solo las liquidaciones que siguen abiertas: una promesa ya cerrada no
        # se vuelve perdida porque la escritura se cayo.
        for hito in negocio.hitos:
            if hito.estado == EstadoNegocio.ACTIVO:
                hito.estado = nuevo

    db.commit()
    db.refresh(movimiento)
    return movimiento
