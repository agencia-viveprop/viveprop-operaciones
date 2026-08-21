"""Tests de la base de cálculo de reportería (sprint 12).

La propiedad que se fija es la de `D-006`: los tres buckets están separados de
forma estructural, no como un filtro que alguien recuerde aplicar. Un negocio
perdido no puede aparecer nunca en lo ganado, y no existe un campo que los sume.
"""
from datetime import date
from decimal import Decimal as D

import pytest

from app.models.catalogo import Catalogo, EstadoNegocio, Etapa, ModeloNegocio
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.reportes_negocios import ResumenNegocios, obtener_resumen_negocios


@pytest.fixture
def cartera(db):
    """Una cartera chica con los tres desenlaces y dos alianzas."""
    assetplan = Catalogo(tipo="alianza", codigo="ASSETPLAN", nombre="Assetplan", orden=1)
    ingevec = Catalogo(tipo="alianza", codigo="INGEVEC", nombre="Ingevec", orden=2)
    db.add_all([assetplan, ingevec])
    db.add_all([
        Etapa(codigo="E2", nombre="Visita", responsable="COMERCIAL", orden=2),
        Etapa(codigo="E5", nombre="Escritura", responsable="OPERACIONES", orden=5),
    ])
    db.flush()

    def negocio(codigo, modelo, alianza, etapa, hitos):
        prop = Propiedad(direccion=f"Calle {codigo}", comuna="Santiago")
        db.add(prop)
        n = Negocio(codigo=codigo, modelo=modelo, propiedad=prop, alianza_id=alianza, etapa=etapa)
        n.hitos = hitos
        db.add(n)
        return n

    def hito(estado, cierre, base, total, real, rebate=D("0"), nombre=None):
        return NegocioHito(
            nombre=nombre,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=cierre,
            estado=estado,
            valor_clp_calculado=base,
            comision_total=total,
            comision_real_vp=real,
            rebate_concentrador=rebate,
        )

    negocio("G-1", ModeloNegocio.MERCADO_PRIMARIO, ingevec.id, "E5", [
        hito(EstadoNegocio.CERRADO, date(2026, 3, 10), D("100000000"), D("4000000"), D("1500000")),
    ])
    # Dos hitos ganados en meses distintos, en el mismo negocio.
    negocio("G-2", ModeloNegocio.MERCADO_PRIMARIO, ingevec.id, "E5", [
        hito(EstadoNegocio.CERRADO, date(2026, 3, 20), D("50000000"), D("1000000"), D("400000"), nombre="PROMESA"),
        hito(EstadoNegocio.CERRADO, date(2026, 4, 5), D("50000000"), D("500000"), D("200000"), nombre="ESCRITURA"),
    ])
    negocio("A-1", ModeloNegocio.SECUNDARIO_CONCENTRADORES, assetplan.id, "E2", [
        hito(EstadoNegocio.ACTIVO, None, D("40000000"), D("800000"), D("400000"), rebate=D("96000")),
    ])
    negocio("P-1", ModeloNegocio.SECUNDARIO_CONCENTRADORES, assetplan.id, "E2", [
        hito(EstadoNegocio.PERDIDO, None, D("30000000"), D("600000"), D("216000")),
    ])
    negocio("P-2", ModeloNegocio.SECUNDARIO_CONCENTRADORES, assetplan.id, "E2", [
        hito(EstadoNegocio.DESISTIDO, None, D("20000000"), D("400000"), D("144000")),
    ])
    db.commit()
    return db


def test_los_tres_buckets_no_se_mezclan(cartera):
    r = obtener_resumen_negocios(cartera)

    assert r.ganado.hitos == 3
    assert r.ganado.comision_real_vp == D("2100000")

    assert r.pipeline.hitos == 1
    assert r.pipeline.comision_real_vp == D("400000")

    # Perdido y desistido van juntos: ninguno entró.
    assert r.potencial_perdido.hitos == 2
    assert r.potencial_perdido.comision_real_vp == D("360000")


def test_no_existe_un_campo_que_los_sume(cartera):
    """Sumar los tres da un número que no significa nada (D-006)."""
    campos = set(ResumenNegocios.model_fields)
    assert "total" not in campos
    assert not any(c.startswith("total_") for c in campos)


def test_los_negocios_se_cuentan_sin_duplicar(cartera):
    """G-2 tiene dos hitos ganados, pero es un solo negocio."""
    r = obtener_resumen_negocios(cartera)
    assert r.ganado.hitos == 3
    assert r.ganado.negocios == 2


