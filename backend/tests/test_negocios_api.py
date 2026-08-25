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
        "etapa": "E2",
        "hitos": [{
            "fecha_inicio": "2026-01-02",
            "estado": "PERDIDO",
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
            {"nombre": "PROMESA", "fecha_inicio": "2026-01-02", "fecha_cierre": "2026-03-01", "estado": "CERRADO",
             "valor_negocio": "1000", "moneda": "UF", "pct_lado_vendedor": "0.02",
             "pct_vp_vendedor": "0.01", "pct_equipo": "0.10"},
            {"nombre": "ESCRITURA", "fecha_inicio": "2026-06-01", "fecha_cierre": "2026-07-01", "estado": "CERRADO",
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
    # El hito de VVP-4 está PERDIDO, así que su plata va a "no concretada" y no
    # se cuela en las otras dos columnas.
    assert D(fila["comision_no_concretada"]) == D("308984.26")
    assert D(fila["comision_ganada"]) == D("0")
    assert D(fila["comision_pipeline"]) == D("0")


def test_el_listado_no_mezcla_lo_ganado_con_lo_potencial(cliente, base_negocios):
    """La promesa ganada y la escritura abierta, en el mismo negocio.

    Es el caso que rompía la versión anterior: había un solo par de columnas que
    sumaba todas las liquidaciones del negocio, así que este negocio mostraba
    plata efectiva y plata potencial en la misma cifra. No se notaba con los
    datos de hoy --los negocios abiertos no tienen cerradas encima-- y es el
    caso normal en cuanto uno cierre una promesa.
    """
    cuerpo = _payload_vvp4()
    promesa = dict(cuerpo["hitos"][0], nombre="PROMESA", estado="CERRADO",
                   fecha_cierre="2026-02-01")
    escritura = dict(cuerpo["hitos"][0], nombre="ESCRITURA", estado="ACTIVO")
    cuerpo["hitos"] = [promesa, escritura]
    assert cliente.post("/api/negocios", json=cuerpo).status_code == 201

    fila = cliente.get("/api/negocios").json()[0]
    assert fila["cantidad_hitos"] == 2
    # Mismos datos en las dos, y aun así el monto es más alto que el del test de
    # arriba: ahí la liquidación estaba PERDIDA y una perdida no genera rebate
    # del concentrador. Sirve de comprobación cruzada de que cada columna está
    # leyendo el hito de su propio estado y no repartiendo un total.
    assert D(fila["comision_ganada"]) == D("411979.01")
    assert D(fila["comision_pipeline"]) == D("411979.01")
    assert D(fila["comision_no_concretada"]) == D("0")


def test_el_filtro_por_estado_no_cambia_los_montos(cliente, base_negocios):
    """Filtrar decide qué negocios se ven, no qué plata se suma.

    Antes las dos cosas estaban enredadas: el filtro elegía los negocios y las
    columnas sumaban todo, así que el total al pie de la tabla cambiaba de
    significado según el filtro puesto. Ahora cada columna dice lo mismo con
    cualquier filtro, y el que suma es quien lee.
    """
    cuerpo = _payload_vvp4()
    promesa = dict(cuerpo["hitos"][0], nombre="PROMESA", estado="CERRADO",
                   fecha_cierre="2026-02-01")
    escritura = dict(cuerpo["hitos"][0], nombre="ESCRITURA", estado="ACTIVO")
    cuerpo["hitos"] = [promesa, escritura]
    cliente.post("/api/negocios", json=cuerpo)

    completo = cliente.get("/api/negocios").json()[0]
    filtrado = cliente.get("/api/negocios?estado=ACTIVO").json()[0]

    for campo in ("comision_ganada", "comision_pipeline", "comision_no_concretada"):
        assert filtrado[campo] == completo[campo]


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
    """La etapa es del negocio, no del hito (D-027)."""
    cuerpo = _payload_vvp4(etapa="E99")

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
        "nombre": "ESCRITURA", "fecha_inicio": "2026-06-01", "fecha_cierre": "2026-07-01", "estado": "CERRADO",
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


# ------------------------------- el cierre va junto con el estado
#
# Dos inconsistencias silenciosas que la API dejaba pasar. Un hito CERRADO sin
# fecha suma en el bucket de ganado --que filtra por estado-- pero no aparece en
# ningun mes, porque toda la reporteria mensual agrupa por `fecha_cierre`: la
# plata existiria y no estaria en ninguna parte. Y un hito perdido con fecha de
# cierre es la contradiccion que la migracion d1f4a72b6e59 limpio en 12 filas.


def _payload_hito(**extra):
    base = {"fecha_inicio": "2026-01-02", "estado": "ACTIVO"}
    return base | extra


def test_un_hito_cerrado_sin_fecha_se_rechaza(cliente, catalogos_sembrados, uf_cargada):
    r = cliente.post("/api/negocios", json={
        "codigo": "VVP-CERRADO-SIN-FECHA",
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": "Calle 1", "comuna": "Santiago"},
        "hitos": [_payload_hito(estado="CERRADO")],
    })

    assert r.status_code == 422
    assert "fecha de cierre" in r.text


@pytest.mark.parametrize("estado", ["ACTIVO", "PERDIDO", "DESISTIDO"])
def test_un_hito_no_cerrado_no_puede_traer_fecha_de_cierre(
    cliente, catalogos_sembrados, uf_cargada, estado
):
    r = cliente.post("/api/negocios", json={
        "codigo": f"VVP-{estado}",
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": "Calle 2", "comuna": "Santiago"},
        "hitos": [_payload_hito(estado=estado, fecha_cierre="2026-03-01")],
    })

    assert r.status_code == 422
    assert "no puede tener fecha de cierre" in r.text


def test_la_fecha_de_cierre_no_puede_ser_anterior_al_inicio(
    cliente, catalogos_sembrados, uf_cargada
):
    r = cliente.post("/api/negocios", json={
        "codigo": "VVP-AL-REVES",
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": "Calle 3", "comuna": "Santiago"},
        "hitos": [_payload_hito(estado="CERRADO", fecha_cierre="2025-12-01")],
    })

    assert r.status_code == 422
    assert "anterior a la de inicio" in r.text


def test_cerrar_un_hito_desde_la_api_recalcula_la_comision(
    cliente, catalogos_sembrados, uf_cargada
):
    """El caso que la app no permitia hacer desde ninguna pantalla."""
    creado = cliente.post("/api/negocios", json={
        "codigo": "VVP-CIERRE",
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": "Calle 4", "comuna": "Santiago"},
        "hitos": [_payload_hito()],
    }).json()
    hito_id = creado["hitos"][0]["id"]
    assert creado["hitos"][0]["comision_real_vp"] in (None, "0.00")

    r = cliente.patch(f"/api/negocios/{creado['id']}/hitos/{hito_id}", json={
        "fecha_inicio": "2026-01-02",
        "fecha_cierre": "2026-06-01",
        "estado": "CERRADO",
        "valor_negocio": "1000",
        "moneda": "UF",
        "fecha_valorizacion": "2026-01-02",
        "pct_lado_vendedor": "0.02",
        "pct_broker_vendedor": "0.01",
        "pct_vp_vendedor": "0.01",
    })

    assert r.status_code == 200, r.text
    hito = r.json()
    assert hito["estado"] == "CERRADO"
    assert hito["fecha_cierre"] == "2026-06-01"
    # La UF del 2026-01-02 es 39.735,63: mil UF son 39.735.630, y el 2% es
    # 794.712,60. El motor lo recalculo al guardar, no vino del cuerpo.
    assert hito["uf_snapshot"] == "39735.63"
    assert hito["comision_total"] == "794712.60"
    assert hito["comision_real_vp"] == "397356.30"


def test_las_tasas_sobreviven_una_vuelta_de_leer_y_guardar(
    cliente, catalogos_sembrados, uf_cargada
):
    """El agujero que este test cierra.

    El formulario de edicion lee el hito, muestra sus campos y manda de vuelta lo
    que haya. Si la API no devolviera las tasas, el formulario las mostraria
    vacias y al guardar irian en nulo: la comision se recalcularia a cero y la
    base del calculo se perderia en silencio, sin ningun error.
    """
    tasas = {
        "pct_lado_vendedor": "0.02",
        "pct_broker_vendedor": "0.01",
        "pct_vp_vendedor": "0.01",
        "pct_equipo": "0.10",
    }
    creado = cliente.post("/api/negocios", json={
        "codigo": "VVP-VUELTA",
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": "Calle 9", "comuna": "Santiago"},
        "hitos": [{
            "fecha_inicio": "2026-01-02", "estado": "ACTIVO",
            "valor_negocio": "1000", "moneda": "UF",
            "fecha_valorizacion": "2026-01-02", **tasas,
        }],
    }).json()
    hito = creado["hitos"][0]

    # 1. La API las devuelve. Sin esto el resto no puede funcionar.
    for campo, esperado in tasas.items():
        assert hito[campo] is not None, f"{campo} no vuelve en la respuesta"
        assert D(hito[campo]) == D(esperado)

    comision_antes = hito["comision_real_vp"]

    # 2. Se manda de vuelta tal cual vino, que es lo que hace el formulario, y
    #    solo se cambia el estado a cerrado.
    cuerpo = {c: hito[c] for c in (
        "nombre", "fecha_inicio", "valor_negocio", "moneda", "fecha_valorizacion",
        "valor_clp_manual", "motivo_valor_manual", "nombre_tercero",
        "motivo_perdida_id", "motivo_perdida_detalle",
        "pct_lado_vendedor", "pct_lado_comprador", "pct_rebate_concentrador",
        "pct_broker_vendedor", "pct_broker_comprador", "pct_vp_vendedor",
        "pct_vp_comprador", "pct_equipo", "pct_tercero",
    )}
    cuerpo |= {"estado": "CERRADO", "fecha_cierre": "2026-06-01"}

    r = cliente.patch(f"/api/negocios/{creado['id']}/hitos/{hito['id']}", json=cuerpo)
    assert r.status_code == 200, r.text
    despues = r.json()

    # 3. La comision no cambio: solo se cerro, no se recalculo sobre nada distinto.
    assert despues["comision_real_vp"] == comision_antes
    for campo, esperado in tasas.items():
        assert D(despues[campo]) == D(esperado)


# --------------------------------------------- la guarda del monto ya cerrado

CAMPOS_DE_VUELTA = (
    "nombre", "fecha_inicio", "valor_negocio", "moneda", "fecha_valorizacion",
    "valor_clp_manual", "motivo_valor_manual", "nombre_tercero",
    "motivo_perdida_id", "motivo_perdida_detalle",
    "pct_lado_vendedor", "pct_lado_comprador", "pct_rebate_concentrador",
    "pct_broker_vendedor", "pct_broker_comprador", "pct_vp_vendedor",
    "pct_vp_comprador", "pct_equipo", "pct_tercero",
)


def _negocio_cerrado(cliente, codigo: str) -> dict:
    """Un negocio con su unica liquidacion ya cerrada y su comision calculada."""
    creado = cliente.post("/api/negocios", json={
        "codigo": codigo,
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": f"Calle {codigo}", "comuna": "Santiago"},
        "hitos": [{
            "fecha_inicio": "2026-01-02",
            "fecha_cierre": "2026-06-01",
            "estado": "CERRADO",
            "valor_negocio": "1000", "moneda": "UF",
            "fecha_valorizacion": "2026-01-02",
            "pct_lado_vendedor": "0.02",
            "pct_broker_vendedor": "0.01",
            "pct_vp_vendedor": "0.01",
        }],
    })
    assert creado.status_code == 201, creado.text
    return creado.json()


def test_guardar_una_liquidacion_cerrada_sin_cambios_no_avisa(
    cliente, catalogos_sembrados, uf_cargada
):
    """La guarda no puede molestar cuando no pasa nada.

    Si avisara en cada guardado se volveria ruido y la gente aprenderia a
    confirmar sin leer, que es peor que no tener guarda.
    """
    negocio = _negocio_cerrado(cliente, "VVP-QUIETO")
    hito = negocio["hitos"][0]
    cuerpo = {c: hito[c] for c in CAMPOS_DE_VUELTA} | {
        "estado": "CERRADO", "fecha_cierre": hito["fecha_cierre"],
    }

    r = cliente.patch(f"/api/negocios/{negocio['id']}/hitos/{hito['id']}", json=cuerpo)

    assert r.status_code == 200, r.text
    assert r.json()["comision_real_vp"] == hito["comision_real_vp"]


def test_cambiar_la_tasa_de_una_liquidacion_cerrada_pide_confirmacion(
    cliente, catalogos_sembrados, uf_cargada
):
    """El caso que motivo todo esto: plata facturada que se mueve al guardar."""
    negocio = _negocio_cerrado(cliente, "VVP-OJO")
    hito = negocio["hitos"][0]
    antes = hito["comision_real_vp"]
    cuerpo = {c: hito[c] for c in CAMPOS_DE_VUELTA} | {
        "estado": "CERRADO",
        "fecha_cierre": hito["fecha_cierre"],
        "pct_vp_vendedor": "0.02",  # el doble
    }

    r = cliente.patch(f"/api/negocios/{negocio['id']}/hitos/{hito['id']}", json=cuerpo)

    assert r.status_code == 409, r.text
    detalle = r.json()["detail"]
    assert detalle["motivo"] == "cambio_de_monto"
    # El mensaje trae los dos montos: sin eso no hay nada que decidir.
    assert D(detalle["comision_actual"]) == D(antes)
    assert D(detalle["comision_nueva"]) > D(antes)

    # Y nada se guardo: el rechazo no puede dejar el cambio a medias.
    guardado = cliente.get(f"/api/negocios/{negocio['id']}").json()["hitos"][0]
    assert guardado["comision_real_vp"] == antes
    assert D(guardado["pct_vp_vendedor"]) == D("0.01")


def test_con_la_confirmacion_el_cambio_pasa(cliente, catalogos_sembrados, uf_cargada):
    """No es un bloqueo: es un aviso que se puede aceptar."""
    negocio = _negocio_cerrado(cliente, "VVP-DALE")
    hito = negocio["hitos"][0]
    cuerpo = {c: hito[c] for c in CAMPOS_DE_VUELTA} | {
        "estado": "CERRADO",
        "fecha_cierre": hito["fecha_cierre"],
        "pct_vp_vendedor": "0.02",
        "confirmar_cambio_de_monto": True,
    }

    r = cliente.patch(f"/api/negocios/{negocio['id']}/hitos/{hito['id']}", json=cuerpo)

    assert r.status_code == 200, r.text
    assert D(r.json()["comision_real_vp"]) == D(hito["comision_real_vp"]) * 2


def test_cerrar_un_hito_abierto_no_pide_confirmacion(
    cliente, catalogos_sembrados, uf_cargada
):
    """Cerrar calcula la comision por primera vez: ahi el cambio es el objetivo."""
    creado = cliente.post("/api/negocios", json={
        "codigo": "VVP-ABRE-Y-CIERRA",
        "modelo": "MERCADO_PRIMARIO",
        "propiedad": {"direccion": "Calle 12", "comuna": "Santiago"},
        "hitos": [{
            "fecha_inicio": "2026-01-02", "estado": "ACTIVO",
            "valor_negocio": "1000", "moneda": "UF",
            "fecha_valorizacion": "2026-01-02",
            "pct_lado_vendedor": "0.02", "pct_broker_vendedor": "0.01",
            "pct_vp_vendedor": "0.01",
        }],
    }).json()
    hito = creado["hitos"][0]
    cuerpo = {c: hito[c] for c in CAMPOS_DE_VUELTA} | {
        "estado": "CERRADO",
        "fecha_cierre": "2026-06-01",
        "pct_vp_vendedor": "0.02",  # cambia la plata, y da lo mismo: estaba abierto
    }

    r = cliente.patch(f"/api/negocios/{creado['id']}/hitos/{hito['id']}", json=cuerpo)

    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "CERRADO"


def test_la_guarda_mira_los_siete_montos_no_solo_la_comision_real(
    cliente, db, catalogos_sembrados, uf_cargada
):
    """La forma exacta de `VVP-2`: se mueve el total y la comision real no.

    Esa fila del Excel calculo el total sobre una base y el reparto sobre otra, asi
    que al guardarla el motor deja la comision real igual --que es la plata que se
    cobro-- y le sube el total en 903.803. Una guarda que solo mirara
    `comision_real_vp` habria dejado pasar justamente el descuadre mas grande.

    Se simula desarmando la fila a mano: se le escribe un total que sus propias
    entradas no producen, que es la condicion en que llego del Excel.
    """
    from app.models.negocio import NegocioHito

    negocio = _negocio_cerrado(cliente, "VVP-COMO-EL-2")
    hito = negocio["hitos"][0]
    real_antes = hito["comision_real_vp"]

    fila = db.get(NegocioHito, hito["id"])
    fila.comision_total = D(hito["comision_total"]) - D("903803")
    db.commit()

    cuerpo = {c: hito[c] for c in CAMPOS_DE_VUELTA} | {
        "estado": "CERRADO", "fecha_cierre": hito["fecha_cierre"],
    }
    r = cliente.patch(f"/api/negocios/{negocio['id']}/hitos/{hito['id']}", json=cuerpo)

    assert r.status_code == 409, r.text
    detalle = r.json()["detail"]
    assert detalle["campo"] == "comision_total"
    # La comision real no se mueve, y aun asi la guarda frena.
    assert "comision_real_vp" not in detalle["montos_que_cambian"]
    assert detalle["montos_que_cambian"]["comision_total"] == [
        str(D(hito["comision_total"]) - D("903803")), hito["comision_total"],
    ]

    db.expire_all()
    assert db.get(NegocioHito, hito["id"]).comision_real_vp == D(real_antes)
