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
        "serie", "promedio", "tendencias",
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


# ------------------------------------------- la serie mensual de la ventana


def test_la_serie_trae_un_mes_por_cada_mes_de_la_ventana(db):
    """Los meses vacios van en cero, no se omiten.

    Un mes sin cierres es justamente el dato que hay que ver en este negocio, y
    saltearlo dejaria un grafico con seis barras un mes y cinco al siguiente.
    """
    for ventana in (3, 6, 12):
        r = obtener_reporte_mensual(db, 2026, 8, ventana=ventana)
        assert len(r.serie) == ventana == r.meses_de_la_ventana
        assert all(m.hitos_cerrados == 0 for m in r.serie)


def test_la_serie_va_del_mes_mas_viejo_al_mas_nuevo(db):
    """El orden es el del grafico: el tiempo corre hacia la derecha."""
    r = obtener_reporte_mensual(db, 2026, 8, ventana=6)

    assert [m.etiqueta for m in r.serie] == [
        "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08",
    ]


def test_la_serie_termina_en_el_mes_que_se_esta_mirando(db):
    """Es lo que permite leer el mes actual contra los anteriores."""
    r = obtener_reporte_mensual(db, 2026, 5, ventana=3)

    assert [m.etiqueta for m in r.serie] == ["2026-03", "2026-04", "2026-05"]


def test_la_serie_atraviesa_el_cambio_de_ano(db):
    r = obtener_reporte_mensual(db, 2026, 2, ventana=3)

    assert [m.etiqueta for m in r.serie] == ["2025-12", "2026-01", "2026-02"]


def test_cada_mes_de_la_serie_cuenta_lo_que_le_toca(db):
    """El reparto por mes, con dos cierres en meses distintos y uno afuera."""
    _negocio(db, "S-1", [_hito(date(2026, 3, 1), date(2026, 4, 10), real=D("100"))])
    _negocio(db, "S-2", [_hito(date(2026, 5, 1), date(2026, 6, 20), real=D("300"))])
    # Fuera de la ventana de tres meses que termina en junio.
    _negocio(db, "S-3", [_hito(date(2026, 1, 5), date(2026, 1, 30), real=D("999"))])

    r = obtener_reporte_mensual(db, 2026, 6, ventana=3)
    por_mes = {m.etiqueta: m for m in r.serie}

    assert por_mes["2026-04"].hitos_cerrados == 1
    assert por_mes["2026-04"].comision_real_vp == D("100")
    assert por_mes["2026-05"].hitos_cerrados == 0
    assert por_mes["2026-06"].hitos_cerrados == 1
    assert por_mes["2026-06"].comision_real_vp == D("300")
    # El de enero no aparece: no esta en la ventana.
    assert "2026-01" not in por_mes
    assert sum(m.comision_real_vp for m in r.serie) == D("400")


def test_la_serie_coincide_con_la_ventana_movil(db):
    """Los dos calculos son distintos y tienen que dar lo mismo.

    La ventana movil se calcula con un rango unico; la serie, mes por mes y
    agrupando en Python. Que sumen igual es lo que dice que el agrupado no perdio
    ni duplico filas en los bordes de mes.
    """
    _negocio(db, "V-1", [_hito(date(2026, 3, 1), date(2026, 3, 31), real=D("111"))])
    _negocio(db, "V-2", [_hito(date(2026, 4, 1), date(2026, 4, 1), real=D("222"))])
    _negocio(db, "V-3", [_hito(date(2026, 5, 1), date(2026, 5, 31), real=D("333"))])

    r = obtener_reporte_mensual(db, 2026, 5, ventana=3)

    assert sum(m.comision_real_vp for m in r.serie) == r.movil.actual.comision_real_vp
    assert sum(m.hitos_cerrados for m in r.serie) == r.movil.actual.hitos_cerrados
    assert sum(m.negocios_iniciados for m in r.serie) == r.movil.actual.negocios_iniciados


def test_los_meses_sin_cierres_salen_de_la_serie(db):
    """Antes se contaban con un segundo recorrido de la ventana; ahora de la serie."""
    _negocio(db, "C-1", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("100"))])

    r = obtener_reporte_mensual(db, 2026, 6, ventana=3)

    assert r.meses_sin_cierres == 2
    assert r.meses_sin_cierres == sum(1 for m in r.serie if m.hitos_cerrados == 0)


# ------------------------------------------------------------- el promedio


def test_el_promedio_incluye_los_meses_en_cero(db):
    """Excluirlos inflaria la referencia justo en el sentido que hace ver
    retroceso donde no hay: en este negocio un mes vacio es normal."""
    _negocio(db, "P-1", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("300"))])

    r = obtener_reporte_mensual(db, 2026, 6, ventana=3)

    # 300 repartido en tres meses, no en el unico con cierre.
    assert r.promedio.comision_real_vp == D("100.00")


