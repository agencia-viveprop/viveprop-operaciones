"""Tests del pipeline de negocios (sprint 11).

Reusa la tabla `movimientos`, que es polimórfica y ya servía a canjes. Lo que se
fija acá es que avanzar de etapa quede registrado con autor y fecha, y que los
desenlaces toquen solo las liquidaciones abiertas.
"""
from datetime import date
from decimal import Decimal as D

import pytest

from app.models.movimiento import EntityType, TipoMovimiento
from app.models.catalogo import Catalogo, Etapa
from app.models.uf import UFDiaria

# codigo, nombre, etapa_resultante, orden
TIPOS = [
    ("NEG_E2_VISITA", "Visita y manifestación de interés", "E2", 2),
    ("NEG_E3_PROMESA", "Negociación, reserva y promesa", "E3", 3),
    ("NEG_E7_TERMINADO", "Terminado", "E7", 7),
    ("NEG_PERDIDA", "Negocio perdido", None, 8),
    ("NEG_COMENTARIO", "Comentario general", None, 10),
]


@pytest.fixture
def pipeline(db):
    db.add_all([
        Catalogo(tipo="alianza", codigo="ASSETPLAN", nombre="Assetplan", orden=1),
        Etapa(codigo="E2", nombre="Visita", responsable="COMERCIAL", orden=2),
        Etapa(codigo="E3", nombre="Promesa", responsable="HIBRIDO", orden=3),
        Etapa(codigo="E7", nombre="Terminado", responsable="OPERACIONES", orden=7),
        UFDiaria(fecha=date(2026, 1, 2), valor=D("39735.63")),
    ])
    db.add_all([
        TipoMovimiento(
            codigo=c, entity_type=EntityType.negocio, nombre=n,
            etapa_resultante=etapa, orden=orden, sla_es_habil=False, activo=True,
        )
        for c, n, etapa, orden in TIPOS
    ])
    # Un tipo de canje, para verificar que no se cruzan los dominios.
    db.add(TipoMovimiento(
        codigo="CIERRE", entity_type=EntityType.canje, nombre="Cierre",
        etapa_resultante="CERRADO", orden=12, sla_es_habil=False, activo=True,
    ))
    db.commit()
    return db


def _crear(cliente, **extra):
    cuerpo = {
        "codigo": "VVP-20",
        "modelo": "SECUNDARIO_CONCENTRADORES",
        "propiedad": {"direccion": "Av. Portales 672", "unidad": "314", "comuna": "Estación Central"},
        "etapa": "E2",
        "hitos": [{
            "fecha_inicio": "2026-01-02", "estado": "ACTIVO",
            "valor_negocio": "1000", "moneda": "UF",
            "pct_lado_comprador": "0.02", "pct_vp_comprador": "0.008", "pct_equipo": "0.10",
        }],
    }
    cuerpo.update(extra)
    r = cliente.post("/api/negocios", json=cuerpo)
    assert r.status_code == 201, r.text
    return r.json()


def test_los_tipos_del_pipeline_se_leen_desde_la_api(cliente, pipeline):
    """Para que el front no hardcodee los pasos."""
    tipos = cliente.get("/api/negocios/tipos-movimiento").json()

    assert [t["codigo"] for t in tipos] == [c for c, *_ in TIPOS]
    assert "CIERRE" not in [t["codigo"] for t in tipos], "los de canjes no se cruzan"


