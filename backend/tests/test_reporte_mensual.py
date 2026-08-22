"""Tests del reporte mensual comparativo (sprint 17).

La propiedad que el criterio del sprint nombra: **un mes sin datos no rompe la
comparación**. Concretamente, la variación contra cero no es infinito ni cien por
ciento: es nulo, porque no hay base contra la que comparar. Poner un número ahí
sería inventarlo.

La segunda: **los bordes del mes entran completos**. Un cierre el día 1 y otro el
día 31 son del mes; un canje solicitado a las 23:59 del último día también.
"""
from datetime import date, datetime, timezone
from decimal import Decimal as D

import pytest
from sqlalchemy import select

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio, Etapa, ModeloNegocio
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.reporte_mensual import (
    METRICAS,
    limites,
    mes_anterior,
    obtener_reporte_mensual,
)

HOY = date(2026, 8, 21)


@pytest.fixture(autouse=True)
def etapas(db):
    db.add(Etapa(codigo="E5", nombre="Escritura", responsable="OPERACIONES", orden=5))
    db.commit()


def _negocio(db, codigo, hitos):
    prop = Propiedad(direccion=f"Calle {codigo}", comuna="Santiago")
    db.add(prop)
    n = Negocio(codigo=codigo, modelo=ModeloNegocio.MERCADO_PRIMARIO, propiedad=prop, etapa="E5")
    n.hitos = hitos
    db.add(n)
    db.commit()
    return n


def _hito(inicio, cierre=None, estado=EstadoNegocio.CERRADO, real=D("0"), total=D("0"), nombre=None):
    return NegocioHito(
        nombre=nombre, fecha_inicio=inicio, fecha_cierre=cierre, estado=estado,
        comision_real_vp=real, comision_total=total,
    )


def _canje(db, id_, solicitud, estado=CanjeEstado.ACTIVO, etapa=CanjeEtapa.EN_REVISION, cierre=None):
    db.add(Canje(id=id_, fecha_solicitud=solicitud, fecha_cierre=cierre,
                 estado=estado, etapa=etapa, comuna="Santiago"))
    db.commit()


# ------------------------------------------------------------- calendario


@pytest.mark.parametrize("anio, mes, esperado", [
    (2026, 8, (date(2026, 8, 1), date(2026, 8, 31))),
    (2026, 2, (date(2026, 2, 1), date(2026, 2, 28))),   # no bisiesto
    (2024, 2, (date(2024, 2, 1), date(2024, 2, 29))),   # bisiesto
    (2026, 4, (date(2026, 4, 1), date(2026, 4, 30))),
])
def test_los_limites_del_mes(anio, mes, esperado):
    assert limites(anio, mes) == esperado


@pytest.mark.parametrize("anio, mes, esperado", [
    (2026, 8, (2026, 7)),
    (2026, 1, (2025, 12)),   # el de enero es diciembre del anio pasado
])
def test_el_mes_anterior_cruza_el_anio(anio, mes, esperado):
    assert mes_anterior(anio, mes) == esperado


def test_en_enero_las_dos_referencias_son_distintas(db):
    """Enero se compara con diciembre del anio pasado y con enero del anterior."""
    r = obtener_reporte_mensual(db, 2026, 1)

    assert r.mes.etiqueta == "2026-01"
    assert r.mes_anterior.contra.etiqueta == "2025-12"
    assert r.mismo_mes_anio_anterior.contra.etiqueta == "2025-01"


# ------------------------------------------- la variacion contra cero


def test_sin_base_la_variacion_es_nula_no_infinita(db):
    """Lo que el criterio del sprint pide: un mes vacio no rompe nada."""
    _negocio(db, "G-1", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("500000"))])

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)
    real = next(v for v in r.mes_anterior.variaciones if v.metrica == "Comisión real ViveProp")

    assert real.actual == D("500000")
    assert real.referencia == D("0")
    assert real.absoluta == D("500000")
    assert real.pct is None


def test_el_porcentaje_se_calcula_cuando_hay_base(db):
    _negocio(db, "G-1", [_hito(date(2026, 7, 1), date(2026, 7, 10), real=D("100000"))])
    _negocio(db, "G-2", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("150000"))])

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)
    real = next(v for v in r.mes_anterior.variaciones if v.metrica == "Comisión real ViveProp")

    assert real.pct == D("50.0")


def test_una_caida_da_porcentaje_negativo(db):
    _negocio(db, "G-1", [_hito(date(2026, 7, 1), date(2026, 7, 10), real=D("200000"))])
    _negocio(db, "G-2", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("50000"))])

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)
    real = next(v for v in r.mes_anterior.variaciones if v.metrica == "Comisión real ViveProp")

    assert real.pct == D("-75.0")


def test_dos_meses_vacios_no_rompen(db):
    """Todo en cero, todas las variaciones nulas, ningun error."""
    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)

    assert r.mes.comision_real_vp == D("0")
    assert all(v.pct is None for v in r.mes_anterior.variaciones)
    assert all(v.absoluta == D("0") for v in r.mes_anterior.variaciones)


