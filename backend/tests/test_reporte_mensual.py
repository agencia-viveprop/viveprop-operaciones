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
from app.models.catalogo import Catalogo, EstadoNegocio, Etapa, ModeloNegocio
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.reporte_mensual import (
    VENTANA_HISTORICO,
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


def test_los_canjes_cerrados_van_por_fecha_de_solicitud(db):
    """Los tres estados con la misma base, para que el apilado cierre.

    **Antes se contaban por fecha de cierre y con `etapa == CERRADO`**, y eso tenia
    dos problemas. Daba 0 en los 46 meses del historico y no podia dar otra cosa:
    esa etapa y esa fecha no coexisten en ninguna fila, porque la fecha es en
    realidad la de cancelacion (`D-070`). Y mezclaba dos granos --mes de cierre
    contra mes de solicitud-- asi que nunca pudo ser un segmento del apilado.

    Cuando haya cierres de verdad va a hacer falta ademas contarlos por mes de
    cierre, que es cuando se gana la comision. Eso llega con el eje de plata.
    """
    _canje(db, 1, datetime(2026, 8, 5, tzinfo=timezone.utc), estado=CanjeEstado.CERRADO)
    _canje(db, 2, datetime(2026, 8, 6, tzinfo=timezone.utc), estado=CanjeEstado.CANCELADO)
    _canje(db, 3, datetime(2026, 8, 7, tzinfo=timezone.utc), estado=CanjeEstado.ACTIVO)

    r = _reporte(db)

    assert r.mes.canjes_cerrados == 1
    assert r.mes.canjes_solicitados == 3
    # La identidad que sostiene el grafico apilado.
    assert r.mes.canjes_solicitados == (
        r.mes.canjes_activos + r.mes.canjes_cerrados + r.mes.canjes_cancelados
    )


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
        "meses_sin_cierres", "meses_con_negocios",
        "serie", "promedio", "tendencias", "es_historico", "inicio_por_dominio",
    }
    assert cuerpo["ventana_meses"] == 6
    # Sin datos, los seis meses de la ventana estan vacios. Es el numero que la
    # pantalla usa para explicar un mes en cero, y antes iba escrito a mano.
    assert cuerpo["meses_con_negocios"] == 6
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
    if ventana == 0:
        # La historica no devuelve cero: se resuelve al largo real de la serie.
        assert r.json()["es_historico"] is True
        assert r.json()["ventana_meses"] >= 1
    else:
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


def test_cuenta_los_meses_vacios_sobre_los_meses_con_negocios(cliente, db):
    """El numero que la pantalla usa para explicar un mes en cero.

    Iba escrito a mano --"4 de 11 meses estuvieron vacios"-- y eso deja de ser
    cierto el mes siguiente sin que nada falle.

    **Y se cuenta sobre los meses en que ya habia negocios**, no sobre el largo de
    la ventana. Los negocios de este caso arrancan en abril, asi que enero,
    febrero y marzo no son meses vacios: son meses sin negocios. Decir "4 de 6"
    los contaria como fracasos.
    """
    _negocio(db, "V-1", [_hito(date(2026, 4, 1), date(2026, 4, 20), real=D("100"))])
    _negocio(db, "V-2", [_hito(date(2026, 6, 1), date(2026, 6, 15), real=D("200"))])

    cuerpo = cliente.get("/api/reportes/mensual?anio=2026&mes=6&ventana=6").json()

    # Abril, mayo y junio. Solo mayo esta vacio.
    assert cuerpo["meses_con_negocios"] == 3
    assert cuerpo["meses_sin_cierres"] == 1

    # Con una ventana de tres da lo mismo: el tramo con negocios es el mismo.
    corto = cliente.get("/api/reportes/mensual?anio=2026&mes=6&ventana=3").json()
    assert corto["meses_con_negocios"] == 3
    assert corto["meses_sin_cierres"] == 1


# ------------------------------------------- la serie mensual de la ventana


