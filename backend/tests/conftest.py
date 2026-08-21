"""Fixtures de test.

La base de test es SQLite en memoria y se crean solo las tablas compatibles
(`canjes`, `uf_diaria`, `catalogos`, `etapas`): asi se evita `sesiones`, que usa
el tipo UUID del dialecto de Postgres y no tiene equivalente en SQLite.

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
from sqlalchemy.pool import StaticPool

from app.models.canje import Canje
from app.models.catalogo import Catalogo, Etapa
from app.models.uf import UFDiaria
from app.services.importar_canjes import COLUMNAS_REQUERIDAS


@pytest.fixture
def db():
    # StaticPool y check_same_thread=False para que la base en memoria sea la
    # misma en todos los hilos: TestClient corre la app en un hilo aparte, y con
    # el pool por defecto abriria una conexion nueva ahi, sin las tablas.
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Canje.__table__.create(engine)
    UFDiaria.__table__.create(engine)
    Catalogo.__table__.create(engine)
    Etapa.__table__.create(engine)
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


@pytest.fixture
def cliente(db):
    """TestClient con la base de test y sin exigir login.

    Se sobreescriben las dos dependencias: `get_db` para que apunte a SQLite en
    memoria en vez de a Neon, y `get_current_user` para no tener que crear una
    sesion real en cada test de endpoint. Los tests que verifican la
    autenticacion en si no usan este fixture.
    """
    from fastapi.testclient import TestClient

    from app.auth import get_current_user
    from app.db import get_db
    from app.main import app
    from app.models.usuario import RolUsuario, Usuario

    usuario = Usuario(
        id=1, email="test@viveprop.com", nombre="Test", password_hash="x", rol=RolUsuario.admin
    )

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def catalogos_sembrados(db):
    """Siembra lo mismo que la migracion c8f2b41d7e05, en chico."""
    db.add_all(
        [
            Catalogo(tipo="alianza", codigo="ASSETPLAN", nombre="Assetplan", orden=1,
                     metadatos={"modelo": "SECUNDARIO_CONCENTRADORES"}),
            Catalogo(tipo="alianza", codigo="INGEVEC", nombre="Ingevec", orden=2,
                     metadatos={"modelo": "MERCADO_PRIMARIO"}),
            Catalogo(tipo="alianza", codigo="ANTIGUA", nombre="Alianza antigua", orden=3,
                     activo=False),
            Catalogo(tipo="tipo_operacion", codigo="VENTA", nombre="Venta", orden=1),
            Catalogo(tipo="tipo_operacion", codigo="ARRIENDO", nombre="Arriendo", orden=2),
        ]
    )
    db.add_all(
        [
            Etapa(codigo="E1", nombre="Calificación del cliente", responsable="COMERCIAL", orden=1),
            Etapa(codigo="E7", nombre="Terminado", responsable="OPERACIONES", orden=7),
        ]
    )
    db.commit()
    return db
