"""Fixtures de test.

La base de test es SQLite en memoria y se crean solo las tablas compatibles
(`canjes`, `uf_diaria`): asi se evita `sesiones`, que usa el tipo UUID del
dialecto de Postgres y no tiene equivalente en SQLite.

Importante: nunca se usa el engine de `app.db` -- ese apunta a Neon, y un test
jamas debe escribir ahi.
"""
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

import openpyxl
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.canje import Canje
from app.models.uf import UFDiaria
from app.services.importar_canjes import COLUMNAS_REQUERIDAS


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Canje.__table__.create(engine)
    UFDiaria.__table__.create(engine)
    with Session(engine) as sesion:
        yield sesion


# Valores reales de la serie, tomados de la hoja UF. Son los que usan los
# negocios historicos, asi que sirven para verificar contra la columna AC.
UF_REALES = {
    date(2025, 12, 10): Decimal("39647.42"),
    date(2026, 1, 2): Decimal("39735.63"),
    date(2026, 6, 1): Decimal("40627.62"),
    date(2026, 8, 20): Decimal("40859.28"),
}


@pytest.fixture
def uf_cargada(db):
    db.add_all([UFDiaria(fecha=f, valor=v) for f, v in UF_REALES.items()])
    db.commit()
    return db


def _fila_base(id_canje: int) -> dict:
    """Una fila valida, con los mismos alias que entrega la query de Dataprop."""
    return {
        "ID_CANJE": id_canje,
        "FECHA_SOLICITUD": datetime(2026, 3, 15),
        "FECHA_CIERRE": None,
        "ESTADO": "Activo",
        "ETAPA": "En revisión",
        "NOMBRE_CORREDOR_SOLICITANTE": "Ana Solicitante",
        "NOMBRE_CORREDOR_PROPIETARIO": "Beto Propietario",
        "EMAIL_CORREDOR_SOLICITANTE": "ana@corredora.cl",
        "EMAIL_CORREDOR_PROPIETARIO": "beto@corredora.cl",
        "TIPO_OPERACION": "Venta",
        "TIPO_PROPIEDAD": "DEPTO",
        "COMUNA_PROPIEDAD": "Providencia",
        "DIRECCION_PROPIEDAD": "Ladislao Errazuriz 2037",
        "VALOR_PROP": 6088.44,
        "MONEDA_VALOR": "UF",
        "LINK_PROPIEDAD": "https://app.dataprop.cl/propiedades/1",
    }


@pytest.fixture
def fila():
    return _fila_base


@pytest.fixture
def construir_xlsx():
    """Arma un .xlsx en memoria a partir de una lista de dicts.

    `columnas=None` usa las requeridas; pasar una lista permite simular un
    archivo al que le falta una columna.
    """

    def _construir(filas: list[dict], columnas: list[str] | None = None) -> bytes:
        cols = columnas if columnas is not None else list(COLUMNAS_REQUERIDAS)
        libro = openpyxl.Workbook()
        hoja = libro.active
        hoja.append(cols)
        for f in filas:
            hoja.append([f.get(c) for c in cols])
        buffer = BytesIO()
        libro.save(buffer)
        return buffer.getvalue()

    return _construir