def test_la_serie_trae_un_mes_por_cada_mes_de_la_ventana(db):
    """Los meses vacios van en cero, no se omiten.

    Un mes sin cierres es justamente el dato que hay que ver en este negocio, y
    saltearlo dejaria un grafico con seis barras un mes y cinco al siguiente.
    """
    for ventana in (3, 6, 12):
        r = obtener_reporte_mensual(db, 2026, 8, ventana=ventana)
        assert len(r.serie) == ventana == r.meses_con_negocios
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

    campos_neg = {c for c, _, _ in METRICAS_NEGOCIOS}
    campos_can = {c for c, _, _ in METRICAS_CANJES}

    assert campos_neg == {
        # El valor de los negocios --partido por operacion, que no se suman-- y
        # el reparto completo de la comision.
        "valor_venta", "valor_arriendo", "comision_total", "comision_broker", "comision_equipo",
        "comision_tercero", "rebate_concentrador", "comision_real_vp",
        "hitos_cerrados", "negocios_iniciados",
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

    assert [v.metrica for v in r.movil.variaciones] == [n for _, n, _ in METRICAS]


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

    campos = {c for c, _, _ in METRICAS_CANJES}
    assert "canjes_activos" in campos
    assert "canjes_activos" not in {c for c, _, _ in METRICAS_NEGOCIOS}


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
    # Con tres puntos el grado es 1: una curva pasaria por los tres y dejaria de
    # ser una tendencia (`D-089`).
    assert te.grado == 1
    # La recta ajustada pasa por los tres puntos de una serie perfectamente lineal.
    assert te.curva == [D("100.00"), D("200.00"), D("300.00")]


def test_una_serie_que_baja_da_tendencia_a_la_baja(db):
    _negocio(db, "T-4", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("300"))])
    _negocio(db, "T-5", [_hito(date(2026, 5, 1), date(2026, 5, 10), real=D("200"))])
    _negocio(db, "T-6", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("100"))])

    te = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]

    assert te.direccion == "baja"
    assert te.pendiente == D("-100.00")
    assert te.curva == [D("300.00"), D("200.00"), D("100.00")]


def test_una_serie_estable_da_tendencia_plana(db):
    """Debajo del umbral no se llama tendencia: con estos volumenes es ruido."""
    _negocio(db, "T-7", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("1000"))])
    _negocio(db, "T-8", [_hito(date(2026, 5, 1), date(2026, 5, 10), real=D("1010"))])
    _negocio(db, "T-9", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("1005"))])

    te = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]

    assert te.direccion == "plana"


def test_la_curva_no_baja_de_cero(db):
    """Una comision negativa no existe, y dibujarla bajo el eje sugeriria que si.

    La serie 300 / 0 / 0 tiene pendiente tan negativa que la recta ajustada
    cruzaria el eje.
    """
    _negocio(db, "T-10", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("300"))])

    te = obtener_reporte_mensual(db, 2026, 6, ventana=3).tendencias["comision_real_vp"]

    assert te.direccion == "baja"
    assert te.curva[-1] == D("0.00")
    assert all(v >= D("0") for v in te.curva)


def test_sin_datos_la_tendencia_es_plana_y_sin_porcentaje(db):
    te = obtener_reporte_mensual(db, 2026, 8, ventana=6).tendencias["comision_real_vp"]

    assert te.direccion == "plana"
    assert te.pct_por_mes is None, "sin base no hay porcentaje que calcular"
    assert te.curva == [D("0.00")] * 6
    assert te.mostrar is False, "una recta plana se superpone con el promedio"


def test_hay_una_tendencia_por_cada_metrica(db):
    from app.services.reporte_mensual import METRICAS

    r = obtener_reporte_mensual(db, 2026, 8, ventana=6)

    assert set(r.tendencias) == {campo for campo, _, _ in METRICAS}
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
    # Y el grado cambia con la ventana, que es el punto de `D-089`: tres meses dan
    # una recta y seis dan una curva con una inflexion.
    assert (corta.grado, larga.grado) == (1, 2)
    # En la corta el unico cierre es el de junio, asi que sube.
    assert corta.direccion == "sube"
    # En la larga el de enero queda dentro. Con la recta vieja eso alcanzaba para
    # que la tendencia dijera "baja"; con la curva, la pendiente se lee **al final
    # de la ventana**, y ahi lo que hay es el cierre de junio subiendo desde cinco
    # meses en cero. Es la lectura que se buscaba: hacia donde va, no el promedio
    # de la ventana.
    assert larga.direccion == "sube"


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
    """Y promedia desde que el dominio existe, no desde el borde de la ventana.

    El unico canje es de mayo, asi que en una ventana de seis meses que termina en
    junio los cuatro meses anteriores son meses sin programa de canjes, no meses
    con cero solicitudes. El promedio va sobre mayo y junio: 1 entre 2.
    """
    _solicitud(db, 20, date(2026, 5, 3), CanjeEstado.ACTIVO)
    db.commit()

    p = obtener_reporte_mensual(db, 2026, 6, ventana=6).promedio

    assert p.canjes_activos == D("0.50")