def test_el_rebate_va_por_bucket(cartera):
    """Los 96.000 son de un negocio activo, así que no están en lo ganado."""
    r = obtener_resumen_negocios(cartera)
    assert r.ganado.rebate_concentrador == D("0")
    assert r.pipeline.rebate_concentrador == D("96000")


def test_el_mes_es_el_de_cierre_no_el_de_inicio(cartera):
    """Lo que importa es cuándo entró la plata."""
    r = obtener_resumen_negocios(cartera)

    assert [c.etiqueta for c in r.ganado_por_mes] == ["2026-03", "2026-04"]
    marzo = r.ganado_por_mes[0]
    assert marzo.hitos == 2, "G-1 y la promesa de G-2"
    assert marzo.comision_real_vp == D("1900000")


def test_un_hito_ganado_sin_fecha_de_cierre_no_se_pierde(db, cartera):
    prop = Propiedad(direccion="Sin fecha 1", comuna="Santiago")
    db.add(prop)
    n = Negocio(codigo="G-3", modelo=ModeloNegocio.MERCADO_PRIMARIO, propiedad=prop)
    n.hitos = [NegocioHito(
        fecha_inicio=date(2026, 1, 1), fecha_cierre=None, estado=EstadoNegocio.CERRADO,
        valor_clp_calculado=D("1000"), comision_total=D("100"), comision_real_vp=D("50"),
    )]
    db.add(n)
    db.commit()

    r = obtener_resumen_negocios(db)
    etiquetas = [c.etiqueta for c in r.ganado_por_mes]
    assert "Sin fecha" in etiquetas


def test_por_alianza_solo_cuenta_lo_ganado(cartera):
    r = obtener_resumen_negocios(cartera)

    por_alianza = {c.etiqueta: c for c in r.ganado_por_alianza}
    assert set(por_alianza) == {"Ingevec"}, "Assetplan no cerró nada en esta cartera"
    assert por_alianza["Ingevec"].comision_real_vp == D("2100000")


def test_por_modelo_usa_el_valor_del_enum(cartera):
    """No el repr de Python, que sería 'ModeloNegocio.MERCADO_PRIMARIO'."""
    r = obtener_resumen_negocios(cartera)
    assert [c.etiqueta for c in r.ganado_por_modelo] == ["MERCADO_PRIMARIO"]


def test_el_pipeline_se_mira_por_etapa(cartera):
    """Es donde está detenido cada negocio."""
    r = obtener_resumen_negocios(cartera)

    assert [c.etiqueta for c in r.pipeline_por_etapa] == ["E2"]
    assert r.pipeline_por_etapa[0].comision_real_vp == D("400000")


def test_los_hitos_sin_valorizar_se_cuentan_aparte(db, cartera):
    """No son ni ganados ni perdidos en plata: no tienen base todavía."""
    assert obtener_resumen_negocios(db).hitos_sin_valorizar == 0

    prop = Propiedad(direccion="Sin valorizar 1", comuna="Santiago")
    db.add(prop)
    n = Negocio(codigo="N-1", modelo=ModeloNegocio.MERCADO_PRIMARIO, propiedad=prop)
    n.hitos = [NegocioHito(fecha_inicio=date(2026, 1, 1), estado=EstadoNegocio.ACTIVO)]
    db.add(n)
    db.commit()

    r = obtener_resumen_negocios(db)
    assert r.hitos_sin_valorizar == 1
    assert r.pipeline.hitos == 2, "cuenta como hito del pipeline"
    assert r.pipeline.comision_real_vp == D("400000"), "pero no aporta plata"


def test_una_cartera_vacia_devuelve_ceros(db):
    r = obtener_resumen_negocios(db)

    assert r.ganado.hitos == 0
    assert r.ganado.comision_real_vp == D("0")
    assert r.ganado_por_mes == []
    assert r.hitos_sin_valorizar == 0


def test_el_endpoint_expone_el_resumen(cliente, cartera):
    r = cliente.get("/api/negocios/reportes/resumen")
    assert r.status_code == 200

    datos = r.json()
    assert D(datos["ganado"]["comision_real_vp"]) == D("2100000")
    assert D(datos["potencial_perdido"]["comision_real_vp"]) == D("360000")
    assert "total" not in datos


def test_el_resumen_exige_sesion(db):
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            assert c.get("/api/negocios/reportes/resumen").status_code == 401
    finally:
        app.dependency_overrides.clear()
