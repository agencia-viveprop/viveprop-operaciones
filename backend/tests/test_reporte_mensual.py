"""Tests del reporte mensual comparativo (sprint 17, rediseñado con ventanas).

Tres propiedades:

1. **Un mes sin datos no rompe la comparación.** La variación contra cero no es
   infinito ni cien por ciento: es nulo, porque no hay base contra la que
   comparar. Poner un número ahí sería inventarlo.
2. **La ventana móvil termina en el mes elegido, y su referencia es la anterior
   del mismo largo, sin solaparse.** Si se solaparan, el mismo cierre contaría en
   los dos lados y la variación saldría diluida.
3. **Los bordes entran completos.** Un cierre el día 1 y otro el día 31 son del
   mes; un canje solicitado a las 23:59 del último día también.
"""
from datetime import date, datetime, timezone
from decimal import Decimal as D

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio, Etapa, ModeloNegocio
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.reporte_mensual import (
    METRICAS,
    VENTANAS_VALIDAS,
    correr_meses,
    limites,
    mes_anterior,
    obtener_reporte_mensual,
    rango_anio_corrido,
    rango_ventana,
)

HOY = date(2026, 8, 22)


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


def _reporte(db, anio=2026, mes=8, ventana=6):
    return obtener_reporte_mensual(db, anio, mes, ventana=ventana, hoy=HOY)


def _var(comparacion, metrica="Comisión real ViveProp"):
    return next(v for v in comparacion.variaciones if v.metrica == metrica)


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
    (2026, 1, (2025, 12)),
])
def test_el_mes_anterior_cruza_el_anio(anio, mes, esperado):
    assert mes_anterior(anio, mes) == esperado


@pytest.mark.parametrize("anio, mes, cuantos, esperado", [
    (2026, 8, -1, (2026, 7)),
    (2026, 1, -1, (2025, 12)),      # cruza el año hacia atrás
    (2026, 8, -12, (2025, 8)),
    (2026, 12, 1, (2027, 1)),       # y hacia adelante
    (2026, 8, -6, (2026, 2)),
])
def test_correr_meses_cruza_el_anio(anio, mes, cuantos, esperado):
    assert correr_meses(anio, mes, cuantos) == esperado


# --------------------------------------------------------- ventanas móviles


@pytest.mark.parametrize("meses, esperado", [
    (3, (date(2026, 6, 1), date(2026, 8, 31))),
    (6, (date(2026, 3, 1), date(2026, 8, 31))),
    (12, (date(2025, 9, 1), date(2026, 8, 31))),
])
def test_la_ventana_termina_en_el_mes_elegido(meses, esperado):
    """Una de 6 que termina en agosto arranca el 1 de marzo, no en febrero."""
    assert rango_ventana(2026, 8, meses) == esperado


def test_la_ventana_de_referencia_no_se_solapa(db):
    """Si se solaparan, el mismo cierre contaría en los dos lados."""
    r = _reporte(db, ventana=6)

    assert r.movil.actual.etiqueta == "2026-03 a 2026-08"
    assert r.movil.contra.etiqueta == "2025-09 a 2026-02"


def test_la_ventana_movil_suma_los_meses_vacios_del_medio(db):
    """El punto del rediseño: la serie mensual es ilegible, la ventana no."""
    _negocio(db, "G-1", [_hito(date(2026, 3, 1), date(2026, 3, 10), real=D("100"))])
    # abril, mayo y junio vacíos
    _negocio(db, "G-2", [_hito(date(2026, 7, 1), date(2026, 7, 10), real=D("200"))])

    julio = _reporte(db, 2026, 7, ventana=6)

    # El mes de julio solo ve 200; la ventana ve los dos cierres.
    assert julio.mes.comision_real_vp == D("200")
    assert julio.movil.actual.comision_real_vp == D("300")


def test_la_ventana_se_puede_cambiar(db):
    _negocio(db, "G-1", [_hito(date(2026, 1, 5), date(2026, 1, 20), real=D("500"))])
    _negocio(db, "G-2", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("100"))])

    tres = _reporte(db, ventana=3)
    doce = _reporte(db, ventana=12)

    assert tres.movil.actual.comision_real_vp == D("100")   # solo jun-ago
    assert doce.movil.actual.comision_real_vp == D("600")   # sep-ago, los dos
    assert (tres.ventana_meses, doce.ventana_meses) == (3, 12)


def test_una_ventana_invalida_se_rechaza(db):
    with pytest.raises(ValueError, match="ventana"):
        obtener_reporte_mensual(db, 2026, 8, ventana=5, hoy=HOY)


# ------------------------------------------------------------ año corrido