def test_el_promedio_de_una_serie_vacia_es_cero(db):
    r = obtener_reporte_mensual(db, 2026, 8, ventana=3)

    assert r.promedio.comision_real_vp == D("0.00")
    assert r.promedio.hitos_cerrados == 0


def test_el_promedio_dice_de_cuantos_meses_es(db):
    """La etiqueta se muestra en pantalla, asi que tiene que ser cierta."""
    r = obtener_reporte_mensual(db, 2026, 8, ventana=6)

    assert r.promedio.etiqueta == "promedio de 6 meses"


# --------------------------------------------- las metricas por dominio


def test_las_metricas_se_declaran_separadas_por_dominio():
    """La pantalla se separo en dos, y el backend dice cual es de cual.

    Si el frontend tuviera que filtrarlas por nombre, renombrar una metrica
    romperia la separacion sin que nada falle.
    """
    from app.services.reporte_mensual import (
        METRICAS,
        METRICAS_CANJES,
        METRICAS_NEGOCIOS,
    )

    campos_neg = {c for c, _ in METRICAS_NEGOCIOS}
    campos_can = {c for c, _ in METRICAS_CANJES}

    assert campos_neg == {
        "comision_real_vp", "comision_total", "hitos_cerrados", "negocios_iniciados",
    }
    assert campos_can == {
        "canjes_solicitados", "canjes_activos", "canjes_cerrados", "canjes_cancelados",
    }
    # Ningun campo en los dos lados, y juntas son todas.
    assert not (campos_neg & campos_can)
    assert METRICAS == METRICAS_NEGOCIOS + METRICAS_CANJES


def test_las_variaciones_cubren_las_metricas_de_los_dos_dominios(db):
    """La comparacion sigue trayendo todo: la pantalla elige que mostrar."""
    from app.services.reporte_mensual import METRICAS

    r = obtener_reporte_mensual(db, 2026, 8, ventana=3)

    assert [v.metrica for v in r.movil.variaciones] == [n for _, n in METRICAS]


# ------------------------------------------------------- los canjes activos


def _solicitud(db, id_canje, fecha, estado=CanjeEstado.ACTIVO, etapa=CanjeEtapa.EN_REVISION):
    db.add(Canje(
        id=id_canje,
        fecha_solicitud=datetime.combine(fecha, datetime.min.time(), tzinfo=timezone.utc),
        estado=estado,
        etapa=etapa,
        comuna="Santiago",
    ))


def test_los_activos_y_los_cancelados_suman_los_solicitados(db):
    """La identidad que permite dibujarlos apilados.

    El estado de un canje solo tiene dos valores, asi que la suma es exacta. Si
    algun dia se agrega un tercero, este test falla y hay que decidir a que
    segmento va antes de que el grafico empiece a mentir sobre su total.
    """
    _solicitud(db, 1, date(2026, 4, 5), CanjeEstado.ACTIVO)
    _solicitud(db, 2, date(2026, 4, 20), CanjeEstado.CANCELADO)
    _solicitud(db, 3, date(2026, 4, 22), CanjeEstado.CANCELADO)
    _solicitud(db, 4, date(2026, 6, 1), CanjeEstado.ACTIVO)
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 6, ventana=3)
    por_mes = {m.etiqueta: m for m in r.serie}

    abril = por_mes["2026-04"]
    assert (abril.canjes_solicitados, abril.canjes_activos, abril.canjes_cancelados) == (3, 1, 2)
    junio = por_mes["2026-06"]
    assert (junio.canjes_solicitados, junio.canjes_activos, junio.canjes_cancelados) == (1, 1, 0)

    for m in r.serie:
        assert m.canjes_solicitados == m.canjes_activos + m.canjes_cancelados

    # Y tambien en la ventana completa, que se calcula por otro camino.
    v = r.movil.actual
    assert v.canjes_solicitados == v.canjes_activos + v.canjes_cancelados == 4


def test_los_activos_se_cuentan_por_mes_de_solicitud(db):
    """Igual que los cancelados, y por el mismo motivo.

    Un canje activo no tiene fecha propia que lo ubique en un mes: lo unico que
    se sabe es cuando entro. Contarlo en el mes en que entro es lo que hace que
    sume con los cancelados de ese mes.
    """
    _solicitud(db, 10, date(2026, 3, 15), CanjeEstado.ACTIVO)
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 6, ventana=6)
    por_mes = {m.etiqueta: m for m in r.serie}

    assert por_mes["2026-03"].canjes_activos == 1
    assert por_mes["2026-06"].canjes_activos == 0


def test_los_activos_estan_en_las_metricas_de_canjes():
    from app.services.reporte_mensual import METRICAS_CANJES, METRICAS_NEGOCIOS

    campos = {c for c, _ in METRICAS_CANJES}
    assert "canjes_activos" in campos
    assert "canjes_activos" not in {c for c, _ in METRICAS_NEGOCIOS}


# ----------------------------------------------------------- la tendencia