# --------------------------------------------------- la ventana historica


def test_la_ventana_historica_arranca_en_el_primer_registro(db):
    """Cero significa "todo": el largo lo decide el dato, no quien pregunta."""
    _solicitud(db, 100, date(2025, 11, 3), CanjeEstado.CANCELADO)
    _negocio(db, "H-1", [_hito(date(2026, 4, 1), date(2026, 4, 10), real=D("500"))])
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 8, ventana=VENTANA_HISTORICO)

    assert r.es_historico is True
    # De noviembre de 2025 a agosto de 2026, los dos extremos incluidos.
    assert r.ventana_meses == 10
    assert len(r.serie) == 10
    assert r.serie[0].etiqueta == "2025-11"
    assert r.serie[-1].etiqueta == "2026-08"


def test_la_historica_toma_el_dominio_mas_viejo_de_los_dos(db):
    """Canjes puede arrancar antes que negocios, o al reves."""
    _solicitud(db, 101, date(2025, 3, 5), CanjeEstado.CANCELADO)
    _negocio(db, "H-2", [_hito(date(2026, 1, 1), date(2026, 1, 10), real=D("100"))])
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 8, ventana=VENTANA_HISTORICO)

    assert r.serie[0].etiqueta == "2025-03"
    assert r.inicio_por_dominio == {"canjes": "2025-03", "negocios": "2026-01"}


def test_sin_ningun_dato_la_historica_no_se_cae(db):
    """Una serie de largo cero romperia el promedio y la tendencia."""
    r = obtener_reporte_mensual(db, 2026, 8, ventana=VENTANA_HISTORICO)

    assert r.ventana_meses == 1
    assert len(r.serie) == 1
    assert r.promedio.comision_real_vp == D("0.00")


def test_las_otras_ventanas_no_son_historicas(db):
    for ventana in (3, 6, 12):
        r = obtener_reporte_mensual(db, 2026, 8, ventana=ventana)
        assert r.es_historico is False
        assert r.ventana_meses == ventana


# ------------------------- el promedio no se diluye con meses sin dominio


def test_el_promedio_historico_arranca_donde_arranca_el_dominio(db):
    """El punto entero de este cambio.

    Canjes existe desde marzo de 2025 y negocios desde junio de 2026. La serie
    historica va de marzo de 2025 a agosto de 2026: 18 meses. Promediar la
    comision sobre esos 18 la reparte entre 15 meses en los que ViveProp no tenia
    ni un negocio cargado, y la deja cinco veces mas baja de lo real. Un mes malo
    se leeria como bueno contra esa referencia.
    """
    _solicitud(db, 102, date(2025, 3, 5), CanjeEstado.CANCELADO)
    _negocio(db, "H-3", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("900"))])
    _negocio(db, "H-4", [_hito(date(2026, 7, 1), date(2026, 7, 10), real=D("300"))])
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 8, ventana=VENTANA_HISTORICO)

    assert r.ventana_meses == 18
    # 1.200 repartidos entre los tres meses de negocios (junio, julio, agosto),
    # no entre los dieciocho de la serie.
    assert r.promedio.comision_real_vp == D("400.00")
    # Y canjes si promedia sobre los dieciocho: existe desde el primero.
    assert r.promedio.canjes_solicitados == (D("1") / 18).quantize(D("0.01"))


def test_la_tendencia_historica_tambien_arranca_ahi(db):
    """Ajustar la recta sobre meses sin dominio describe el nacimiento del
    negocio, no su tendencia."""
    _solicitud(db, 103, date(2025, 3, 5), CanjeEstado.CANCELADO)
    _negocio(db, "H-5", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("300"))])
    _negocio(db, "H-6", [_hito(date(2026, 7, 1), date(2026, 7, 10), real=D("200"))])
    _negocio(db, "H-7", [_hito(date(2026, 8, 1), date(2026, 8, 10), real=D("100"))])
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 8, ventana=VENTANA_HISTORICO)

    te = r.tendencias["comision_real_vp"]
    assert te.puntos == 3, "los tres meses de negocios, no los dieciocho de la serie"
    assert te.direccion == "baja"
    assert te.pendiente == D("-100.00")
    # Canjes si usa la serie completa.
    assert r.tendencias["canjes_solicitados"].puntos == 18


