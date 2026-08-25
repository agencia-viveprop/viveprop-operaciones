"""El resumen del dashboard de canjes, y el desglose por etapa y estado.

El bloque «Canjes por etapa» mostraba un solo número por etapa: el total, sin
distinguir los activos de los cancelados. Con 293 cancelados de 297, ese número
era básicamente el conteo de cancelados y no decía nada sobre lo que hay vivo. El
desglose viene ahora en la misma respuesta, para que el selector de la pantalla
filtre sin volver a consultar.
"""
from datetime import datetime, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, OperacionTipo
from app.services.reportes_canjes import ETAPA_LABELS, obtener_resumen_canjes


def _canje(db, id_canje: int, etapa: CanjeEtapa, estado: CanjeEstado, **extra) -> Canje:
    c = Canje(
        id=id_canje,
        fecha_solicitud=datetime(2026, 3, 15, tzinfo=timezone.utc),
        estado=estado,
        etapa=etapa,
        **extra,
    )
    db.add(c)
    return c


@pytest.fixture
def cartera(db):
    """Una cartera con las dos dimensiones cruzadas, y una etapa vacía.

    `EN_REVISION` queda sin ningún canje a propósito: una etapa sin datos tiene
    que aparecer en cero, no desaparecer de la lista, o la pantalla mostraría
    cinco tiles un día y seis al siguiente.
    """
    _canje(db, 1, CanjeEtapa.EN_OFERTA, CanjeEstado.ACTIVO)
    _canje(db, 2, CanjeEtapa.EN_OFERTA, CanjeEstado.CANCELADO)
    _canje(db, 3, CanjeEtapa.EN_OFERTA, CanjeEstado.CANCELADO)
    _canje(db, 4, CanjeEtapa.RECEPCION, CanjeEstado.CANCELADO)
    _canje(db, 5, CanjeEtapa.EN_NEGOCIO, CanjeEstado.ACTIVO)
    _canje(db, 6, CanjeEtapa.CERRADO, CanjeEstado.CANCELADO)
    db.commit()
    return db


def test_cada_etapa_trae_su_total_y_su_desglose(cartera):
    r = obtener_resumen_canjes(cartera)
    por_etiqueta = {e.etiqueta: e for e in r.por_etapa}

    oferta = por_etiqueta["En oferta"]
    assert (oferta.cantidad, oferta.activos, oferta.cancelados) == (3, 1, 2)

    negocio = por_etiqueta["En negocio"]
    assert (negocio.cantidad, negocio.activos, negocio.cancelados) == (1, 1, 0)

    recepcion = por_etiqueta["Recepción"]
    assert (recepcion.cantidad, recepcion.activos, recepcion.cancelados) == (1, 0, 1)


def test_las_seis_etapas_aparecen_siempre_aunque_esten_en_cero(cartera):
    r = obtener_resumen_canjes(cartera)

    assert [e.etiqueta for e in r.por_etapa] == list(ETAPA_LABELS.values())
    vacia = next(e for e in r.por_etapa if e.etiqueta == "En revisión")
    assert (vacia.cantidad, vacia.activos, vacia.cancelados) == (0, 0, 0)


def test_el_desglose_suma_el_total(cartera):
    """Si no sumara, el filtro mostraría menos canjes de los que hay."""
    r = obtener_resumen_canjes(cartera)

    assert sum(e.cantidad for e in r.por_etapa) == r.total == 6
    assert sum(e.activos + e.cancelados for e in r.por_etapa) == r.total
    assert sum(e.cancelados for e in r.por_etapa) == r.cancelados == 4


def test_un_activo_con_la_etapa_cerrada_queda_contado_y_declarado(db):
    """El caso que hace que el desglose no cuadre con el tile de arriba.

    El tile de «Activos» exige `estado = ACTIVO` **y** `etapa != Cerrado`: un canje
    cerrado no está activo, aunque nadie haya actualizado su estado. El desglose
    por etapa, en cambio, cuenta por estado sin más. Entonces un canje en ese
    cruce aparece como activo en la fila «Cerrado» y no en el tile, y la suma da
    uno más.

    En vez de esconder la diferencia, se devuelve cuántos son para que la pantalla
    pueda explicarla. Hoy en producción son cero; el día que alguien cierre un
    canje sin cambiarle el estado, deja de serlo.
    """
    _canje(db, 10, CanjeEtapa.CERRADO, CanjeEstado.ACTIVO)
    _canje(db, 11, CanjeEtapa.EN_OFERTA, CanjeEstado.ACTIVO)
    db.commit()

    r = obtener_resumen_canjes(db)

    assert r.activos_con_etapa_cerrada == 1
    # El tile cuenta uno; el desglose, dos.
    assert r.activos == 1
    assert sum(e.activos for e in r.por_etapa) == 2
    # Y la diferencia es exactamente ese número, que es lo que la deja explicable.
    assert sum(e.activos for e in r.por_etapa) - r.activos == r.activos_con_etapa_cerrada


def test_sin_canjes_el_resumen_no_se_cae(db):
    r = obtener_resumen_canjes(db)

    assert (r.total, r.activos, r.cancelados) == (0, 0, 0)
    assert r.tasa_activos_pct == 0.0
    assert r.activos_con_etapa_cerrada == 0
    # Las seis etapas siguen estando, en cero.
    assert len(r.por_etapa) == 6
    assert all(e.cantidad == 0 for e in r.por_etapa)


def test_el_endpoint_devuelve_el_desglose(cliente, cartera):
    r = cliente.get("/api/canjes/reportes/resumen")

    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert "activos_con_etapa_cerrada" in cuerpo
    oferta = next(e for e in cuerpo["por_etapa"] if e["etiqueta"] == "En oferta")
    assert (oferta["cantidad"], oferta["activos"], oferta["cancelados"]) == (3, 1, 2)


def test_el_resto_del_resumen_sigue_igual(cartera):
    """El cambio es aditivo: los otros bloques del dashboard no se tocaron."""
    _canje(cartera, 20, CanjeEtapa.EN_OFERTA, CanjeEstado.ACTIVO,
           tipo_inmueble="DEPTO", tipo_operacion=OperacionTipo.VENTA)
    cartera.commit()

    r = obtener_resumen_canjes(cartera)

    assert [(x.etiqueta, x.cantidad) for x in r.por_tipo_inmueble] == [("DEPTO", 1)]
    assert [(x.etiqueta, x.cantidad) for x in r.por_operacion] == [("VENTA", 1)]
    assert [x.etiqueta for x in r.por_mes] == ["2026-03"]
