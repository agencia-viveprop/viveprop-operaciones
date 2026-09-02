"""Tests de la vista directorio (sprint 18).

La propiedad central: **la proyección no puede presentarse como una cifra.** Con
17 negocios resueltos la tasa de conversión tiene un intervalo de casi 50 puntos,
y un directorio decide plata leyendo esto. Los tests fijan que el rango salga del
margen de error real y que el `n` viaje siempre, para que nadie pueda mostrar el
41% sin el "sobre 17 casos" al lado.

La segunda: **lo que no se puede saber se dice.** No hay forma de proyectar
*cuándo* va a entrar la plata —eso necesita duración de ciclo, que no existe— y
la vista lo declara en vez de rellenarlo con una estimación.
"""
from datetime import date
from decimal import Decimal as D

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, OperacionTipo
from app.models.catalogo import Catalogo, EstadoNegocio, Etapa, ModeloNegocio
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.vista_directorio import obtener_vista_directorio

HOY = date(2026, 8, 22)


@pytest.fixture(autouse=True)
def etapas(db):
    db.add(Etapa(codigo="E5", nombre="Escritura", responsable="OPERACIONES", orden=5))
    db.commit()


def _negocio(db, codigo, hitos, modelo=ModeloNegocio.MERCADO_PRIMARIO, alianza_id=None):
    prop = Propiedad(direccion=f"Calle {codigo}", comuna="Santiago")
    db.add(prop)
    n = Negocio(codigo=codigo, modelo=modelo, propiedad=prop, etapa="E5", alianza_id=alianza_id)
    n.hitos = hitos
    db.add(n)
    db.commit()
    return n


def _hito(estado, real, inicio=date(2026, 1, 10), cierre=None):
    return NegocioHito(
        fecha_inicio=inicio, fecha_cierre=cierre, estado=estado, comision_real_vp=real
    )


def _vista(db, ventana: int = 12):
    # Doce por defecto: es la ventana con la que se escribieron los tests de los
    # buckets, antes de que la ventana fuera elegible.
    return obtener_vista_directorio(db, hoy=HOY, ventana=ventana)


# --------------------------------------------------- los tres buckets


def test_los_tres_buckets_no_se_suman(db):
    """`D-006`: son plata, pero no la misma plata. No existe un total."""
    _negocio(db, "G-1", [_hito(EstadoNegocio.CERRADO, D("1000"), cierre=date(2026, 3, 1))])
    _negocio(db, "A-1", [_hito(EstadoNegocio.ACTIVO, D("500"))])
    _negocio(db, "P-1", [_hito(EstadoNegocio.PERDIDO, D("300"))])

    v = _vista(db)

    assert v.ganado.comision_real_vp == D("1000")
    assert v.pipeline.comision_real_vp == D("500")
    assert v.potencial_perdido.comision_real_vp == D("300")
    assert not hasattr(v, "total")


# ---------------------------------------------------- tasa de conversión


def test_la_conversion_lleva_el_n_a_la_vista(db):
    """Un 50% sobre 2 casos y un 50% sobre 200 se leen igual y no valen lo mismo."""
    _negocio(db, "G-1", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))])
    _negocio(db, "P-1", [_hito(EstadoNegocio.PERDIDO, D("100"))])

    c = _vista(db).conversion

    assert (c.cerrados, c.perdidos, c.n) == (1, 1, 2)
    assert c.tasa_pct == D("50.0")


def test_los_activos_no_entran_en_la_conversion(db):
    """Un negocio abierto todavía no se ganó ni se perdió: contarlo como
    perdido diría que ya fracasó."""
    _negocio(db, "G-1", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))])
    _negocio(db, "A-1", [_hito(EstadoNegocio.ACTIVO, D("999"))])

    c = _vista(db).conversion

    assert c.n == 1
    assert c.tasa_pct == D("100.0")


def test_el_intervalo_es_mas_ancho_con_menos_casos(db):
    """La propiedad que hace honesta a la proyección."""
    for i in range(2):
        _negocio(db, f"G-{i}", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))])
        _negocio(db, f"P-{i}", [_hito(EstadoNegocio.PERDIDO, D("100"))])
    pocos = _vista(db).conversion

    for i in range(2, 25):
        _negocio(db, f"G-{i}", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))])
        _negocio(db, f"P-{i}", [_hito(EstadoNegocio.PERDIDO, D("100"))])
    muchos = _vista(db).conversion

    ancho_pocos = pocos.intervalo_alto_pct - pocos.intervalo_bajo_pct
    ancho_muchos = muchos.intervalo_alto_pct - muchos.intervalo_bajo_pct

    # Misma tasa, 50%, pero con 50 casos el margen se angosta.
    assert pocos.tasa_pct == muchos.tasa_pct == D("50.0")
    assert ancho_muchos < ancho_pocos


