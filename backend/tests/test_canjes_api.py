"""Tests del listado de canjes y sus filtros.

El filtro por **N° de solicitud** es el que motiva este archivo. Busca por
prefijo y no por igualdad: mientras alguien escribe «364», el «3» y el «36»
tienen que mostrar algo, o la pantalla parpadea en vacio y se lee como que el
canje no existe.
"""
from datetime import datetime, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa

SOLICITUD = datetime(2026, 8, 1, tzinfo=timezone.utc)


@pytest.fixture
def cartera(db):
    """Numeros elegidos para que el prefijo distinga: 36, 364, 3640 y 401."""
    for id_, comuna, estado in (
        (36, "Nunoa", CanjeEstado.ACTIVO),
        (364, "La Florida", CanjeEstado.ACTIVO),
        (3640, "Vitacura", CanjeEstado.CANCELADO),
        (401, "Las Condes", CanjeEstado.ACTIVO),
    ):
        db.add(Canje(
            id=id_, fecha_solicitud=SOLICITUD, estado=estado,
            etapa=CanjeEtapa.EN_REVISION, comuna=comuna,
        ))
    db.commit()
    return db


def _numeros(cliente, **params):
    r = cliente.get("/api/canjes", params=params)
    assert r.status_code == 200, r.text
    return sorted(c["id"] for c in r.json())


def test_sin_filtro_vienen_todos(cliente, cartera):
    assert _numeros(cliente) == [36, 364, 401, 3640]


def test_el_numero_completo_trae_ese_canje(cliente, cartera):
    assert _numeros(cliente, numero="401") == [401]


def test_el_numero_incompleto_busca_por_prefijo(cliente, cartera):
    """Lo que hace que escribir no pase por un vacio intermedio."""
    assert _numeros(cliente, numero="36") == [36, 364, 3640]
    assert _numeros(cliente, numero="364") == [364, 3640]


def test_el_prefijo_no_es_una_busqueda_en_cualquier_posicion(cliente, cartera):
    """«64» no puede traer el 364: en un numero, el prefijo es lo que se recuerda."""
    assert _numeros(cliente, numero="64") == []


def test_se_puede_pegar_la_referencia_con_gato(cliente, cartera):
    """La app escribe las referencias como «#364» en los reportes."""
    assert _numeros(cliente, numero="#364") == [364, 3640]


def test_una_entrada_sin_digitos_no_filtra_nada(cliente, cartera):
    """Mejor mostrar todo que una lista vacia sin explicacion."""
    assert _numeros(cliente, numero="abc") == [36, 364, 401, 3640]


def test_el_numero_se_combina_con_los_otros_filtros(cliente, cartera):
    """Los filtros se suman: si no, elegir dos daria mas resultados que uno."""
    assert _numeros(cliente, numero="36", estado="ACTIVO") == [36, 364]
    assert _numeros(cliente, numero="36", comuna="florida") == [364]
