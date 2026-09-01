"""Tests del importador del .xlsx de Dataprop.

El caso que mas importa es `test_la_importacion_no_toca_estado_ni_etapa`: esa
regla es la que protege el trabajo hecho en la app de ser sobreescrito por una
reimportacion, y no hay nada en el esquema que la garantice.
"""
import pytest

from datetime import datetime

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
    assert canje.comision_dataprop is None
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


def test_etapa_vacia_entra_en_revision(db, fila, construir_xlsx):
    """Dataprop manda «Sin etapa» cuando todavia no lo clasifico.

    Entra como **En revision** y no como una etapa propia: que el canje este en
    esta app significa que ViveProp lo tomo, y tomarlo es el inicio de la
    revision. Antes esto creaba una etapa «Recepcion» donde nadie pasaba tiempo
    (`D-081`).
    """
    f = fila(701)
    f["ETAPA"] = None

    importar_canjes(db, construir_xlsx([f]))

    assert db.get(Canje, 701).etapa == CanjeEtapa.EN_REVISION


def test_una_consulta_y_un_commit_para_todo_el_archivo(db, fila, construir_xlsx, monkeypatch):
    """Fija el numero de viajes a la base, que es lo que se vino a arreglar.

    Antes eran dos por fila -un db.get y un db.commit-, o sea ~594 para las 297
    filas del export real. Un test que solo verificara el resultado habria pasado
    igual con la version lenta, asi que se cuentan las llamadas.
    """
    llamadas = {"commit": 0, "get": 0}
    commit_real, get_real = db.commit, db.get
    monkeypatch.setattr(db, "commit", lambda: (llamadas.__setitem__("commit", llamadas["commit"] + 1), commit_real())[1])
    monkeypatch.setattr(db, "get", lambda *a, **k: (llamadas.__setitem__("get", llamadas["get"] + 1), get_real(*a, **k))[1])

    resumen = importar_canjes(db, construir_xlsx([fila(900 + i) for i in range(30)]))

    assert resumen.nuevas == 30
    assert resumen.errores == []
    assert llamadas["commit"] == 1, "un commit para todo el archivo, no uno por fila"
    assert llamadas["get"] == 0, "el chequeo de existencia va en una sola consulta"


def test_un_id_repetido_en_el_archivo_no_rompe_el_lote(db, fila, construir_xlsx):
    """Dos filas con el mismo ID: la segunda actualiza a la primera.

    Sin esto la segunda no encontraria el canje en el mapa, intentaria insertarlo
    de nuevo y haria fallar el commit del lote entero, mandando las 297 filas al
    camino lento por una sola fila repetida.
    """
    primera = fila(950)
    segunda = fila(950)
    segunda["COMUNA_PROPIEDAD"] = "Ñuñoa"

    resumen = importar_canjes(db, construir_xlsx([primera, segunda]))

    assert resumen.errores == []
    # Una alta y una actualizacion, no dos altas ni un error.
    assert (resumen.nuevas, resumen.actualizadas) == (1, 1)
    assert db.get(Canje, 950).comuna == "Ñuñoa"


# --------------------------------------------------------- el corte historico


def test_la_importacion_no_repone_lo_que_el_corte_dejo_fuera(db, fila, construir_xlsx):
    """**Sin esta guarda el borrado dura hasta la próxima carga** (`D-096`).

    El importador crea cualquier canje cuyo ID no esté en la base. Se borraron
    definitivamente los anteriores a junio de 2025, y el export de Dataprop sigue
    trayéndolos: sin el corte acá, volverían a entrar como nuevos y el trabajo se
    desharía solo.
    """
    vieja = dict(fila(301), FECHA_SOLICITUD=datetime(2025, 5, 31))
    nueva = dict(fila(302), FECHA_SOLICITUD=datetime(2025, 6, 1))

    resumen = importar_canjes(db, construir_xlsx([vieja, nueva]))

    assert (resumen.nuevas, resumen.antiguas) == (1, 1)
    assert db.get(Canje, 301) is None, "la anterior al corte no entra"
    assert db.get(Canje, 302) is not None, "la del día del corte sí entra"


def test_las_antiguas_se_cuentan_aparte_de_las_ignoradas(db, fila, construir_xlsx):
    """Son dos razones distintas para no tocar una fila y la pantalla dice las dos.

    `ignoradas` es «esta la gestiona la app, no la piso»; `antiguas` es «esta no
    va a existir nunca». Contarlas juntas dejaría al usuario sin saber por qué su
    archivo de 300 filas cargó 20.
    """
    importar_canjes(db, construir_xlsx([fila(401)]))
    db.get(Canje, 401).gestionado_en_app = True
    db.commit()

    resumen = importar_canjes(
        db,
        construir_xlsx([fila(401), dict(fila(402), FECHA_SOLICITUD=datetime(2024, 1, 1))]),
    )

    assert resumen.ignoradas == 1
    assert resumen.antiguas == 1
    assert resumen.nuevas == 0
