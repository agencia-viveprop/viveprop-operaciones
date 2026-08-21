"""Tests del CRUD de negocios (sprint 8).

Lo que se fija acá es que los tres sprints anteriores queden bien conectados:
al guardar un hito se congela la UF (sprint 3), se resuelve la base (`D-017`) y
se calculan las comisiones con la fórmula del modelo (sprint 7), en ese orden.

El caso de referencia es VVP-4, que en el Excel da 42.914.480,40 de base y
858.290 de comisión total con la UF del 2026-01-02.
"""
from datetime import date
from decimal import Decimal as D

import pytest

from app.models.catalogo import Catalogo, Etapa

UF_VVP4 = D("39735.63")  # UF del 2026-01-02


@pytest.fixture
def base_negocios(db):
    """Catálogos, etapas y la UF que necesitan los negocios de prueba."""
    from app.models.uf import UFDiaria

    alianza = Catalogo(tipo="alianza", codigo="ASSETPLAN", nombre="Assetplan", orden=1)
    operacion = Catalogo(tipo="tipo_operacion", codigo="VENTA", nombre="Venta", orden=1)
    tipo_prop = Catalogo(tipo="tipo_propiedad", codigo="DEPARTAMENTO", nombre="Departamento", orden=1)
    db.add_all([alianza, operacion, tipo_prop])
    db.add_all([
        Etapa(codigo="E2", nombre="Visita", responsable="COMERCIAL", orden=2),
        Etapa(codigo="E7", nombre="Terminado", responsable="OPERACIONES", orden=7),
    ])
    db.add_all([
        UFDiaria(fecha=date(2026, 1, 2), valor=UF_VVP4),
        UFDiaria(fecha=date(2026, 6, 1), valor=D("40627.62")),
    ])
    db.commit()
    return {"alianza": alianza.id, "operacion": operacion.id, "tipo_prop": tipo_prop.id}


def _payload_vvp4(**extra):
    """VVP-4 real: Assetplan, 1.080 UF, concentradores."""
    cuerpo = {
        "codigo": "VVP-4",
        "modelo": "SECUNDARIO_CONCENTRADORES",
        "propiedad": {
            "direccion": "Mario Kreutzberger 1520",
            "unidad": "316-A",
            "comuna": "San Ramón",
        },
        "vendedor_arrendador": "Assetplan",
        "hitos": [{
            "fecha_inicio": "2026-01-02",
            "estado": "PERDIDO",
            "etapa": "E2",
            "valor_negocio": "1080",
            "moneda": "UF",
            "pct_lado_vendedor": "0.02",
            "pct_lado_comprador": "0.02",
            "pct_rebate_concentrador": "0.12",
            "pct_broker_comprador": "0.012",
            "pct_vp_comprador": "0.008",
            "pct_equipo": "0.10",
        }],
    }
    cuerpo.update(extra)
    return cuerpo


def test_crear_negocio_congela_la_uf_y_calcula_las_comisiones(cliente, base_negocios):
    r = cliente.post("/api/negocios", json=_payload_vvp4())
    assert r.status_code == 201, r.text

    hito = r.json()["hitos"][0]
    assert D(hito["uf_snapshot"]) == UF_VVP4
    assert D(hito["valor_clp_calculado"]) == D("42914480.40")
    assert D(hito["base_comision"]) == D("42914480.40")
    assert D(hito["comision_total"]) == D("858289.61")
    assert D(hito["comision_broker"]) == D("514973.76")
    assert D(hito["comision_vp_bruta"]) == D("343315.84")
    assert D(hito["comision_equipo"]) == D("34331.58")
    assert D(hito["comision_real_vp"]) == D("308984.26")


def test_un_negocio_perdido_no_genera_rebate(cliente, base_negocios):
    """Aunque la tasa del 12% esté registrada, como en los 10 perdidos."""
    hito = cliente.post("/api/negocios", json=_payload_vvp4()).json()["hitos"][0]
    assert D(hito["rebate_concentrador"]) == D("0")


def test_el_mismo_negocio_activo_si_genera_rebate(cliente, base_negocios):
    cuerpo = _payload_vvp4()
    cuerpo["hitos"][0]["estado"] = "ACTIVO"
    hito = cliente.post("/api/negocios", json=cuerpo).json()["hitos"][0]
    # base x pct_lado_vendedor x 12%
    assert D(hito["rebate_concentrador"]) == D("102994.75")
    assert D(hito["comision_real_vp"]) > D(hito["comision_vp_bruta"])


