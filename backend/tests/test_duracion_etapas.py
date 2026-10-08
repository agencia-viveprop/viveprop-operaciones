"""Duración por etapa de los canjes (`D-115`)."""
from datetime import date, datetime, timezone

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.services.duracion_etapas import obtener_duracion_por_etapa, tramos_del_canje


def _dt(dia: int, mes: int = 8) -> datetime:
    return datetime(2026, mes, dia, 15, 0, tzinfo=timezone.utc)


HOY = date(2026, 8, 30)


# --- tramos_del_canje -------------------------------------------------------


def test_revision_arranca_en_la_solicitud():
    tramos = tramos_del_canje(
        _dt(1),
        [(_dt(5), "EN_REVISION"), (_dt(11), "PROCESO_DE_ACUERDO")],
    )
    # Del 1 (solicitud) al 11, no del 5 (primera estampa).
    assert tramos == [(CanjeEtapa.EN_REVISION, 10, False)]


def test_gestiones_en_la_misma_etapa_no_cortan_el_tramo():
    tramos = tramos_del_canje(
        _dt(1),
        [
            (_dt(2), "EN_REVISION"),
            (_dt(3), "PROCESO_DE_ACUERDO"),
            (_dt(6), "PROCESO_DE_ACUERDO"),
            (_dt(9), "PROCESO_DE_ACUERDO"),
            (_dt(13), "EN_OFERTA"),
        ],
    )
    assert tramos == [
        (CanjeEtapa.EN_REVISION, 2, False),
        (CanjeEtapa.PROCESO_DE_ACUERDO, 10, False),
    ]


def test_la_etapa_en_curso_de_un_activo_cuenta_hasta_hoy():
    tramos = tramos_del_canje(
        _dt(1),
        [(_dt(2), "EN_REVISION"), (_dt(10), "EN_OFERTA"), (_dt(20), "EN_OFERTA")],
        CanjeEtapa.EN_OFERTA,
        HOY,
    )
    # En oferta desde el 10 (primera estampa de la racha) hasta hoy, el 30.
    assert tramos == [
        (CanjeEtapa.EN_REVISION, 9, False),
        (CanjeEtapa.EN_OFERTA, 20, True),
    ]


def test_sin_hoy_la_ultima_etapa_no_cuenta():
    # Es lo que pasa con un cancelado: la cancelación no termina la etapa, y
    # medirla hasta hoy la haría crecer para siempre.
    tramos = tramos_del_canje(_dt(1), [(_dt(4), "EN_OFERTA"), (_dt(20), "EN_OFERTA")])
    assert tramos == []


def test_etapa_en_curso_distinta_de_la_ficha_no_tiene_inicio():
    # La ficha dice negocio y la última estampa dice oferta: la etapa cambió sin
    # dejar rastro, así que no se sabe desde cuándo está en negocio.
    tramos = tramos_del_canje(
        _dt(1), [(_dt(5), "EN_OFERTA")], CanjeEtapa.EN_NEGOCIO, HOY
    )
    assert tramos == []


def test_activo_sin_estampas_en_revision_cuenta_desde_la_solicitud():
    assert tramos_del_canje(_dt(1), [], CanjeEtapa.EN_REVISION, HOY) == [
        (CanjeEtapa.EN_REVISION, 29, True)
    ]
    # En otra etapa, sin estampas, no se sabe desde cuándo.
    assert tramos_del_canje(_dt(1), [], CanjeEtapa.EN_OFERTA, HOY) == []


def test_primer_tramo_que_no_es_revision_no_tiene_inicio_conocido():
    # Llegó de Dataprop ya en oferta: no se sabe desde cuándo. Lo que sigue sí.
    tramos = tramos_del_canje(
        _dt(1),
        [(_dt(10), "EN_OFERTA"), (_dt(15), "EN_NEGOCIO"), (_dt(22), "CERRADO")],
    )
    assert tramos == [(CanjeEtapa.EN_NEGOCIO, 7, False)]


def test_etapas_retiradas_se_saltan():
    tramos = tramos_del_canje(
        _dt(1),
        [(_dt(2), "RECEPCION"), (_dt(3), "EN_REVISION"), (_dt(8), "EN_OFERTA")],
    )
    assert tramos == [(CanjeEtapa.EN_REVISION, 7, False)]


# --- obtener_duracion_por_etapa ----------------------------------------------


def _canje(db, id_, estado, etapa, solicitud):
    db.add(Canje(id=id_, fecha_solicitud=solicitud, estado=estado, etapa=etapa))
    db.flush()


def _mov(db, canje_id, fecha, etapa, tipo="LLAMADA"):
    db.add(
        Movimiento(
            entity_type=EntityType.canje,
            entity_id=canje_id,
            tipo_movimiento=tipo,
            etapa_resultante=etapa,
            fecha=fecha,
        )
    )