def test_se_comparan_todas_las_metricas_declaradas(db):
    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)

    assert len(r.mes_anterior.variaciones) == len(METRICAS)
    assert len(r.mismo_mes_anio_anterior.variaciones) == len(METRICAS)


# ---------------------------------------------------- bordes del mes


def test_el_primero_y_el_ultimo_dia_entran(db):
    _negocio(db, "G-1", [_hito(date(2026, 8, 1), date(2026, 8, 1), real=D("100"))])
    _negocio(db, "G-2", [_hito(date(2026, 8, 1), date(2026, 8, 31), real=D("200"))])
    # Y el dia siguiente no.
    _negocio(db, "G-3", [_hito(date(2026, 9, 1), date(2026, 9, 1), real=D("999"))])

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)

    assert r.mes.hitos_cerrados == 2
    assert r.mes.comision_real_vp == D("300")


def test_un_canje_del_ultimo_instante_del_mes_entra(db):
    _canje(db, 1, datetime(2026, 8, 31, 23, 59, tzinfo=timezone.utc))
    _canje(db, 2, datetime(2026, 9, 1, 0, 1, tzinfo=timezone.utc))

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)

    assert r.mes.canjes_solicitados == 1


# ------------------------------------------------------- que se cuenta


def test_solo_los_cerrados_cuentan_como_cerrados(db):
    _negocio(db, "G-1", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("100"))])
    _negocio(db, "A-1", [_hito(date(2026, 8, 1), None, EstadoNegocio.ACTIVO, real=D("999"))])
    _negocio(db, "P-1", [_hito(date(2026, 8, 1), None, EstadoNegocio.PERDIDO, real=D("999"))])

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)

    assert r.mes.hitos_cerrados == 1
    assert r.mes.comision_real_vp == D("100")


def test_un_negocio_con_dos_hitos_se_inicia_una_sola_vez(db):
    """`VVP-3` tiene promesa y escritura: es un negocio, no dos."""
    _negocio(db, "G-1", [
        _hito(date(2026, 8, 5), date(2026, 8, 20), real=D("100"), nombre="PROMESA"),
        _hito(date(2026, 9, 5), date(2026, 9, 20), real=D("200"), nombre="ESCRITURA"),
    ])

    agosto = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)
    septiembre = obtener_reporte_mensual(db, 2026, 9, hoy=HOY)

    # Cae en agosto, el mes de su hito mas antiguo, y no se repite en septiembre.
    assert agosto.mes.negocios_iniciados == 1
    assert septiembre.mes.negocios_iniciados == 0
    # Pero sus liquidaciones si cuentan cada una en su mes.
    assert (agosto.mes.hitos_cerrados, septiembre.mes.hitos_cerrados) == (1, 1)


def test_los_canjes_cerrados_van_por_fecha_de_cierre(db):
    _canje(db, 1, datetime(2026, 6, 1, tzinfo=timezone.utc),
           etapa=CanjeEtapa.CERRADO, cierre=datetime(2026, 8, 15, tzinfo=timezone.utc))

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)

    assert r.mes.canjes_cerrados == 1
    # Se solicito en junio, no en agosto.
    assert r.mes.canjes_solicitados == 0


def test_los_cancelados_se_cuentan_por_fecha_de_solicitud(db):
    """`canjes` no guarda cuando se cancelo, asi que la pregunta que se puede
    responder es "de los que entraron este mes, cuantos terminaron cancelados"."""
    _canje(db, 1, datetime(2026, 8, 5, tzinfo=timezone.utc), estado=CanjeEstado.CANCELADO)
    _canje(db, 2, datetime(2026, 8, 6, tzinfo=timezone.utc), estado=CanjeEstado.ACTIVO)

    r = obtener_reporte_mensual(db, 2026, 8, hoy=HOY)

    assert (r.mes.canjes_solicitados, r.mes.canjes_cancelados) == (2, 1)


# ------------------------------------------------------------ endpoint


def test_el_endpoint_sin_parametros_toma_el_mes_actual(cliente):
    r = cliente.get("/api/reportes/mensual")

    assert r.status_code == 200
    cuerpo = r.json()
    assert set(cuerpo) == {"mes", "mes_anterior", "mismo_mes_anio_anterior"}


def test_el_endpoint_acepta_un_mes_puntual(cliente, db):
    _negocio(db, "G-1", [_hito(date(2026, 3, 1), date(2026, 3, 10), real=D("777"))])

    r = cliente.get("/api/reportes/mensual", params={"anio": 2026, "mes": 3})

    assert r.status_code == 200
    assert r.json()["mes"]["etiqueta"] == "2026-03"
    assert r.json()["mes"]["comision_real_vp"] == "777.00"


@pytest.mark.parametrize("params, codigo", [
    ({"anio": 2026}, 400),          # anio sin mes
    ({"mes": 3}, 400),              # mes sin anio
    ({"anio": 2026, "mes": 13}, 422),
    ({"anio": 2026, "mes": 0}, 422),
    ({"anio": 1999, "mes": 3}, 422),
])
def test_el_endpoint_rechaza_periodos_imposibles(cliente, params, codigo):
    assert cliente.get("/api/reportes/mensual", params=params).status_code == codigo