def test_avanzar_de_etapa_mueve_el_negocio(cliente, pipeline):
    negocio = _crear(cliente)
    assert negocio["etapa"] == "E2"

    r = cliente.post(
        f"/api/negocios/{negocio['id']}/movimientos",
        json={"tipo_movimiento": "NEG_E3_PROMESA", "comentario": "Promesa firmada"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["etapa_resultante"] == "E3"

    assert cliente.get(f"/api/negocios/{negocio['id']}").json()["etapa"] == "E3"


def test_el_movimiento_queda_en_el_historial_con_su_autor(cliente, pipeline):
    negocio = _crear(cliente)
    cliente.post(
        f"/api/negocios/{negocio['id']}/movimientos",
        json={"tipo_movimiento": "NEG_E3_PROMESA", "comentario": "Promesa firmada"},
    )

    historial = cliente.get(f"/api/negocios/{negocio['id']}/movimientos").json()

    assert len(historial) == 1
    assert historial[0]["tipo_nombre"] == "Negociación, reserva y promesa"
    assert historial[0]["comentario"] == "Promesa firmada"
    assert historial[0]["autor_nombre"] == "Test"


def test_el_historial_viene_del_mas_reciente_al_mas_antiguo(cliente, pipeline):
    """Lo primero que se lee es lo ultimo que paso, y el desempate se mantiene.

    **Este orden fue y volvio, asi que vale dejar la historia completa.** Al
    principio era descendente. Se paso a ascendente porque el pipeline es una
    secuencia que se lee de E1 hacia adelante (`D-065`), y de paso se arreglo algo
    peor: ordenaba solo por `fecha`, asi que dos etapas registradas el mismo dia
    salian en orden arbitrario --en los datos reales aparecio E2 arriba de E1--.
    Ahora vuelve a ser descendente porque el usuario lo pidio despues de usarlo
    con negocios de seis y siete registros (`D-082`), igual que en canjes
    (`D-080`).

    **Lo que no vuelve es el defecto:** el `id` sigue desempatando, ahora tambien
    descendente, asi que dentro del mismo dia la ultima etapa cargada queda arriba
    y el orden es determinista.
    """
    negocio = _crear(cliente)
    for tipo in ("NEG_E3_PROMESA", "NEG_E7_TERMINADO"):
        cliente.post(f"/api/negocios/{negocio['id']}/movimientos", json={"tipo_movimiento": tipo})

    historial = cliente.get(f"/api/negocios/{negocio['id']}/movimientos").json()

    assert [m["tipo_movimiento"] for m in historial] == ["NEG_E7_TERMINADO", "NEG_E3_PROMESA"]
    # Los dos entran el mismo dia: si el `id` no desempatara, este orden seria
    # el que decida el plan de la consulta.
    assert [m["fecha"] for m in historial] == sorted(
        (m["fecha"] for m in historial), reverse=True
    )
    assert [m["id"] for m in historial] == sorted(
        (m["id"] for m in historial), reverse=True
    )


def test_un_comentario_no_mueve_la_etapa(cliente, pipeline):
    negocio = _crear(cliente)

    cliente.post(
        f"/api/negocios/{negocio['id']}/movimientos",
        json={"tipo_movimiento": "NEG_COMENTARIO", "comentario": "Llamé al cliente"},
    )

    assert cliente.get(f"/api/negocios/{negocio['id']}").json()["etapa"] == "E2"


def test_la_perdida_solo_toca_las_liquidaciones_abiertas(cliente, pipeline):
    """Una promesa ya cerrada no se vuelve perdida porque la escritura se cayó."""
    negocio = _crear(cliente, hitos=[
        {"nombre": "PROMESA", "fecha_inicio": "2026-01-02", "fecha_cierre": "2026-03-01", "estado": "CERRADO",
         "valor_negocio": "1000", "moneda": "UF", "pct_lado_comprador": "0.02",
         "pct_vp_comprador": "0.008", "pct_equipo": "0.10"},
        {"nombre": "ESCRITURA", "fecha_inicio": "2026-01-02", "estado": "ACTIVO",
         "valor_negocio": "1000", "moneda": "UF", "pct_lado_comprador": "0.01",
         "pct_vp_comprador": "0.004", "pct_equipo": "0.10"},
    ])

    cliente.post(
        f"/api/negocios/{negocio['id']}/movimientos",
        json={"tipo_movimiento": "NEG_PERDIDA", "comentario": "No se logró el crédito"},
    )

    hitos = {h["nombre"]: h for h in cliente.get(f"/api/negocios/{negocio['id']}").json()["hitos"]}
    assert hitos["PROMESA"]["estado"] == "CERRADO", "lo ya cerrado no se toca"
    assert hitos["ESCRITURA"]["estado"] == "PERDIDO"


def test_no_se_puede_usar_un_tipo_de_canje_en_un_negocio(cliente, pipeline):
    """Los códigos llevan prefijo NEG_ justamente para no confundirlos (D-014)."""
    negocio = _crear(cliente)

    r = cliente.post(
        f"/api/negocios/{negocio['id']}/movimientos",
        json={"tipo_movimiento": "CIERRE"},
    )

    assert r.status_code == 400
    assert "CIERRE" in r.json()["detail"]


def test_tipo_inexistente_falla_claro(cliente, pipeline):
    negocio = _crear(cliente)
    r = cliente.post(
        f"/api/negocios/{negocio['id']}/movimientos",
        json={"tipo_movimiento": "NEG_INVENTADO"},
    )
    assert r.status_code == 400


def test_movimiento_sobre_un_negocio_inexistente(cliente, pipeline):
    """`movimientos.entity_id` no puede tener clave foránea, así que lo valida el servicio."""
    r = cliente.post(
        "/api/negocios/9999/movimientos", json={"tipo_movimiento": "NEG_E3_PROMESA"}
    )
    assert r.status_code == 404