def test_el_anio_corrido_compara_el_mismo_tramo(db):
    """Enero-agosto contra enero-agosto, no contra el año entero.

    Comparar ocho meses contra doce diría que el año viene mal cuando solo
    viene incompleto.
    """
    assert rango_anio_corrido(2026, 8) == (date(2026, 1, 1), date(2026, 8, 31))

    r = _reporte(db)
    assert r.anio_corrido.actual.etiqueta == "2026-01 a 2026-08"
    assert r.anio_corrido.contra.etiqueta == "2025-01 a 2025-08"


def test_el_anio_corrido_no_arrastra_diciembre_del_anio_pasado(db):
    _negocio(db, "G-1", [_hito(date(2025, 12, 1), date(2025, 12, 20), real=D("999"))])
    _negocio(db, "G-2", [_hito(date(2026, 2, 1), date(2026, 2, 10), real=D("100"))])

    r = _reporte(db)

    assert r.anio_corrido.actual.comision_real_vp == D("100")
    # Diciembre del 2025 cae fuera de los dos tramos (enero-agosto).
    assert r.anio_corrido.contra.comision_real_vp == D("0")


# ------------------------------------------- la variación contra cero


def test_sin_base_la_variacion_es_nula_no_infinita(db):
    """Lo que el criterio del sprint pide: un período vacío no rompe nada."""
    _negocio(db, "G-1", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("500000"))])

    real = _var(_reporte(db).movil)

    assert real.actual == D("500000")
    assert real.referencia == D("0")
    assert real.absoluta == D("500000")
    assert real.pct is None


def test_el_porcentaje_se_calcula_cuando_hay_base(db):
    # Uno en la ventana anterior (sep-feb) y uno en la actual (mar-ago).
    _negocio(db, "G-1", [_hito(date(2025, 10, 1), date(2025, 10, 10), real=D("100000"))])
    _negocio(db, "G-2", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("150000"))])

    assert _var(_reporte(db).movil).pct == D("50.0")


def test_una_caida_da_porcentaje_negativo(db):
    _negocio(db, "G-1", [_hito(date(2025, 10, 1), date(2025, 10, 10), real=D("200000"))])
    _negocio(db, "G-2", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("50000"))])

    assert _var(_reporte(db).movil).pct == D("-75.0")


def test_dos_ventanas_vacias_no_rompen(db):
    """Todo en cero, todas las variaciones nulas, ningún error."""
    r = _reporte(db)

    assert r.mes.comision_real_vp == D("0")
    assert all(v.pct is None for v in r.movil.variaciones)
    assert all(v.absoluta == D("0") for v in r.movil.variaciones)


def test_se_comparan_todas_las_metricas_declaradas(db):
    r = _reporte(db)

    assert len(r.movil.variaciones) == len(METRICAS)
    assert len(r.anio_corrido.variaciones) == len(METRICAS)


# ---------------------------------------------------------- bordes del mes


def test_el_primero_y_el_ultimo_dia_entran(db):
    _negocio(db, "G-1", [_hito(date(2026, 8, 1), date(2026, 8, 1), real=D("100"))])
    _negocio(db, "G-2", [_hito(date(2026, 8, 1), date(2026, 8, 31), real=D("200"))])
    _negocio(db, "G-3", [_hito(date(2026, 9, 1), date(2026, 9, 1), real=D("999"))])

    r = _reporte(db)

    assert r.mes.hitos_cerrados == 2
    assert r.mes.comision_real_vp == D("300")


def test_un_canje_del_ultimo_instante_del_mes_entra(db):
    _canje(db, 1, datetime(2026, 8, 31, 23, 59, tzinfo=timezone.utc))
    _canje(db, 2, datetime(2026, 9, 1, 0, 1, tzinfo=timezone.utc))

    assert _reporte(db).mes.canjes_solicitados == 1


# ------------------------------------------------------------ qué se cuenta


def test_solo_los_cerrados_cuentan_como_cerrados(db):
    _negocio(db, "G-1", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("100"))])
    _negocio(db, "A-1", [_hito(date(2026, 8, 1), None, EstadoNegocio.ACTIVO, real=D("999"))])
    _negocio(db, "P-1", [_hito(date(2026, 8, 1), None, EstadoNegocio.PERDIDO, real=D("999"))])

    r = _reporte(db)

    assert r.mes.hitos_cerrados == 1
    assert r.mes.comision_real_vp == D("100")


def test_un_negocio_con_dos_hitos_se_inicia_una_sola_vez(db):
    """`VVP-3` tiene promesa y escritura: es un negocio, no dos."""
    _negocio(db, "G-1", [
        _hito(date(2026, 8, 5), date(2026, 8, 20), real=D("100"), nombre="PROMESA"),
        _hito(date(2026, 9, 5), date(2026, 9, 20), real=D("200"), nombre="ESCRITURA"),
    ])

    agosto = _reporte(db, 2026, 8)
    septiembre = _reporte(db, 2026, 9)

    assert agosto.mes.negocios_iniciados == 1
    assert septiembre.mes.negocios_iniciados == 0
    # Pero sus liquidaciones sí cuentan cada una en su mes.
    assert (agosto.mes.hitos_cerrados, septiembre.mes.hitos_cerrados) == (1, 1)