def _por_etapa(resultado):
    return {e.etapa: e for e in resultado.etapas}


def test_activos_e_inactivos_van_separados_y_la_cancelacion_no_cierra(db):
    db.add_all([
        TipoMovimiento(codigo="LLAMADA", entity_type=EntityType.canje, nombre="Llamada"),
        TipoMovimiento(codigo="CANCELACION", entity_type=EntityType.canje, nombre="Cancelación"),
    ])
    # Sin relación declarada, la sesión no sabe que los tipos van antes que los
    # movimientos que los nombran.
    db.flush()
    # Activo: revisión 4 días, y en acuerdo desde el 5 hasta hoy (25 días).
    _canje(db, 1, CanjeEstado.ACTIVO, CanjeEtapa.PROCESO_DE_ACUERDO, _dt(1))
    _mov(db, 1, _dt(2), "EN_REVISION")
    _mov(db, 1, _dt(5), "PROCESO_DE_ACUERDO")
    # Cancelado: revisión 6 días, acuerdo 3 días, y se cayó en oferta. La
    # cancelación estampa la misma etapa y no termina el tramo de oferta.
    _canje(db, 2, CanjeEstado.CANCELADO, CanjeEtapa.EN_OFERTA, _dt(1))
    _mov(db, 2, _dt(7), "PROCESO_DE_ACUERDO")
    _mov(db, 2, _dt(3), "EN_REVISION")
    _mov(db, 2, _dt(10), "EN_OFERTA")
    _mov(db, 2, _dt(25), "EN_OFERTA", tipo="CANCELACION")
    # Un movimiento sin etapa (los migrados) no cuenta para nada.
    _mov(db, 2, _dt(4), None)
    db.commit()

    r = _por_etapa(obtener_duracion_por_etapa(db, HOY))

    assert r[CanjeEtapa.EN_REVISION].activos.pasaron == 1
    assert r[CanjeEtapa.EN_REVISION].activos.promedio == 4
    assert r[CanjeEtapa.EN_REVISION].inactivos.pasaron == 1
    assert r[CanjeEtapa.EN_REVISION].inactivos.promedio == 6
    assert r[CanjeEtapa.EN_REVISION].activos.hoy_en_etapa == 0
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].activos.pasaron == 0
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].activos.hoy_en_etapa == 1
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].activos.sin_fecha_de_inicio == 0
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].activos.promedio == 25
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].inactivos.promedio == 3
    # El cancelado se cayó en oferta: esa etapa no entra, ni hasta hoy.
    assert r[CanjeEtapa.EN_OFERTA].inactivos.pasaron == 0
    # Un cancelado no está hoy en ninguna etapa.
    assert r[CanjeEtapa.EN_OFERTA].inactivos.hoy_en_etapa == 0
    # Las cinco etapas van siempre, en el orden del ciclo.
    assert [e for e in r] == list(CanjeEtapa)


def test_promedio_mediana_y_rango(db):
    db.add(TipoMovimiento(codigo="LLAMADA", entity_type=EntityType.canje, nombre="Llamada"))
    db.flush()
    for i, dias in enumerate([2, 4, 30], start=1):
        _canje(db, i, CanjeEstado.ACTIVO, CanjeEtapa.PROCESO_DE_ACUERDO, _dt(1))
        _mov(db, i, _dt(1), "EN_REVISION")
        _mov(db, i, _dt(1 + dias), "PROCESO_DE_ACUERDO")
    db.commit()

    g = _por_etapa(obtener_duracion_por_etapa(db, HOY))[CanjeEtapa.EN_REVISION].activos
    assert (g.pasaron, g.promedio, g.mediana, g.minimo, g.maximo) == (3, 12.0, 4.0, 2, 30)


def test_hoy_en_la_etapa_cuadra_con_el_listado_aunque_falte_el_inicio(db):
    """Como el #334: está en negocio sin ningún registro de cuándo entró."""
    db.add(TipoMovimiento(codigo="LLAMADA", entity_type=EntityType.canje, nombre="Llamada"))
    db.flush()
    _canje(db, 1, CanjeEstado.ACTIVO, CanjeEtapa.EN_NEGOCIO, _dt(1))
    # Otro en negocio con inicio conocido.
    _canje(db, 2, CanjeEstado.ACTIVO, CanjeEtapa.EN_NEGOCIO, _dt(1))
    _mov(db, 2, _dt(20), "EN_NEGOCIO")
    _mov(db, 2, _dt(10), "EN_REVISION")
    db.commit()

    g = _por_etapa(obtener_duracion_por_etapa(db, HOY))[CanjeEtapa.EN_NEGOCIO].activos
    assert (g.hoy_en_etapa, g.sin_fecha_de_inicio, g.pasaron) == (2, 1, 0)
    # El promedio es solo del que tiene inicio: del 20 al 30.
    assert g.promedio == 10