def test_en_una_ventana_corta_el_recorte_no_cambia_nada(db):
    """El recorte solo importa en la historica: en tres, seis o doce meses el
    dominio ya existia en todo el tramo."""
    _negocio(db, "H-8", [_hito(date(2026, 6, 1), date(2026, 6, 10), real=D("600"))])
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 8, ventana=3)

    assert r.tendencias["comision_real_vp"].puntos == 3
    assert r.promedio.comision_real_vp == D("200.00")


def test_los_meses_vacios_se_cuentan_sobre_el_tramo_con_negocios(db):
    """"39 de los ultimos 46 meses estuvieron vacios" seria cierto y engañoso."""
    _solicitud(db, 104, date(2025, 1, 5), CanjeEstado.CANCELADO)
    _negocio(db, "H-9", [_hito(date(2026, 7, 1), date(2026, 7, 10), real=D("100"))])
    db.commit()

    r = obtener_reporte_mensual(db, 2026, 8, ventana=VENTANA_HISTORICO)

    assert r.ventana_meses == 20, "la serie completa"
    # Negocios existe desde julio: dos meses, uno con cierre y uno sin.
    assert r.meses_con_negocios == 2
    assert r.meses_sin_cierres == 1


# --------------------------------------------------------------- endpoint


def test_el_endpoint_acepta_la_ventana_historica(cliente):
    r = cliente.get("/api/reportes/mensual?anio=2026&mes=8&ventana=0")

    assert r.status_code == 200, r.text
    assert r.json()["es_historico"] is True


def test_el_endpoint_sigue_rechazando_una_ventana_invalida(cliente):
    assert cliente.get("/api/reportes/mensual?ventana=5").status_code == 422
    assert cliente.get("/api/reportes/mensual?ventana=-1").status_code == 422


def test_la_venta_y_el_arriendo_no_se_suman(db):
    """Dos negocios cerrados el mismo mes, uno de venta y uno de arriendo.

    En una venta la base es el precio de la propiedad; en un arriendo es **un mes
    de renta**. Son dos ordenes de magnitud de diferencia --en el historico, 1.556
    millones contra 2,3-- asi que sumarlos da el mismo numero sin sentido que hizo
    descartar `valor_prop` en canjes (`D-054`), y en un grafico juntos el arriendo
    es invisible.

    Este test es lo que evita que vuelvan a un solo campo.
    """
    venta = Catalogo(tipo="tipo_operacion", codigo="VENTA", nombre="Venta", orden=1)
    arriendo = Catalogo(tipo="tipo_operacion", codigo="ARRIENDO", nombre="Arriendo", orden=2)
    db.add_all([venta, arriendo])
    db.flush()

    def negocio(codigo, operacion_id, base):
        prop = Propiedad(direccion=f"Calle {codigo}", comuna="Santiago")
        db.add(prop)
        n = Negocio(
            codigo=codigo, modelo=ModeloNegocio.MERCADO_PRIMARIO, propiedad=prop,
            etapa="E5", tipo_operacion_id=operacion_id,
        )
        n.hitos = [
            NegocioHito(
                fecha_inicio=date(2026, 7, 1), fecha_cierre=date(2026, 8, 5),
                estado=EstadoNegocio.CERRADO, valor_clp_calculado=base,
                comision_total=D("1"), comision_real_vp=D("1"),
            )
        ]
        db.add(n)

    negocio("V-1", venta.id, D("240000000"))
    negocio("A-1", arriendo.id, D("1200000"))
    db.commit()

    agosto = _reporte(db).serie[-1]

    assert agosto.etiqueta == "2026-08"
    assert agosto.valor_venta == D("240000000")
    assert agosto.valor_arriendo == D("1200000")