def test_una_serie_que_sube_da_tendencia_al_alza(db):
    """Con un cierre mas grande cada mes, la recta sube."""
    _negocio(db, "T-1", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("100"))])
    _negocio(db, "T-2", [_hito(date(2026, 5, 1), date(2026, 5, 10), real=D("200"))])
    _negocio(db, "T-3", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("300"))])

    te = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]

    assert te.direccion == "sube"
    assert te.pendiente == D("100.00")
    assert te.puntos == 3
    # La recta ajustada pasa por los extremos de una serie perfectamente lineal.
    assert (te.desde, te.hasta) == (D("100.00"), D("300.00"))


def test_una_serie_que_baja_da_tendencia_a_la_baja(db):
    _negocio(db, "T-4", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("300"))])
    _negocio(db, "T-5", [_hito(date(2026, 5, 1), date(2026, 5, 10), real=D("200"))])
    _negocio(db, "T-6", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("100"))])

    te = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]

    assert te.direccion == "baja"
    assert te.pendiente == D("-100.00")
    assert (te.desde, te.hasta) == (D("300.00"), D("100.00"))


def test_una_serie_estable_da_tendencia_plana(db):
    """Debajo del umbral no se llama tendencia: con estos volumenes es ruido."""
    _negocio(db, "T-7", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("1000"))])
    _negocio(db, "T-8", [_hito(date(2026, 5, 1), date(2026, 5, 10), real=D("1010"))])
    _negocio(db, "T-9", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("1005"))])

    te = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]

    assert te.direccion == "plana"


def test_la_recta_no_baja_de_cero(db):
    """Una proyeccion negativa de un conteo o de una comision no existe.

    La serie 300 / 0 / 0 tiene pendiente tan negativa que la recta ajustada
    cruzaria el eje. Dibujarla bajo cero sugeriria comisiones negativas.
    """
    _negocio(db, "T-10", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("300"))])

    te = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]

    assert te.direccion == "baja"
    assert te.hasta == D("0.00")
    assert te.desde >= D("0")


def test_sin_datos_la_tendencia_es_plana_y_sin_porcentaje(db):
    te = obtener_reporte_mensual(db, 2026, 8, ventana=6).tendencias["comision_real_vp"]

    assert te.direccion == "plana"
    assert te.pct_por_mes is None, "sin base no hay porcentaje que calcular"
    assert (te.desde, te.hasta) == (D("0.00"), D("0.00"))


def test_hay_una_tendencia_por_cada_metrica(db):
    from app.services.reporte_mensual import METRICAS

    r = obtener_reporte_mensual(db, 2026, 8, ventana=6)

    assert set(r.tendencias) == {campo for campo, _ in METRICAS}
    # Cada una sabe de que dominio es y sobre cuantos meses se trazo.
    assert all(te.puntos == 6 for te in r.tendencias.values())
    assert r.tendencias["comision_real_vp"].dominio == "negocios"
    assert r.tendencias["canjes_activos"].dominio == "canjes"


def test_la_tendencia_usa_los_meses_de_la_ventana_elegida(db):
    """Cambiar la ventana cambia la tendencia: son horizontes distintos."""
    _negocio(db, "T-11", [_hito(date(2026, 1, 1), date(2026, 1, 10), real=D("900"))])
    _negocio(db, "T-12", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("100"))])

    corta = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]
    larga = obtener_reporte_mensual(db, 2026, 6, ventana=6).tendencias["comision_real_vp"]

    assert corta.puntos == 3
    assert larga.puntos == 6
    # En la corta el unico cierre es el de junio, asi que sube; en la larga el de
    # enero queda dentro y pesa mas, asi que baja.
    assert corta.direccion == "sube"
    assert larga.direccion == "baja"


def test_el_promedio_de_un_conteo_no_se_trunca(db):
    """El bug que este test fija.

    La primera version del promedio casteaba los conteos con `int()`, asi que
    cuatro liquidaciones en seis meses daban un promedio de **cero**. El reporte
    afirmaba que en promedio no se cierra nada habiendo cuatro cierres, y la linea
    de referencia de los canjes activos desaparecia por quedar en cero.

    Un promedio truncado no es un promedio: es un promedio equivocado.
    """
    _negocio(db, "PR-1", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("600"))])
    _negocio(db, "PR-2", [_hito(date(2026, 5, 1), date(2026, 5, 10), real=D("600"))])

    p = obtener_reporte_mensual(db, 2026, 6, ventana=3).promedio

    # Dos cierres en tres meses: 0,67 por mes, no 0.
    assert p.hitos_cerrados == D("0.67")
    assert p.comision_real_vp == D("400.00")


def test_el_promedio_de_los_activos_tampoco_se_trunca(db):
    _solicitud(db, 20, date(2026, 5, 3), CanjeEstado.ACTIVO)
    db.commit()

    p = obtener_reporte_mensual(db, 2026, 6, ventana=6).promedio

    assert p.canjes_activos == D("0.17")