def test_el_valor_manual_le_gana_al_calculado(cliente, base_negocios):
    """El caso VVP-2: la liquidación real fue menor que la regla (D-017)."""
    cuerpo = _payload_vvp4()
    cuerpo["hitos"][0]["valor_clp_manual"] = "20000000"
    cuerpo["hitos"][0]["motivo_valor_manual"] = "Liquidación de Assetplan"

    hito = cliente.post("/api/negocios", json=cuerpo).json()["hitos"][0]

    # El calculado se conserva: comparar los dos es el análisis (D-005).
    assert D(hito["valor_clp_calculado"]) == D("42914480.40")
    assert D(hito["base_comision"]) == D("20000000")
    assert D(hito["comision_total"]) == D("400000.00")


def test_valor_en_clp_no_usa_la_uf(cliente, base_negocios):
    cuerpo = _payload_vvp4()
    cuerpo["hitos"][0].update({"valor_negocio": "50000000", "moneda": "CLP"})

    hito = cliente.post("/api/negocios", json=cuerpo).json()["hitos"][0]

    assert hito["uf_snapshot"] is None
    assert D(hito["valor_clp_calculado"]) == D("50000000")


def test_sin_uf_para_la_fecha_dice_que_hay_que_cargarla(cliente, base_negocios):
    cuerpo = _payload_vvp4()
    cuerpo["hitos"][0]["fecha_inicio"] = "2027-05-05"

    r = cliente.post("/api/negocios", json=cuerpo)

    assert r.status_code == 400
    detalle = r.json()["detail"]
    assert "2027-05-05" in detalle
    assert "cargar" in detalle.lower()


def test_un_negocio_sin_valorizar_deja_las_comisiones_nulas(cliente, base_negocios):
    """Nulo y no cero: distingue "sin valorizar" de "valorizado en cero"."""
    cuerpo = _payload_vvp4()
    cuerpo["hitos"][0].pop("valor_negocio")
    cuerpo["hitos"][0].pop("moneda")

    hito = cliente.post("/api/negocios", json=cuerpo).json()["hitos"][0]

    assert hito["base_comision"] is None
    assert hito["comision_total"] is None
    assert hito["comision_real_vp"] is None


def test_dos_hitos_con_porcentajes_distintos(cliente, base_negocios):
    """VVP-3: mismo valor, 2% en la promesa y 1% en la escritura."""
    cuerpo = {
        "codigo": "VVP-3",
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": "Ladislao Errázuriz 2037", "unidad": "503", "comuna": "Providencia"},
        "hitos": [
            {"nombre": "PROMESA", "fecha_inicio": "2026-01-02", "estado": "CERRADO",
             "valor_negocio": "1000", "moneda": "UF", "pct_lado_vendedor": "0.02",
             "pct_vp_vendedor": "0.01", "pct_equipo": "0.10"},
            {"nombre": "ESCRITURA", "fecha_inicio": "2026-06-01", "estado": "CERRADO",
             "valor_negocio": "1000", "moneda": "UF", "pct_lado_vendedor": "0.01",
             "pct_vp_vendedor": "0.005", "pct_equipo": "0.10"},
        ],
    }
    r = cliente.post("/api/negocios", json=cuerpo)
    assert r.status_code == 201, r.text

    hitos = {h["nombre"]: h for h in r.json()["hitos"]}
    # UF distintas: cada hito se valoriza en su fecha.
    assert D(hitos["PROMESA"]["uf_snapshot"]) == UF_VVP4
    assert D(hitos["ESCRITURA"]["uf_snapshot"]) == D("40627.62")
    assert D(hitos["PROMESA"]["comision_total"]) > D(hitos["ESCRITURA"]["comision_total"])


def test_el_listado_suma_los_hitos_sin_duplicar(cliente, base_negocios):
    cliente.post("/api/negocios", json=_payload_vvp4())

    fila = cliente.get("/api/negocios").json()[0]

    assert fila["cantidad_hitos"] == 1
    assert fila["direccion"] == "Mario Kreutzberger 1520"
    assert D(fila["comision_total"]) == D("858289.61")