def test_un_negocio_sin_operacion_cae_en_venta(db):
    """Es el caso dominante --17 de 19-- y hoy no hay ninguno asi.

    Lo que se fija es que **no desaparezca**: si cayera afuera de los dos campos,
    su plata se perderia del reporte sin que nada lo dijera.
    """
    prop = Propiedad(direccion="Calle S-1", comuna="Santiago")
    db.add(prop)
    n = Negocio(codigo="S-1", modelo=ModeloNegocio.MERCADO_PRIMARIO, propiedad=prop, etapa="E5")
    n.hitos = [
        NegocioHito(
            fecha_inicio=date(2026, 7, 1), fecha_cierre=date(2026, 8, 5),
            estado=EstadoNegocio.CERRADO, valor_clp_calculado=D("99000000"),
            comision_total=D("1"), comision_real_vp=D("1"),
        )
    ]
    db.add(n)
    db.commit()

    agosto = _reporte(db).serie[-1]
    assert agosto.valor_venta == D("99000000")
    assert agosto.valor_arriendo == D("0")


def test_el_grado_de_la_curva_crece_con_los_puntos():
    """La ventana elegida decide cuantas inflexiones puede mostrar la curva.

    Con techo en 4: cada grado extra es una inflexion mas, y sobre trece meses un
    grado alto sigue el ruido en vez de la forma.
    """
    from app.services.reporte_mensual import _grado_de_tendencia

    assert [_grado_de_tendencia(n) for n in (1, 3, 4)] == [1, 1, 1]
    assert [_grado_de_tendencia(n) for n in (5, 9)] == [2, 2]
    assert [_grado_de_tendencia(n) for n in (10, 23)] == [3, 3]
    assert [_grado_de_tendencia(n) for n in (24, 46, 200)] == [4, 4, 4]


def test_la_curva_reproduce_una_parabola():
    """El ajuste tiene que recuperar la forma cuando la forma existe.

    Nueve puntos de `y = (i-4)**2` y grado 2: si el ajuste esta bien, la curva
    pasa por los nueve. Es el test que caza un error de signo o de escala en las
    ecuaciones normales, que con datos reales pasaria desapercibido.
    """
    from app.services.reporte_mensual import _coeficientes

    ys = [float((i - 4) ** 2) for i in range(9)]
    coef = _coeficientes(ys, 2)
    ts = [(2 * i - 8) / 8 for i in range(9)]
    ajustado = [sum(c * t**k for k, c in enumerate(coef)) for t in ts]

    assert [round(v, 6) for v in ajustado] == ys


def test_una_serie_en_v_termina_subiendo(db):
    """**La diferencia entre la recta y la curva, en un caso.**

    Baja y despues sube con la misma fuerza. La recta ajustada da pendiente casi
    cero y dice "plana"; la curva de grado 2 dice "sube", porque la pendiente se
    lee al final de la ventana y ahi la serie va para arriba.
    """
    valores = (D("500"), D("300"), D("100"), D("100"), D("300"), D("500"))
    for i, valor in enumerate(valores):
        mes = 3 + i
        _negocio(db, f"V-{i}", [_hito(date(2026, mes, 1), date(2026, mes, 10), real=valor)])

    te = obtener_reporte_mensual(db, 2026, 8, ventana=6).tendencias["comision_real_vp"]

    assert te.puntos == 6 and te.grado == 2
    assert te.direccion == "sube"
    assert te.pendiente > D("0")
    # Y la curva tiene forma de V: los extremos por encima del medio.
    assert te.curva[0] > te.curva[2] and te.curva[-1] > te.curva[3]


def test_una_curva_con_forma_se_dibuja_aunque_termine_plana(db):
    """`mostrar` no puede depender solo de la pendiente del final.

    Esta serie sube, hace techo y vuelve al mismo valor: la curva de grado 2
    termina casi horizontal en su vertice, asi que por pendiente diria "plana". Y
    tiene toda la forma que mostrar. Al reves, una recta plana no aporta nada y se
    superpone con la linea del promedio, asi que esa no se dibuja.
    """
    valores = (D("100"), D("300"), D("500"), D("500"), D("300"), D("100"))
    for i, valor in enumerate(valores):
        mes = 3 + i
        _negocio(db, f"P-{i}", [_hito(date(2026, mes, 1), date(2026, mes, 10), real=valor)])

    te = obtener_reporte_mensual(db, 2026, 8, ventana=6).tendencias["comision_real_vp"]

    assert (te.puntos, te.grado) == (6, 2)
    assert te.mostrar is True, "tiene forma de campana, aunque el final sea plano"
    # La forma esta: el medio por encima de los dos extremos.
    assert te.curva[2] > te.curva[0] and te.curva[3] > te.curva[-1]
