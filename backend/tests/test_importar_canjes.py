"""Tests del importador del .xlsx de Dataprop.

El caso que mas importa es `test_la_importacion_no_toca_estado_ni_etapa`: esa
regla es la que protege el trabajo hecho en la app de ser sobreescrito por una
reimportacion, y no hay nada en el esquema que la garantice.
"""
import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
from app.services.importar_canjes import COLUMNAS_REQUERIDAS, importar_canjes


def test_importa_filas_nuevas_y_mapea_los_campos(db, fila, construir_xlsx):
    resumen = importar_canjes(db, construir_xlsx([fila(101), fila(102)]))

    assert (resumen.nuevas, resumen.actualizadas, resumen.ignoradas) == (2, 0, 0)
    assert resumen.errores == []

    canje = db.get(Canje, 101)
    assert canje.estado == CanjeEstado.ACTIVO
    assert canje.etapa == CanjeEtapa.EN_REVISION
    assert canje.tipo_operacion == OperacionTipo.VENTA
    assert canje.moneda_valor == MonedaTipo.UF
    assert float(canje.valor_prop) == 6088.44
    assert canje.comuna == "Providencia"
    assert canje.fecha_solicitud.date().isoformat() == "2026-03-15"
    # Lo que Dataprop no provee queda vacio, no en cero.
    assert canje.valor_negocio is None
    assert canje.comision_dbrokers is None
    # Una fila importada no esta gestionada en la app.
    assert canje.gestionado_en_app is False


def test_reimportar_actualiza_las_no_gestionadas(db, fila, construir_xlsx):
    importar_canjes(db, construir_xlsx([fila(201)]))

    f = fila(201)
    f["COMUNA_PROPIEDAD"] = "Nunoa"
    resumen = importar_canjes(db, construir_xlsx([f]))

    assert (resumen.nuevas, resumen.actualizadas, resumen.ignoradas) == (0, 1, 0)
    assert db.get(Canje, 201).comuna == "Nunoa"


def test_no_toca_los_canjes_gestionados_en_la_app(db, fila, construir_xlsx):
    importar_canjes(db, construir_xlsx([fila(301)]))
    canje = db.get(Canje, 301)
    canje.gestionado_en_app = True
    canje.comuna = "Comuna puesta a mano"
    db.commit()

    f = fila(301)
    f["COMUNA_PROPIEDAD"] = "Comuna del archivo"
    resumen = importar_canjes(db, construir_xlsx([f]))

    assert (resumen.nuevas, resumen.actualizadas, resumen.ignoradas) == (0, 0, 1)
    assert db.get(Canje, 301).comuna == "Comuna puesta a mano"


def test_la_importacion_no_toca_estado_ni_etapa(db, fila, construir_xlsx):
    """Estado y etapa los gobierna la app, no el archivo."""
    importar_canjes(db, construir_xlsx([fila(401)]))
    canje = db.get(Canje, 401)
    canje.estado = CanjeEstado.CANCELADO
    canje.etapa = CanjeEtapa.EN_NEGOCIO
    db.commit()

    f = fila(401)
    f["ESTADO"] = "Activo"
    f["ETAPA"] = "Sin etapa"
    resumen = importar_canjes(db, construir_xlsx([f]))

    assert resumen.actualizadas == 1
    canje = db.get(Canje, 401)
    assert canje.estado == CanjeEstado.CANCELADO
    assert canje.etapa == CanjeEtapa.EN_NEGOCIO


def test_falta_una_columna_requerida(db, fila, construir_xlsx):
    sin_estado = [c for c in COLUMNAS_REQUERIDAS if c != "ESTADO"]

    with pytest.raises(ValueError) as exc:
        importar_canjes(db, construir_xlsx([fila(501)], columnas=sin_estado))

    assert "ESTADO" in str(exc.value)
    assert db.get(Canje, 501) is None


def test_una_fila_invalida_no_frena_a_las_demas(db, fila, construir_xlsx):
    mala = fila(601)
    mala["ESTADO"] = "Pendiente de revision"  # no existe en el mapa
    buena = fila(602)

    resumen = importar_canjes(db, construir_xlsx([mala, buena]))

    assert resumen.nuevas == 1
    assert len(resumen.errores) == 1
    assert "ESTADO" in resumen.errores[0]
    assert db.get(Canje, 601) is None
    assert db.get(Canje, 602) is not None


def test_etapa_vacia_cae_en_sin_etapa(db, fila, construir_xlsx):
    f = fila(701)
    f["ETAPA"] = None

    importar_canjes(db, construir_xlsx([f]))

    assert db.get(Canje, 701).etapa == CanjeEtapa.SIN_ETAPA
