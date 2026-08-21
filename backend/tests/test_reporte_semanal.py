"""Tests del reporte semanal (sprint 16).

Las dos propiedades que protegen:

1. **"Avanzó" es toda actividad, no solo un cambio de etapa.** La primera
   version filtraba por `etapa_resultante is not None` y daba cero sobre 44
   movimientos reales de una semana, porque los movimientos migrados del Excel
   llevan la etapa nula a proposito (D-030). Un reporte que no ve la gestion
   registrada no sirve.
2. **Estancado es una ausencia, no un estado guardado.** Se mide contra el
   ultimo movimiento, y si nunca hubo ninguno contra la fecha de origen. Un
   canje sin gestion desde 2022 tiene que salir, no quedar invisible por no
   tener filas en `movimientos`.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio, Etapa, ModeloNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.reporte_semanal import (
    TOPE_LISTA,
    obtener_reporte_semanal,
    semana_de,
)

# Un viernes. La semana que lo contiene es del lunes 17 al domingo 23.
AHORA = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
LUNES, DOMINGO = date(2026, 8, 17), date(2026, 8, 23)


def _hace(dias=0, horas=0) -> datetime:
    return AHORA - timedelta(days=dias, hours=horas)


@pytest.fixture(autouse=True)
def etapas(db):
    """`negocios.etapa` apunta a `etapas.codigo` y la clave foranea esta activa."""
    db.add(Etapa(codigo="E2", nombre="Visita", responsable="COMERCIAL", orden=2))
    db.commit()


@pytest.fixture
def tipos(db):
    """Los tipos que el reporte necesita distinguir: gestion, avance y caida."""
    db.add_all([
        TipoMovimiento(codigo="WA_SOLICITANTE", entity_type=EntityType.canje,
                       nombre="WA confirmación solicitante", etapa_resultante=None,
                       orden=1, sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="PASA_A_OFERTA", entity_type=EntityType.canje,
                       nombre="Pasa a oferta", etapa_resultante="EN_OFERTA",
                       orden=2, sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="CANCELACION", entity_type=EntityType.canje,
                       nombre="Cancelación", etapa_resultante=None,
                       orden=3, sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="NEG_LLAMADA", entity_type=EntityType.negocio,
                       nombre="Llamada", etapa_resultante=None,
                       orden=1, sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="NEG_PERDIDA", entity_type=EntityType.negocio,
                       nombre="Pérdida", etapa_resultante=None,
                       orden=2, sla_es_habil=False, activo=True),
    ])
    db.commit()
    return db


def _canje(db, id_, etapa=CanjeEtapa.EN_REVISION, estado=CanjeEstado.ACTIVO,
           dias_solicitud=60, cierre=None):
    db.add(Canje(
        id=id_,
        fecha_solicitud=_hace(dias_solicitud),
        fecha_cierre=cierre,
        estado=estado,
        etapa=etapa,
        comuna="Providencia",
        corredor_solicitante_nombre="Ana Solicitante",
    ))


def _mov(db, entity_type, entity_id, tipo, cuando, etapa=None, comentario="x"):
    db.add(Movimiento(
        entity_type=entity_type,
        entity_id=entity_id,
        tipo_movimiento=tipo,
        fecha=cuando,
        etapa_resultante=etapa,
        comentario=comentario,
    ))


def _negocio(db, codigo, estado=EstadoNegocio.ACTIVO, cierre=None, real=D("0"),
             etapa="E2"):
    prop = Propiedad(direccion=f"Calle {codigo}", comuna="Nunoa")
    db.add(prop)
    n = Negocio(codigo=codigo, modelo=ModeloNegocio.MERCADO_PRIMARIO,
                propiedad=prop, etapa=etapa)
    n.hitos = [NegocioHito(
        fecha_inicio=(AHORA - timedelta(days=90)).date(),
        fecha_cierre=cierre,
        estado=estado,
        comision_real_vp=real,
    )]
    db.add(n)
    db.flush()
    return n


def _reporte(db, desde=LUNES, hasta=DOMINGO, dias=14):
    return obtener_reporte_semanal(db, desde, hasta, dias, ahora=AHORA)


# ------------------------------------------------------------------ semana


@pytest.mark.parametrize("dia", [17, 19, 21, 23])
def test_cualquier_dia_de_la_semana_da_el_mismo_lunes_y_domingo(dia):
    assert semana_de(date(2026, 8, dia)) == (LUNES, DOMINGO)


def test_sin_periodo_toma_la_semana_en_curso(db):
    r = obtener_reporte_semanal(db, ahora=AHORA)
    assert (r.desde, r.hasta) == (LUNES, DOMINGO)


# ------------------------------------------------- avanzo = toda actividad


def test_la_gestion_sin_cambio_de_etapa_cuenta_como_avance(db, tipos):
    """La regresion que motivo el cambio: 44 movimientos y cero avanzados."""
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(2), etapa=None)
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_avanzados == 1
    assert seccion.avanzados[0].referencia == "#1"
    # Sin etapa, pero con el nombre del tipo para que se sepa que se hizo.
    assert seccion.avanzados[0].etapa is None
    assert seccion.avanzados[0].comentario == "WA confirmación solicitante"


def test_cuando_el_movimiento_si_mueve_la_etapa_la_muestra(db, tipos):
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "PASA_A_OFERTA", _hace(2), etapa="EN_OFERTA")
    db.commit()

    assert _reporte(db).canjes.avanzados[0].etapa == "EN_OFERTA"


def test_una_caida_no_se_cuenta_tambien_como_avance(db, tipos):
    """El mismo hecho en dos columnas inflaria las dos."""
    _canje(db, 1)
    _canje(db, 2)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(2))
    _mov(db, EntityType.canje, 2, "CANCELACION", _hace(3), comentario="se arrepintio")
    db.commit()

    seccion = _reporte(db).canjes
    assert (seccion.total_avanzados, seccion.total_caidos) == (1, 1)
    assert seccion.avanzados[0].referencia == "#1"
    assert seccion.caidos[0].referencia == "#2"
    assert seccion.caidos[0].comentario == "se arrepintio"


def test_la_perdida_de_un_negocio_no_cuenta_como_avance(db, tipos):
    n = _negocio(db, "VVP-1")
    _mov(db, EntityType.negocio, n.id, "NEG_PERDIDA", _hace(1), comentario="precio")
    db.commit()

    seccion = _reporte(db).negocios
    assert (seccion.total_caidos, seccion.total_avanzados) == (1, 0)


def test_lo_de_fuera_del_periodo_no_entra(db, tipos):
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(20))
    db.commit()

    assert _reporte(db).canjes.total_avanzados == 0


def test_el_ultimo_dia_del_periodo_entra_completo(db, tipos):
    """Un movimiento a las 23:00 del domingo es de esa semana."""
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE",
         datetime(2026, 8, 23, 23, 0, tzinfo=timezone.utc))
    db.commit()

    assert _reporte(db).canjes.total_avanzados == 1


# ---------------------------------------------------------------- cerrados


def test_lo_cerrado_sale_de_la_fecha_de_cierre_y_suma_la_comision(db):
    _negocio(db, "G-1", EstadoNegocio.CERRADO, cierre=date(2026, 8, 19), real=D("1500000"))
    _negocio(db, "G-2", EstadoNegocio.CERRADO, cierre=date(2026, 8, 21), real=D("400000"))
    _negocio(db, "G-3", EstadoNegocio.CERRADO, cierre=date(2026, 7, 1), real=D("999999"))
    db.commit()

    seccion = _reporte(db).negocios
    assert seccion.total_cerrados == 2
    assert seccion.monto_cerrado == D("1900000")
    assert [c.referencia for c in seccion.cerrados] == ["G-1", "G-2"]


def test_los_canjes_cerrados_no_traen_monto(db):
    """Un canje no lleva comision propia: sumar cero seria inventar plata."""
    _canje(db, 1, etapa=CanjeEtapa.CERRADO, cierre=_hace(2))
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_cerrados == 1
    assert seccion.monto_cerrado == D("0")
    assert seccion.cerrados[0].detalle == "Ana Solicitante"


# -------------------------------------------------------------- estancados


@pytest.mark.parametrize("dias_sin_mover, umbral, sale", [
    (20, 14, True),
    (14, 14, False),   # justo en el umbral todavia no esta estancado
    (15, 14, True),
    (20, 30, False),
])
def test_el_umbral_de_estancado_es_estricto(db, tipos, dias_sin_mover, umbral, sale):
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(dias_sin_mover))
    db.commit()

    assert bool(_reporte(db, dias=umbral).canjes.total_estancados) is sale


def test_sin_movimientos_se_mide_desde_la_solicitud(db):
    _canje(db, 1, dias_solicitud=400)
    db.commit()

    item = _reporte(db).canjes.estancados[0]
    assert item.dias_sin_movimiento == 400
    assert "sin gestión" in item.detalle


def test_manda_el_ultimo_movimiento_no_el_primero(db, tipos):
    _canje(db, 1, dias_solicitud=400)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(300))
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(20))
    db.commit()

    assert _reporte(db).canjes.estancados[0].dias_sin_movimiento == 20


def test_lo_cerrado_no_puede_estar_estancado(db):
    _canje(db, 1, etapa=CanjeEtapa.CERRADO, dias_solicitud=400)
    _canje(db, 2, estado=CanjeEstado.CANCELADO, dias_solicitud=400)
    _negocio(db, "G-1", EstadoNegocio.CERRADO, cierre=date(2026, 1, 5))
    _negocio(db, "P-1", EstadoNegocio.PERDIDO)
    db.commit()

    r = _reporte(db)
    assert (r.canjes.total_estancados, r.negocios.total_estancados) == (0, 0)


def test_el_canje_activo_con_etapa_cerrada_queda_fuera(db):
    """Los 31 que arrastran el desalineamiento de Dataprop, igual que la bandeja."""
    _canje(db, 1, estado=CanjeEstado.ACTIVO, etapa=CanjeEtapa.CERRADO, dias_solicitud=400)
    db.commit()

    assert _reporte(db).canjes.total_estancados == 0


def test_los_estancados_van_del_mas_viejo_al_mas_nuevo(db):
    for id_, dias in ((1, 30), (2, 400), (3, 100)):
        _canje(db, id_, dias_solicitud=dias)
    db.commit()

    dias = [e.dias_sin_movimiento for e in _reporte(db).canjes.estancados]
    assert dias == sorted(dias, reverse=True)


def test_un_negocio_con_dos_hitos_activos_sale_una_sola_vez(db):
    n = _negocio(db, "VVP-1")
    n.hitos.append(NegocioHito(
        fecha_inicio=(AHORA - timedelta(days=90)).date(),
        estado=EstadoNegocio.ACTIVO,
        comision_real_vp=D("0"),
    ))
    db.commit()

    assert _reporte(db).negocios.total_estancados == 1


# ------------------------------------------------------- totales vs listas


def test_el_total_cuenta_todo_aunque_la_lista_venga_topeada(db):
    for id_ in range(1, TOPE_LISTA + 6):
        _canje(db, id_, dias_solicitud=100 + id_)
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_estancados == TOPE_LISTA + 5
    assert len(seccion.estancados) == TOPE_LISTA


# ---------------------------------------------------------------- endpoint


def test_el_endpoint_sin_parametros_devuelve_la_semana_en_curso(cliente):
    r = cliente.get("/api/reportes/semanal")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["dias_estancado"] == 14
    assert set(cuerpo) == {"desde", "hasta", "dias_estancado", "negocios", "canjes"}


@pytest.mark.parametrize("params, trozo", [
    ({"desde": "2026-08-17"}, "juntos"),
    ({"hasta": "2026-08-23"}, "juntos"),
    ({"desde": "2026-08-23", "hasta": "2026-08-17"}, "anterior"),
    ({"desde": "2024-01-01", "hasta": "2026-08-17"}, "366"),
])
def test_el_endpoint_rechaza_periodos_imposibles(cliente, params, trozo):
    r = cliente.get("/api/reportes/semanal", params=params)
    assert r.status_code == 400
    assert trozo in r.json()["detail"]


def test_el_umbral_de_estancado_se_puede_cambiar_desde_la_query(cliente, db, tipos):
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(20))
    db.commit()

    assert cliente.get("/api/reportes/semanal",
                       params={"dias_estancado": 14}).json()["canjes"]["total_estancados"] == 1
    assert cliente.get("/api/reportes/semanal",
                       params={"dias_estancado": 30}).json()["canjes"]["total_estancados"] == 0