def test_la_propiedad_se_reusa_en_el_reintento(cliente, base_negocios):
    """Tres negocios sobre la misma unidad, una sola propiedad."""
    for codigo in ("VVP-4", "VVP-13", "VVP-16"):
        cuerpo = _payload_vvp4(codigo=codigo)
        assert cliente.post("/api/negocios", json=cuerpo).status_code == 201

    props = cliente.get("/api/negocios/propiedades?q=Kreutzberger").json()
    assert len(props) == 1, "la misma unidad no debe duplicarse"

    ids = {n["id"] for n in cliente.get("/api/negocios").json()}
    assert len(ids) == 3


def test_codigo_repetido_da_conflicto(cliente, base_negocios):
    cliente.post("/api/negocios", json=_payload_vvp4())
    r = cliente.post("/api/negocios", json=_payload_vvp4())

    assert r.status_code == 409
    assert "VVP-4" in r.json()["detail"]


def test_no_se_puede_usar_un_catalogo_del_tipo_equivocado(cliente, base_negocios):
    """El costo de la tabla genérica de D-021: lo valida el servicio."""
    cuerpo = _payload_vvp4(alianza_id=base_negocios["operacion"])

    r = cliente.post("/api/negocios", json=cuerpo)

    assert r.status_code == 400
    detalle = r.json()["detail"]
    assert "alianza_id" in detalle and "tipo_operacion" in detalle


def test_etapa_desconocida_dice_cuales_valen(cliente, base_negocios):
    cuerpo = _payload_vvp4()
    cuerpo["hitos"][0]["etapa"] = "E99"

    r = cliente.post("/api/negocios", json=cuerpo)

    assert r.status_code == 400
    assert "E99" in r.json()["detail"]
    assert "E2" in r.json()["detail"]


def test_hay_que_dar_propiedad_por_id_o_por_datos_pero_no_ambos(cliente, base_negocios):
    cuerpo = _payload_vvp4(propiedad_id=1)
    assert cliente.post("/api/negocios", json=cuerpo).status_code == 422


def test_cambiar_el_modelo_recalcula_las_comisiones(cliente, base_negocios):
    """La fórmula depende del modelo, así que cambiarlo cambia los montos."""
    creado = cliente.post("/api/negocios", json=_payload_vvp4()).json()
    antes = D(creado["hitos"][0]["comision_total"])

    r = cliente.patch(f"/api/negocios/{creado['id']}", json={"modelo": "MERCADO_PRIMARIO"})
    assert r.status_code == 200

    despues = D(r.json()["hitos"][0]["comision_total"])
    # En Primario la comisión sale del lado vendedor, no del comprador.
    assert despues == antes, "ambos lados son 0,02 en este caso, así que coincide"
    assert D(r.json()["hitos"][0]["rebate_concentrador"]) == D("0"), "Primario no tiene rebate"


def test_agregar_un_hito_a_un_negocio_existente(cliente, base_negocios):
    creado = cliente.post("/api/negocios", json=_payload_vvp4()).json()

    r = cliente.post(f"/api/negocios/{creado['id']}/hitos", json={
        "nombre": "ESCRITURA", "fecha_inicio": "2026-06-01", "estado": "CERRADO",
        "valor_negocio": "1080", "moneda": "UF", "pct_lado_comprador": "0.02",
        "pct_vp_comprador": "0.008", "pct_equipo": "0.10",
    })
    assert r.status_code == 201, r.text
    assert D(r.json()["uf_snapshot"]) == D("40627.62")

    assert cliente.get("/api/negocios").json()[0]["cantidad_hitos"] == 2


def test_un_hito_de_otro_negocio_no_se_puede_editar(cliente, base_negocios):
    a = cliente.post("/api/negocios", json=_payload_vvp4()).json()
    b = cliente.post("/api/negocios", json=_payload_vvp4(codigo="VVP-13")).json()

    r = cliente.patch(
        f"/api/negocios/{b['id']}/hitos/{a['hitos'][0]['id']}",
        json={"fecha_inicio": "2026-01-02", "estado": "ACTIVO"},
    )
    assert r.status_code == 404
    assert "VVP-13" in r.json()["detail"]


def test_negocio_inexistente_da_404(cliente, base_negocios):
    assert cliente.get("/api/negocios/9999").status_code == 404
