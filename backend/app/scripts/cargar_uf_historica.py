"""Carga la serie de UF de años anteriores desde el SII.

**Por qué hace falta.** La serie cargada empieza el 01-01-2026, y eso alcanzaba
mientras la UF solo servía para valorizar negocios de hoy. Dejó de alcanzar al
valorizar canjes: **178 de los 303 se solicitaron entre 2022 y 2025**, y sin la UF
de su fecha no se pueden convertir a pesos. La alternativa --usar la UF de hoy para
un canje de 2023-- sería valorizarlo con una unidad que nunca tuvo.

Reusa el lector del SII que ya existe: la misma descarga y el mismo parser que la
actualización diaria, apuntados a otro año. El SII publica una página por año y las
de años pasados siguen disponibles.

**No pisa lo que ya está.** Inserta solo las fechas que faltan, así que correrlo dos
veces no cambia nada y no puede sobrescribir un valor cargado antes.

Se corre desde `backend/`:

    python -m app.scripts.cargar_uf_historica 2022 2023 2024 2025
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

RAIZ = Path(__file__).resolve().parent.parent.parent
if not os.environ.get("DATABASE_URL"):
    load_dotenv(RAIZ / ".env")

from app.models.uf import UFDiaria  # noqa: E402
from app.services.uf_sii import descargar, parsear  # noqa: E402


def cargar(db: Session, anio: int) -> tuple[int, int]:
    """Devuelve (insertadas, ya_estaban)."""
    html = descargar(anio)
    if html is None:
        print(f"  {anio}: el SII no tiene página para ese año")
        return (0, 0)

    serie = parsear(html, anio)
    existentes = set(
        db.scalars(
            select(UFDiaria.fecha).where(
                UFDiaria.fecha >= min(serie), UFDiaria.fecha <= max(serie)
            )
        ).all()
    )
    nuevas = [UFDiaria(fecha=f, valor=v) for f, v in sorted(serie.items()) if f not in existentes]
    db.add_all(nuevas)
    db.commit()
    print(f"  {anio}: {len(nuevas)} insertadas, {len(serie) - len(nuevas)} ya estaban")
    return (len(nuevas), len(serie) - len(nuevas))


def main() -> None:
    anios = [int(a) for a in sys.argv[1:]]
    if not anios:
        raise SystemExit("Uso: python -m app.scripts.cargar_uf_historica 2022 2023 2024 2025")

    destino = os.environ["DATABASE_URL"].split("@")[-1].split("/")[0]
    print(f"base: {destino}")
    engine = create_engine(os.environ["DATABASE_URL"])
    total = 0
    with Session(engine) as db:
        for anio in anios:
            insertadas, _ = cargar(db, anio)
            total += insertadas
        primera, ultima = db.scalar(select(UFDiaria.fecha).order_by(UFDiaria.fecha)), db.scalar(
            select(UFDiaria.fecha).order_by(UFDiaria.fecha.desc())
        )
    print(f"total insertadas: {total}")
    print(f"la serie ahora va de {primera} a {ultima}")


if __name__ == "__main__":
    main()
