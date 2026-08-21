"""Tests del semáforo y la bandeja diaria (sprint 20).

La decisión que estos tests protegen es que **`sin_gestion` sea un nivel aparte
y no "crítico"**. Con 194 canjes que nunca se tocaron, meterlos en rojo dejaría
la bandeja con 194 filas rojas y el color no informaría nada.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.services.bandeja_canjes import (
    UMBRAL_ADVERTENCIA,
    UMBRAL_CRITICO,
    clasificar,
    obtener_bandeja,
)

AHORA = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def tipos(db):
    db.add(TipoMovimiento(
        codigo="GESTION_INICIAL", entity_type=EntityType.canje, nombre="Gestión inicial",
        etapa_resultante="EN_REVISION", orden=1, sla_es_habil=False, activo=True,
    ))
    db.commit()
    return db


def _canje(db, id_, estado=CanjeEstado.ACTIVO, etapa=CanjeEtapa.EN_REVISION, dias_atras=30):
    c = Canje(
        id=id_,
        fecha_solicitud=AHORA - timedelta(days=dias_atras),
        estado=estado,
        etapa=etapa,
        comuna="Santiago",
    )
    db.add(c)
    return c


def _movimiento(db, canje_id, horas_atras):
    db.add(Movimiento(
        entity_type=EntityType.canje,
        entity_id=canje_id,
        tipo_movimiento="GESTION_INICIAL",
        fecha=AHORA - timedelta(hours=horas_atras),
        comentario="x",
    ))


# ------------------------------------------------------------ clasificación


@pytest.mark.parametrize(
    "horas, esperado",
    [
        (None, "sin_gestion"),
        (0, "al_dia"),
        (23.9, "al_dia"),
        (24, "advertencia"),
        (47.9, "advertencia"),
        (48, "critico"),
        (500, "critico"),
    ],
)
def test_los_umbrales_son_los_de_config(horas, esperado):
    assert clasificar(horas) == esperado


def test_los_umbrales_son_48_y_24():
    assert (UMBRAL_CRITICO, UMBRAL_ADVERTENCIA) == (48, 24)


def test_sin_gestion_no_es_critico():
    """Nunca tocado y abandonado tres días son problemas distintos."""
    assert clasificar(None) != clasificar(1000)


# ------------------------------------------------------------ bandeja


def test_un_canje_sin_movimientos_queda_sin_gestion(db, tipos):
    _canje(db, 1)
    db.commit()

    b = obtener_bandeja(db, AHORA)

    assert b.resumen.sin_gestion == 1
    assert b.filas[0].nivel == "sin_gestion"
    assert b.filas[0].horas_sin_gestion is None
    assert b.filas[0].ultimo_movimiento is None


def test_el_semaforo_mide_desde_el_ultimo_movimiento(db, tipos):
    _canje(db, 1)
    _canje(db, 2)
    _canje(db, 3)
    db.commit()
    _movimiento(db, 1, horas_atras=2)
    _movimiento(db, 2, horas_atras=30)
    _movimiento(db, 3, horas_atras=100)
    db.commit()

    niveles = {f.canje_id: f.nivel for f in obtener_bandeja(db, AHORA).filas}

    assert niveles == {1: "al_dia", 2: "advertencia", 3: "critico"}


def test_cuenta_desde_el_movimiento_mas_reciente(db, tipos):
    """Un canje viejo con gestión de hoy está al día, no crítico."""
    _canje(db, 1)
    db.commit()
    _movimiento(db, 1, horas_atras=200)
    _movimiento(db, 1, horas_atras=1)
    db.commit()

    fila = obtener_bandeja(db, AHORA).filas[0]

    assert fila.nivel == "al_dia"
    assert fila.horas_sin_gestion == 1.0
    assert fila.ultimo_movimiento_nombre == "Gestión inicial"


def test_los_cancelados_no_son_trabajo_pendiente(db, tipos):
    _canje(db, 1, estado=CanjeEstado.CANCELADO)
    db.commit()

    b = obtener_bandeja(db, AHORA)

    assert b.filas == []


def test_los_activos_con_etapa_cerrada_quedan_fuera(db, tipos):
    """Son 31 en la base real: activos pero con la etapa ya cerrada."""
    _canje(db, 1, etapa=CanjeEtapa.CERRADO)
    _canje(db, 2, etapa=CanjeEtapa.EN_OFERTA)
    db.commit()

    b = obtener_bandeja(db, AHORA)

    assert [f.canje_id for f in b.filas] == [2]


def test_el_orden_pone_primero_lo_que_nunca_se_toco(db, tipos):
    _canje(db, 1)
    _canje(db, 2)
    _canje(db, 3)
    db.commit()
    _movimiento(db, 1, horas_atras=100)  # crítico
    _movimiento(db, 2, horas_atras=30)   # advertencia
    db.commit()                          # el 3 queda sin gestión

    orden = [f.canje_id for f in obtener_bandeja(db, AHORA).filas]

    assert orden == [3, 1, 2]


def test_entre_dos_igual_de_abandonados_va_primero_el_mas_viejo(db, tipos):
    _canje(db, 1, dias_atras=10)
    _canje(db, 2, dias_atras=400)
    db.commit()

    orden = [f.canje_id for f in obtener_bandeja(db, AHORA).filas]

    assert orden == [2, 1]


def test_dentro_de_un_nivel_va_primero_el_mas_abandonado(db, tipos):
    _canje(db, 1)
    _canje(db, 2)
    db.commit()
    _movimiento(db, 1, horas_atras=60)
    _movimiento(db, 2, horas_atras=300)
    db.commit()

    orden = [f.canje_id for f in obtener_bandeja(db, AHORA).filas]

    assert orden == [2, 1], "los dos son críticos; manda quién lleva más tiempo"


def test_el_resumen_cuadra_con_las_filas(db, tipos):
    for i in range(1, 6):
        _canje(db, i)
    db.commit()
    _movimiento(db, 1, horas_atras=1)
    _movimiento(db, 2, horas_atras=30)
    _movimiento(db, 3, horas_atras=100)
    db.commit()

    b = obtener_bandeja(db, AHORA)
    r = b.resumen

    assert (r.al_dia, r.advertencia, r.critico, r.sin_gestion) == (1, 1, 1, 2)
    assert r.requieren_atencion == 4
    assert sum([r.al_dia, r.advertencia, r.critico, r.sin_gestion]) == len(b.filas)


def test_una_bandeja_vacia_no_falla(db, tipos):
    b = obtener_bandeja(db, AHORA)
    assert b.filas == []
    assert b.resumen.requieren_atencion == 0


# ------------------------------------------------------------ endpoint


def test_el_endpoint_devuelve_la_bandeja(cliente, tipos, db):
    _canje(db, 1)
    db.commit()

    r = cliente.get("/api/canjes/bandeja")

    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["umbral_critico_horas"] == 48
    assert datos["umbral_advertencia_horas"] == 24
    assert datos["resumen"]["sin_gestion"] == 1


def test_la_bandeja_no_se_confunde_con_un_id(cliente, tipos):
    """`/canjes/bandeja` va antes de `/canjes/{id}` en el registro de rutas."""
    assert cliente.get("/api/canjes/bandeja").status_code == 200


def test_la_bandeja_exige_sesion(db):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            assert c.get("/api/canjes/bandeja").status_code == 401
    finally:
        app.dependency_overrides.clear()
