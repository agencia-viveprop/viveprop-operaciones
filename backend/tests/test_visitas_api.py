"""Tests del módulo de visitas: importar, listar, borrar de a una y vaciar.

No hay ID en el archivo de origen, así que la identidad de una visita entre
cargas la arma Propiedad + Cliente + RUT + Fecha/hora solicitada. El foco acá
es: si hay un error no se escribe nada; reimportar la misma fila actualiza en
vez de duplicar; y Etapa/Corredor sí se actualizan porque son los datos que
avanzan con el tiempo.
"""
from io import BytesIO

import openpyxl

from app.services.importar_visitas import COLUMNAS_REQUERIDAS

FILA_OK = {
    "Propiedad": "OP 14671 · Eco Vista · Los Carrera 1131 · Copiapó · DP 1207",
    "Dirección": "Los Carrera 1131, Copiapó",
    "Tipo": "Usada",
    "Mercado": "Mercado secundario",
    "Cliente": "Franco Carozzi",
    "RUT": "11111111",
    "Objetivo de compra": None,
    "Fecha/hora solicitada": "2026-09-14T16:12:00",
    "Etapa": "Solicitada",
    "Corredor": "María Teresa Zegers Silva",
    "Solicitada el": "2026-09-07T13:23:53",
}


def _xlsx(filas: list[dict], columnas: list[str] | None = None) -> bytes:
    cols = columnas if columnas is not None else list(COLUMNAS_REQUERIDAS)
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(cols)
    for f in filas:
        hoja.append([f.get(c) for c in cols])
    buffer = BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def _subir(cliente, contenido: bytes):
    return cliente.post(
        "/api/visitas/importar",
        files={"archivo": ("visitas.xlsx", contenido, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )


def test_importa_todas_las_filas_validas(cliente):
    r = _subir(cliente, _xlsx([FILA_OK, {**FILA_OK, "Cliente": "Marisol Mendoza"}]))
    assert r.status_code == 200, r.text
    assert r.json() == {"nuevas": 2, "actualizadas": 0, "errores": []}

    listado = cliente.get("/api/visitas").json()
    assert len(listado) == 2
    assert {v["cliente"] for v in listado} == {"Franco Carozzi", "Marisol Mendoza"}


def test_cargar_el_mismo_archivo_dos_veces_no_duplica(cliente):
    """La clave es Propiedad + Cliente + RUT + Fecha/hora solicitada: sin
    ningún cambio en esos cuatro datos, la segunda carga actualiza la misma
    fila en vez de crear otra."""
    _subir(cliente, _xlsx([FILA_OK]))
    r = _subir(cliente, _xlsx([FILA_OK]))

    assert r.json() == {"nuevas": 0, "actualizadas": 1, "errores": []}
    listado = cliente.get("/api/visitas").json()
    assert len(listado) == 1


def test_reimportar_actualiza_etapa_y_corredor(cliente):
    """Son los dos datos que avanzan con el tiempo para la misma solicitud."""
    _subir(cliente, _xlsx([FILA_OK]))
    _subir(cliente, _xlsx([{**FILA_OK, "Etapa": "Confirmada", "Corredor": "Otro Corredor"}]))

    listado = cliente.get("/api/visitas").json()
    assert len(listado) == 1
    assert listado[0]["etapa"] == "Confirmada"
    assert listado[0]["corredor"] == "Otro Corredor"


def test_una_fecha_distinta_es_una_visita_nueva(cliente):
    """Cambiar cualquiera de los cuatro datos de la clave es otra solicitud."""
    _subir(cliente, _xlsx([FILA_OK]))
    _subir(cliente, _xlsx([{**FILA_OK, "Fecha/hora solicitada": "2026-09-20T10:00:00"}]))

    assert len(cliente.get("/api/visitas").json()) == 2


def test_una_fila_con_propiedad_vacia_no_escribe_nada(cliente):
    r = _subir(cliente, _xlsx([FILA_OK, {**FILA_OK, "Propiedad": None}]))
    assert r.status_code == 200, r.text
    resumen = r.json()
    assert resumen["nuevas"] == 0
    assert resumen["actualizadas"] == 0
    assert len(resumen["errores"]) == 1

    assert cliente.get("/api/visitas").json() == []


def test_archivo_sin_las_columnas_esperadas_es_rechazado(cliente):
    r = _subir(cliente, _xlsx([FILA_OK], columnas=["Propiedad", "Cliente"]))
    assert r.status_code == 400


def test_eliminar_una_visita(cliente):
    _subir(cliente, _xlsx([FILA_OK, {**FILA_OK, "Cliente": "Marisol Mendoza"}]))
    listado = cliente.get("/api/visitas").json()
    a_borrar = next(v["id"] for v in listado if v["cliente"] == "Franco Carozzi")

    r = cliente.delete(f"/api/visitas/{a_borrar}")
    assert r.status_code == 204

    restante = cliente.get("/api/visitas").json()
    assert len(restante) == 1
    assert restante[0]["cliente"] == "Marisol Mendoza"


def test_eliminar_una_visita_inexistente_da_404(cliente):
    r = cliente.delete("/api/visitas/999")
    assert r.status_code == 404


def test_vaciar_todas_las_visitas(cliente):
    _subir(cliente, _xlsx([FILA_OK, {**FILA_OK, "Cliente": "Marisol Mendoza"}]))

    r = cliente.delete("/api/visitas")
    assert r.status_code == 200
    assert r.json() == {"eliminadas": 2}

    assert cliente.get("/api/visitas").json() == []


def test_vaciar_y_recargar_el_mismo_archivo_repone_todo(cliente):
    """Es la garantía que hace segura la acción: reimportar repone lo mismo."""
    contenido = _xlsx([FILA_OK, {**FILA_OK, "Cliente": "Marisol Mendoza"}])
    _subir(cliente, contenido)
    cliente.delete("/api/visitas")

    r = _subir(cliente, contenido)
    assert r.json() == {"nuevas": 2, "actualizadas": 0, "errores": []}
    assert len(cliente.get("/api/visitas").json()) == 2


def test_vaciar_con_la_tabla_vacia_no_falla(cliente):
    r = cliente.delete("/api/visitas")
    assert r.status_code == 200
    assert r.json() == {"eliminadas": 0}
