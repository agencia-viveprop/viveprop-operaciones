from datetime import datetime

from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio


class MovimientoError(Exception):
    pass


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

    if tipo.etapa_resultante is not None:
        canje.etapa = CanjeEtapa(tipo.etapa_resultante)
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

    if tipo.etapa_resultante is not None:
        negocio.etapa = tipo.etapa_resultante

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