def test_sin_negocios_resueltos_no_hay_tasa(db):
    _negocio(db, "A-1", [_hito(EstadoNegocio.ACTIVO, D("500"))])

    v = _vista(db)

    assert v.conversion.n == 0
    assert v.conversion.tasa_pct == D("0")
    assert "no hay tasa de conversión" in v.proyeccion.nota


# ------------------------------------------------------------ proyección


def test_la_proyeccion_es_un_rango_derivado_del_margen(db):
    """Los tres escenarios no son criterios inventados: son el mismo dato con su
    margen de error."""
    _negocio(db, "G-1", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))])
    _negocio(db, "P-1", [_hito(EstadoNegocio.PERDIDO, D("100"))])
    _negocio(db, "A-1", [_hito(EstadoNegocio.ACTIVO, D("1000"))])

    p = _vista(db).proyeccion
    c = _vista(db).conversion

    assert p.pipeline == D("1000")
    assert p.pesimista == (D("1000") * c.intervalo_bajo_pct / 100).quantize(D("1"))
    assert p.esperado == (D("1000") * c.tasa_pct / 100).quantize(D("1"))
    assert p.optimista == (D("1000") * c.intervalo_alto_pct / 100).quantize(D("1"))
    assert p.pesimista < p.esperado < p.optimista


def test_la_proyeccion_dice_que_no_sabe_cuando(db):
    """Sin duración de ciclo no se puede decir *cuándo* entra la plata.

    Los historicos traen la misma fecha de inicio y de cierre, asi que ni un
    negocio aporta duracion. La vista lo declara en vez de estimarlo.
    """
    _negocio(db, "G-1", [
        _hito(EstadoNegocio.CERRADO, D("100"), inicio=date(2026, 3, 1), cierre=date(2026, 3, 1))
    ])
    _negocio(db, "A-1", [_hito(EstadoNegocio.ACTIVO, D("500"))])

    p = _vista(db).proyeccion

    assert p.sin_dato_de_plazo is True
    assert "no dice" in p.nota.lower()
    assert "cuándo" in p.nota


def test_con_duraciones_reales_deja_de_avisar(db):
    """Tres cierres con fechas distintas ya son base para hablar de plazos."""
    for i in range(3):
        _negocio(db, f"G-{i}", [
            _hito(EstadoNegocio.CERRADO, D("100"),
                  inicio=date(2026, 1, 5), cierre=date(2026, 3, 1))
        ])
    _negocio(db, "P-1", [_hito(EstadoNegocio.PERDIDO, D("100"))])

    p = _vista(db).proyeccion

    assert p.sin_dato_de_plazo is False
    assert "no dice" not in p.nota.lower()


# --------------------------------------------------------------- mezcla


def test_la_mezcla_por_alianza_usa_el_nombre_no_el_id(db):
    """Un directorio no lee `alianza_id = 3`."""
    ingevec = Catalogo(tipo="alianza", codigo="INGEVEC", nombre="Ingevec", orden=1)
    db.add(ingevec)
    db.flush()
    _negocio(db, "G-1", [_hito(EstadoNegocio.CERRADO, D("500"), cierre=date(2026, 3, 1))],
             alianza_id=ingevec.id)
    _negocio(db, "G-2", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))])

    etiquetas = {m.etiqueta: m.valor for m in _vista(db).por_alianza}

    assert etiquetas["Ingevec"] == D("500")
    assert etiquetas["Sin alianza"] == D("100")


def test_la_mezcla_va_ordenada_de_mayor_a_menor(db):
    _negocio(db, "G-1", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))],
             modelo=ModeloNegocio.MERCADO_PRIMARIO)
    _negocio(db, "G-2", [_hito(EstadoNegocio.CERRADO, D("900"), cierre=date(2026, 3, 1))],
             modelo=ModeloNegocio.SECUNDARIO_AGENCIA)

    modelos = _vista(db).por_modelo

    assert modelos[0].etiqueta == "SECUNDARIO_AGENCIA"
    assert modelos[0].valor == D("900")