def test_los_canjes_cerrados_van_por_fecha_de_cierre(db):
    _canje(db, 1, datetime(2026, 6, 1, tzinfo=timezone.utc),
           etapa=CanjeEtapa.CERRADO, cierre=datetime(2026, 8, 15, tzinfo=timezone.utc))

    r = _reporte(db)

    assert r.mes.canjes_cerrados == 1
    assert r.mes.canjes_solicitados == 0   # se solicitó en junio


def test_los_cancelados_se_cuentan_por_fecha_de_solicitud(db):
    """`canjes` no guarda cuándo se canceló, así que la pregunta que se puede
    responder es "de los que entraron, cuántos terminaron cancelados"."""
    _canje(db, 1, datetime(2026, 8, 5, tzinfo=timezone.utc), estado=CanjeEstado.CANCELADO)
    _canje(db, 2, datetime(2026, 8, 6, tzinfo=timezone.utc), estado=CanjeEstado.ACTIVO)

    r = _reporte(db)

    assert (r.mes.canjes_solicitados, r.mes.canjes_cancelados) == (2, 1)


# ---------------------------------------------------------------- endpoint


def test_el_endpoint_sin_parametros_toma_el_mes_actual(cliente):
    r = cliente.get("/api/reportes/mensual")

    assert r.status_code == 200
    cuerpo = r.json()
    assert set(cuerpo) == {
        "mes", "ventana_meses", "movil", "anio_corrido",
        "meses_sin_cierres", "meses_de_la_ventana",
    }
    assert cuerpo["ventana_meses"] == 6
    # Sin datos, los seis meses de la ventana estan vacios. Es el numero que la
    # pantalla usa para explicar un mes en cero, y antes iba escrito a mano.
    assert cuerpo["meses_de_la_ventana"] == 6
    assert cuerpo["meses_sin_cierres"] == 6


def test_el_endpoint_acepta_un_mes_puntual(cliente, db):
    _negocio(db, "G-1", [_hito(date(2026, 3, 1), date(2026, 3, 10), real=D("777"))])

    r = cliente.get("/api/reportes/mensual", params={"anio": 2026, "mes": 3})

    assert r.status_code == 200
    assert r.json()["mes"]["etiqueta"] == "2026-03"
    assert r.json()["mes"]["comision_real_vp"] == "777.00"


@pytest.mark.parametrize("ventana", VENTANAS_VALIDAS)
def test_el_endpoint_acepta_las_tres_ventanas(cliente, ventana):
    r = cliente.get("/api/reportes/mensual", params={"ventana": ventana})

    assert r.status_code == 200
    assert r.json()["ventana_meses"] == ventana


@pytest.mark.parametrize("params, codigo", [
    ({"anio": 2026}, 400),          # año sin mes
    ({"mes": 3}, 400),              # mes sin año
    ({"anio": 2026, "mes": 13}, 422),
    ({"anio": 2026, "mes": 0}, 422),
    ({"anio": 1999, "mes": 3}, 422),
    ({"ventana": 5}, 422),          # no es 3, 6 ni 12
])
def test_el_endpoint_rechaza_periodos_imposibles(cliente, params, codigo):
    assert cliente.get("/api/reportes/mensual", params=params).status_code == codigo


def test_cuenta_los_meses_vacios_de_su_propia_ventana(cliente, db):
    """El numero que la pantalla usa para explicar un mes en cero.

    Iba escrito a mano --"4 de 11 meses estuvieron vacios"-- y eso deja de ser
    cierto el mes siguiente sin que nada falle. Un dato que envejece mal es peor
    que ninguno, porque nadie se entera de que dejo de valer.
    """
    # Dos cierres dentro de la ventana de seis meses que termina en junio: abril
    # y junio. Quedan cuatro meses sin ningun cierre.
    _negocio(db, "V-1", [_hito(date(2026, 4, 1), date(2026, 4, 20), real=D("100"))])
    _negocio(db, "V-2", [_hito(date(2026, 6, 1), date(2026, 6, 15), real=D("200"))])

    cuerpo = cliente.get("/api/reportes/mensual?anio=2026&mes=6&ventana=6").json()

    assert cuerpo["meses_de_la_ventana"] == 6
    assert cuerpo["meses_sin_cierres"] == 4

    # Y sigue al dia cuando cambia la ventana: en tres meses --abril, mayo,
    # junio-- solo mayo esta vacio.
    corto = cliente.get("/api/reportes/mensual?anio=2026&mes=6&ventana=3").json()
    assert corto["meses_de_la_ventana"] == 3
    assert corto["meses_sin_cierres"] == 1
