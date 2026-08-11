from datetime import datetime

from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento


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
