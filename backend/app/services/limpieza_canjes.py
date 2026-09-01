"""Qué historia de canjes guarda la app, y cómo se borra la que no.

**El corte es una política, no un parámetro de una corrida.** El usuario pidió
sacar definitivamente los canjes anteriores a junio de 2025: son cancelaciones de
2022 a 2025 que no aporta arrastrar. Si el corte viviera solo en el script que
borra, la próxima importación los repondría --el importador crea cualquier canje
cuyo ID no esté en la base-- y el borrado duraría hasta la siguiente carga. Por
eso la constante vive acá y la usan las dos cosas: el borrado y la importación.

**El criterio es la fecha de solicitud, con la de creación como respaldo.** Es
como lo pidió --«fecha de solicitud o creación»-- y cubre el caso de un canje
cargado a mano sin fecha de solicitud. En los datos de hoy no hay ninguno así,
pero el respaldo evita que un nulo lo salve del corte por accidente.

**Los movimientos hay que borrarlos a mano.** `obligaciones.canje_id` tiene
clave foránea con `ON DELETE CASCADE` --y sus avances cuelgan de ella igual-- así
que esos se van solos. `movimientos` no tiene clave foránea: usa
`entity_type` + `entity_id` (`D-002`), que es lo que permite servir a canjes y
negocios con una tabla, y el costo es que la base no puede limpiarlos. Sin este
borrado explícito quedarían movimientos huérfanos apuntando a canjes que ya no
existen, y el reporte semanal los seguiría contando en «Se cayó».
"""
from datetime import date, datetime, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.models.canje import Canje
from app.models.movimiento import EntityType, Movimiento
from app.models.obligacion import Obligacion

# Los canjes anteriores a esta fecha no se guardan: se borran, y la importación
# no los vuelve a crear. Pedido el 2026-08-31 (`D-096`).
CORTE_HISTORICO = date(2025, 6, 1)


def _instante(corte: date) -> datetime:
    """El corte como instante en UTC, para comparar con columnas `timestamptz`."""
    return datetime.combine(corte, datetime.min.time(), tzinfo=timezone.utc)


def es_anterior_al_corte(fecha_solicitud, creado_en, corte: date = CORTE_HISTORICO) -> bool:
    """Si un canje queda fuera por antiguo. La de solicitud manda; la de creación
    es el respaldo cuando la primera no está."""
    referencia = fecha_solicitud or creado_en
    if referencia is None:
        return False
    if referencia.tzinfo is None:
        referencia = referencia.replace(tzinfo=timezone.utc)
    return referencia < _instante(corte)


def canjes_anteriores_al_corte(
    db: Session, corte: date = CORTE_HISTORICO
) -> list[Canje]:
    """Los canjes que el corte deja fuera, del más viejo al más nuevo."""
    limite = _instante(corte)
    return list(
        db.scalars(
            select(Canje)
            .where(
                or_(
                    Canje.fecha_solicitud < limite,
                    Canje.fecha_solicitud.is_(None) & (Canje.creado_en < limite),
                )
            )
            .order_by(Canje.fecha_solicitud, Canje.id)
        )
    )


def borrar_canje(db: Session, canje: Canje) -> tuple[int, int]:
    """Borra un canje con todo lo que le cuelga. **No hace commit.**

    Devuelve cuántos movimientos y cuántas obligaciones se fueron con él, para
    que quien llama pueda informarlo: un borrado silencioso de 182 movimientos es
    justo lo que uno querría haber sabido después.
    """
    movimientos = db.execute(
        delete(Movimiento).where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.entity_id == canje.id,
        )
    ).rowcount
    # Se cuentan antes de borrar el canje: después la cascada ya las llevó.
    obligaciones = len(
        list(db.scalars(select(Obligacion.id).where(Obligacion.canje_id == canje.id)))
    )
    db.delete(canje)
    return movimientos, obligaciones