def test_la_mezcla_solo_cuenta_lo_cerrado(db):
    """Es la plata que entró, no la que podría entrar."""
    _negocio(db, "A-1", [_hito(EstadoNegocio.ACTIVO, D("999"))])

    assert _vista(db).por_modelo == []


# ------------------------------------------------------------- ticket


def test_el_ticket_usa_la_mediana_y_muestra_el_rango(db):
    """Con 4x de dispersión, el promedio engaña y la mediana no."""
    for i, monto in enumerate(("100", "200", "5000")):
        _negocio(db, f"G-{i}", [
            _hito(EstadoNegocio.CERRADO, D(monto), cierre=date(2026, 3, 1))
        ])

    t = _vista(db).ticket

    assert t.mediano == D("200")      # la mediana, no el promedio de 1766
    assert (t.minimo, t.maximo, t.n) == (D("100"), D("5000"), 3)


def test_sin_cierres_no_hay_ticket(db):
    _negocio(db, "A-1", [_hito(EstadoNegocio.ACTIVO, D("500"))])

    assert _vista(db).ticket is None


# -------------------------------------------------------------- canjes


def test_los_conteos_de_canjes_van_por_estado_y_reconcilian(db):
    """Los tres estados parten el total, sin condiciones extra.

    Los conteos del periodo tienen que cumplir `solicitados = activos + cerrados +
    cancelados` para poder dibujarse apilados (`D-055`), y eso solo se sostiene si
    la particion es por estado y nada mas.

    **Antes los cerrados se deducian de la etapa**, con "estado activo y etapa
    Cerrado", porque el estado `CERRADO` no existia. Ahora existe y el conteo sale
    de el: un canje puede llegar a la etapa de cierre y caerse igual, y eso es
    exactamente lo que paso 31 veces en el historico.
    """
    db.add_all([
        Canje(id=1, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.ACTIVO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        Canje(id=2, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CERRADO,
              etapa=CanjeEtapa.CERRADO, comuna="Santiago"),
        Canje(id=3, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
    ])
    db.commit()

    c = _vista(db).canjes

    assert c.solicitados_historicos == 3
    assert c.activos_historicos == 1, "solo el que sigue con estado ACTIVO"
    assert c.cerrados_historicos == 1, "el que tiene estado CERRADO"
    # Los tres estados parten el total sin dejar ni repetir ninguno.
    assert c.solicitados == c.activos + c.cerrados + c.cancelados


def test_los_conteos_del_periodo_suman_entre_si(db):
    """`solicitados = activos + cancelados` en la ventana, igual que en la serie."""
    db.add_all([
        Canje(id=10, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.ACTIVO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        Canje(id=11, fecha_solicitud=date(2026, 7, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        # Fuera de la ventana de tres meses que termina en agosto.
        Canje(id=12, fecha_solicitud=date(2026, 1, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
    ])
    db.commit()

    c = _vista(db, ventana=3).canjes

    assert (c.solicitados, c.activos, c.cancelados) == (2, 1, 1)
    assert c.solicitados == c.activos + c.cerrados + c.cancelados
    # El historico si los cuenta todos.
    assert c.solicitados_historicos == 3


def test_la_tasa_de_cierre_de_canjes_va_sobre_los_resueltos(db):
    """Los que siguen abiertos no cuentan ni a favor ni en contra.

    Hoy da cero sobre los datos reales, y es cierto: ningun canje se ha cerrado
    con exito. El test usa un cerrado inventado para verificar que la formula
    funciona el dia que haya uno.
    """
    db.add_all([
        Canje(id=20, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CERRADO,
              etapa=CanjeEtapa.CERRADO, comuna="Santiago"),
        Canje(id=21, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        Canje(id=22, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        Canje(id=23, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.ACTIVO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
    ])
    db.commit()

    c = _vista(db).canjes

    # Tres resueltos: un cerrado y dos cancelados. El cuarto sigue abierto.
    assert c.resueltos_historicos == 3
    assert c.cerrados_historicos == 1
    assert c.tasa_cierre_pct == D("33.3")


def test_sin_canjes_resueltos_la_tasa_es_cero_y_no_falla(db):
    c = _vista(db).canjes

    assert c.resueltos_historicos == 0
    assert c.tasa_cierre_pct == D("0")


def test_los_desgloses_de_canjes_van_de_mayor_a_menor(db):
    """Lo que importa es donde esta el volumen, no el listado completo."""
    db.add_all([
        Canje(id=30 + i, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Las Condes" if i < 3 else "Maipu",
              tipo_operacion=OperacionTipo.VENTA if i < 4 else OperacionTipo.ARRIENDO)
        for i in range(5)
    ])
    db.commit()

    c = _vista(db).canjes

    assert [(x.etiqueta, x.cantidad) for x in c.por_comuna] == [("Las Condes", 3), ("Maipu", 2)]
    assert [(x.etiqueta, x.cantidad) for x in c.por_operacion] == [("VENTA", 4), ("ARRIENDO", 1)]


def test_los_nulos_no_arman_una_categoria_sin_dato(db):
    """Una categoria "Sin dato" grande empuja hacia abajo a las reales."""
    db.add_all([
        Canje(id=40, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago", tipo_inmueble="DEPTO"),
        Canje(id=41, fecha_solicitud=date(2026, 8, 1), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna=None, tipo_inmueble=None),
    ])
    db.commit()

    c = _vista(db).canjes

    assert [x.etiqueta for x in c.por_comuna] == ["Santiago"]
    assert [x.etiqueta for x in c.por_tipo_inmueble] == ["DEPTO"]


# ------------------------------------------------- la ventana y la tendencia


def test_la_ventana_solo_alcanza_lo_temporal(db):
    """Los buckets no se filtran por la ventana, y es deliberado.

    Un negocio abierto esta abierto: no pertenece a un mes. Y una tasa de cierre
    calculada sobre uno o dos casos resueltos daria un intervalo de casi cien
    puntos, que es peor que no darla.
    """
    _negocio(db, "W-1", [_hito(EstadoNegocio.CERRADO, D("500"),
                               inicio=date(2026, 1, 5), cierre=date(2026, 1, 20))])
    _negocio(db, "W-2", [_hito(EstadoNegocio.ACTIVO, D("700"), inicio=date(2026, 8, 1))])

    corta = _vista(db, ventana=3)
    larga = _vista(db, ventana=12)

    # La ventana movil si cambia: el cierre de enero entra en la de doce y no en
    # la de tres.
    assert corta.ventana_movil.comision_real_vp == D("0")
    assert larga.ventana_movil.comision_real_vp == D("500")
    # Los buckets no.
    assert corta.ganado.comision_real_vp == larga.ganado.comision_real_vp == D("500")
    assert corta.pipeline.comision_real_vp == larga.pipeline.comision_real_vp == D("700")


def test_la_serie_y_la_tendencia_siguen_la_ventana(db):
    for ventana in (3, 6, 12):
        v = _vista(db, ventana=ventana)
        assert v.ventana_meses == ventana
        assert len(v.serie) == ventana
        assert all(te.puntos == ventana for te in v.tendencias.values())


def test_la_tendencia_del_directorio_es_la_misma_del_reporte_mensual(db):
    """Se reusa la funcion, no se recalcula: dos versiones divergirian."""
    from app.services.reporte_mensual import obtener_reporte_mensual

    _negocio(db, "W-3", [_hito(EstadoNegocio.CERRADO, D("300"),
                               inicio=date(2026, 6, 1), cierre=date(2026, 6, 10))])
    _negocio(db, "W-4", [_hito(EstadoNegocio.CERRADO, D("900"),
                               inicio=date(2026, 8, 1), cierre=date(2026, 8, 10))])

    v = _vista(db, ventana=6)
    m = obtener_reporte_mensual(db, 2026, 8, ventana=6)

    assert v.tendencias["comision_real_vp"] == m.tendencias["comision_real_vp"]
    assert v.serie == m.serie
    assert v.promedio == m.promedio


def test_una_ventana_invalida_se_rechaza(db):
    import pytest as _pytest

    with _pytest.raises(ValueError, match="ventana"):
        _vista(db, ventana=5)


# ------------------------------------------------------------ endpoint


def test_el_endpoint_responde(cliente, db):
    _negocio(db, "G-1", [_hito(EstadoNegocio.CERRADO, D("100"), cierre=date(2026, 3, 1))])

    r = cliente.get("/api/reportes/directorio")

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ganado"]["comision_real_vp"] == "100.00"
    # El `n` viaja siempre: la tasa no se puede mostrar sin él.
    assert "n" in cuerpo["conversion"]
    assert "nota" in cuerpo["proyeccion"]


def test_una_base_vacia_no_rompe(cliente):
    r = cliente.get("/api/reportes/directorio")

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ticket"] is None
    assert cuerpo["conversion"]["n"] == 0
