"""Tests del endpoint de catálogos (sprint 4, especificación en D-021).

Lo que se fija acá: que el front pueda pintar cualquier desplegable desde la API
sin listas hardcodeadas, que los inactivos no se cuelen, y que los enums viajen
junto a los catálogos editables aunque no vivan en la misma tabla.
"""
from app.models.catalogo import EstadoNegocio, ModeloNegocio, TipoCatalogo


def test_devuelve_todos_los_grupos_en_una_llamada(cliente, catalogos_sembrados):
    r = cliente.get("/api/catalogos")
    assert r.status_code == 200
    datos = r.json()

    esperados = {
        "alianzas", "estados_facturacion", "tipos_propiedad", "tipos_operacion",
        "estados_propiedad", "motivos_perdida", "etapas", "modelos_negocio",
        "estados_negocio",
    }
    assert esperados <= datos.keys()


def test_no_devuelve_los_inactivos(cliente, catalogos_sembrados):
    """La alianza dada de baja no debe aparecer en un desplegable."""
    alianzas = cliente.get("/api/catalogos").json()["alianzas"]
    codigos = [a["codigo"] for a in alianzas]

    assert codigos == ["ASSETPLAN", "INGEVEC"]
    assert "ANTIGUA" not in codigos


def test_respeta_el_orden_definido(cliente, catalogos_sembrados):
    ops = cliente.get("/api/catalogos").json()["tipos_operacion"]
    assert [o["codigo"] for o in ops] == ["VENTA", "ARRIENDO"]


def test_la_alianza_trae_su_modelo_en_metadatos(cliente, catalogos_sembrados):
    alianzas = {a["codigo"]: a for a in cliente.get("/api/catalogos").json()["alianzas"]}
    assert alianzas["ASSETPLAN"]["metadatos"]["modelo"] == "SECUNDARIO_CONCENTRADORES"
    assert alianzas["INGEVEC"]["metadatos"]["modelo"] == "MERCADO_PRIMARIO"


def test_las_etapas_traen_su_responsable(cliente, catalogos_sembrados):
    etapas = cliente.get("/api/catalogos").json()["etapas"]
    assert [e["codigo"] for e in etapas] == ["E1", "E7"]
    assert etapas[0]["responsable"] == "COMERCIAL"
    assert etapas[1]["responsable"] == "OPERACIONES"


def test_los_enums_viajan_como_catalogos(cliente, catalogos_sembrados):
    """Modelo y estado son enums (D-021) pero el front los consume igual."""
    datos = cliente.get("/api/catalogos").json()

    modelos = {m["codigo"] for m in datos["modelos_negocio"]}
    assert modelos == {m.value for m in ModeloNegocio}
    assert len(modelos) == 3

    estados = {e["codigo"] for e in datos["estados_negocio"]}
    assert estados == {e.value for e in EstadoNegocio}

    nombres = {m["codigo"]: m["nombre"] for m in datos["modelos_negocio"]}
    assert nombres["SECUNDARIO_CONCENTRADORES"] == "Secundario Concentradores"


def test_motivos_de_perdida_arranca_vacio(cliente, catalogos_sembrados):
    """Por D-023 el catálogo se puebla con lo que se registre, no se inventa."""
    assert cliente.get("/api/catalogos").json()["motivos_perdida"] == []


def test_consulta_de_un_tipo_puntual(cliente, catalogos_sembrados):
    r = cliente.get("/api/catalogos/alianza")
    assert r.status_code == 200
    assert [a["codigo"] for a in r.json()] == ["ASSETPLAN", "INGEVEC"]


def test_tipo_desconocido_dice_cuales_son_validos(cliente, catalogos_sembrados):
    r = cliente.get("/api/catalogos/comunas")
    assert r.status_code == 404
    detalle = r.json()["detail"]
    assert "comunas" in detalle
    for tipo in TipoCatalogo:
        assert tipo.value in detalle


def test_los_catalogos_exigen_sesion(db):
    """Sin el override de autenticación, el endpoint no se puede leer."""
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            assert c.get("/api/catalogos").status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_los_catalogos_traen_su_id(cliente, catalogos_sembrados):
    """Los negocios referencian catálogos por id, no por código.

    Sin el id en la respuesta, el formulario del sprint 9 no puede traducir la
    alianza elegida a `alianza_id`.
    """
    alianzas = cliente.get("/api/catalogos").json()["alianzas"]
    assert all(isinstance(a["id"], int) for a in alianzas)

    por_tipo = cliente.get("/api/catalogos/alianza").json()
    assert por_tipo[0]["id"] == alianzas[0]["id"]


def test_los_grupos_que_salen_de_un_enum_no_traen_id(cliente, catalogos_sembrados):
    """Modelo y estado no son filas de tabla, así que no tienen id."""
    datos = cliente.get("/api/catalogos").json()
    assert all(m["id"] is None for m in datos["modelos_negocio"])
    assert all(e["id"] is None for e in datos["estados_negocio"])
