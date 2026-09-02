"""Conversion entre UF y CLP con fecha de referencia.

Todo pasa por `valor_uf`: no hay conversion sin fecha. Eso es deliberado -- un
monto en UF sin la fecha a la que se valorizo no se puede llevar a pesos de
forma reproducible, y la reporteria comparativa (D-004) necesita justamente
reproducir el valor de un periodo pasado.

Se usa Decimal en todo el camino. Con float, 1080 x 39735.63 no da exacto y las
comisiones dejarian de cuadrar al peso contra el Excel.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.uf import UFDiaria


class UFNoDisponible(Exception):
    """La serie no tiene valor para esa fecha."""


def valor_uf(db: Session, fecha: date) -> Decimal:
    valor = db.scalar(select(UFDiaria.valor).where(UFDiaria.fecha == fecha))
    if valor is None:
        primera, ultima = rango(db)
        if primera is None:
            raise UFNoDisponible("La serie de UF esta vacia. Hay que cargarla.")
        raise UFNoDisponible(
            f"No hay UF para el {fecha.isoformat()}. La serie va del "
            f"{primera.isoformat()} al {ultima.isoformat()}."
        )
    return Decimal(valor)


def serie_completa(db: Session) -> dict[date, Decimal]:
    """Toda la serie de UF en un diccionario, en una sola consulta.

    Existe para los cálculos que valorizan muchas filas con fechas distintas. El
    caso que la motivó: el reporte por período valoriza cada canje con la UF de
    **su** fecha --la del cierre para un cerrado, la de la solicitud para un
    cancelado (`D-046`)-- así que hay casi una fecha distinta por canje, y el
    reporte los recorre una vez por semana y por mes comparado. Pidiendo la UF de
    a una eran cientos de consultas contra Neon; con la serie en memoria, 252
    filas en una (`D-098`).

    Quien la use tiene que tratar **la ausencia como "no hay UF para ese día"**,
    que es exactamente lo que significa: `valor_uf` busca por fecha exacta y falla
    si no está.
    """
    return {
        fecha: Decimal(valor)
        for fecha, valor in db.execute(select(UFDiaria.fecha, UFDiaria.valor)).all()
    }


def uf_a_clp(db: Session, monto_uf: Decimal | float | int, fecha: date) -> Decimal:
    return Decimal(str(monto_uf)) * valor_uf(db, fecha)


def clp_a_uf(db: Session, monto_clp: Decimal | float | int, fecha: date) -> Decimal:
    return Decimal(str(monto_clp)) / valor_uf(db, fecha)


def rango(db: Session) -> tuple[date | None, date | None]:
    fila = db.execute(select(func.min(UFDiaria.fecha), func.max(UFDiaria.fecha))).one()
    return fila[0], fila[1]


def dias_de_colchon(db: Session, hoy: date) -> int | None:
    """Dias de serie que quedan por delante. Negativo si la serie esta vencida.

    Alimenta el aviso del sprint 5: se avisa con 3 dias o menos (D-008), y se
    alerta distinto si el resultado es negativo, porque ahi las conversiones del
    dia ya no son posibles.
    """
    _, ultima = rango(db)
    if ultima is None:
        return None
    return (ultima - hoy).days
