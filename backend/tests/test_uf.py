"""Tests de la conversion UF <-> CLP.

Los montos esperados no son inventados: son la columna AC del Excel de
operaciones para negocios reales. Si estos tests pasan, la conversion reproduce
los valores historicos al peso, que es el criterio de listo del sprint 3.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.services.uf import (
    UFNoDisponible,
    clp_a_uf,
    dias_de_colchon,
    rango,
    uf_a_clp,
    valor_uf,
)


@pytest.mark.parametrize(
    "negocio, monto_uf, fecha, clp_esperado",
    [
        ("VVP-4", Decimal("1080"), date(2026, 1, 2), Decimal("42914480.40")),
        ("VVP-1", Decimal("3348"), date(2025, 12, 10), Decimal("132739562.16")),
        ("VVP-2", Decimal("2625.65"), date(2025, 12, 10), Decimal("104100248.323")),
        ("VVP-19 arriendo", Decimal("27"), date(2026, 6, 1), Decimal("1096945.74")),
    ],
)
def test_reproduce_los_valores_del_excel(uf_cargada, negocio, monto_uf, fecha, clp_esperado):
    assert uf_a_clp(uf_cargada, monto_uf, fecha) == clp_esperado


def test_la_ida_y_vuelta_no_pierde_precision(uf_cargada):
    f = date(2026, 1, 2)
    assert clp_a_uf(uf_cargada, uf_a_clp(uf_cargada, Decimal("1080"), f), f) == Decimal("1080")


def test_valor_uf_devuelve_el_valor_exacto(uf_cargada):
    assert valor_uf(uf_cargada, date(2026, 1, 2)) == Decimal("39735.63")


def test_fecha_fuera_de_la_serie_avisa_el_rango(uf_cargada):
    with pytest.raises(UFNoDisponible) as exc:
        valor_uf(uf_cargada, date(2020, 1, 1))
    mensaje = str(exc.value)
    assert "2020-01-01" in mensaje
    assert "2025-12-10" in mensaje  # primera de la serie cargada
    assert "2026-08-20" in mensaje  # ultima


def test_serie_vacia_pide_cargarla(db):
    with pytest.raises(UFNoDisponible) as exc:
        valor_uf(db, date(2026, 1, 2))
    assert "vacia" in str(exc.value)


def test_rango_de_la_serie(uf_cargada):
    assert rango(uf_cargada) == (date(2025, 12, 10), date(2026, 8, 20))


def test_colchon_positivo_cuando_queda_serie(uf_cargada):
    assert dias_de_colchon(uf_cargada, date(2026, 8, 17)) == 3


def test_colchon_negativo_cuando_la_serie_vencio(uf_cargada):
    """El caso de alerta, distinto del aviso: ya no hay UF para hoy."""
    assert dias_de_colchon(uf_cargada, date(2026, 8, 25)) == -5


def test_colchon_es_none_si_no_hay_serie(db):
    assert dias_de_colchon(db, date(2026, 8, 20)) is None
