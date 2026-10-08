"""Duración por etapa de los canjes (`D-115`)."""
from datetime import datetime, timezone

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.services.duracion_etapas import obtener_duracion_por_etapa, tramos_del_canje


def _dt(dia: int, mes: int = 8) -> datetime:
    return datetime(2026, mes, dia, 15, 0, tzinfo=timezone.utc)


# --- tramos_del_canje -------------------------------------------------------


def test_revision_arranca_en_la_solicitud():
    tramos = tramos_del_canje(
        _dt(1),
        [(_dt(5), "EN_REVISION"), (_dt(11), "PROCESO_DE_ACUERDO")],
    )
    # Del 1 (solicitud) al 11, no del 5 (primera estampa).
    assert tramos == [(CanjeEtapa.EN_REVISION, 10)]


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
        (CanjeEtapa.EN_REVISION, 2),
        (CanjeEtapa.PROCESO_DE_ACUERDO, 10),
    ]


def test_la_etapa_en_curso_no_es_un_tramo():
    # Quedó en oferta: ese tramo no tiene término y no se cuenta.
    tramos = tramos_del_canje(_dt(1), [(_dt(4), "EN_OFERTA"), (_dt(20), "EN_OFERTA")])
    assert tramos == []


def test_primer_tramo_que_no_es_revision_no_tiene_inicio_conocido():
    # Llegó de Dataprop ya en oferta: no se sabe desde cuándo. Lo que sigue sí.
    tramos = tramos_del_canje(
        _dt(1),
        [(_dt(10), "EN_OFERTA"), (_dt(15), "EN_NEGOCIO"), (_dt(22), "CERRADO")],
    )
    assert tramos == [(CanjeEtapa.EN_NEGOCIO, 7)]


def test_etapas_retiradas_se_saltan():
    tramos = tramos_del_canje(
        _dt(1),
        [(_dt(2), "RECEPCION"), (_dt(3), "EN_REVISION"), (_dt(8), "EN_OFERTA")],
    )
    assert tramos == [(CanjeEtapa.EN_REVISION, 7)]


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
    # Activo: revisión 4 días, sigue en acuerdo.
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

    r = _por_etapa(obtener_duracion_por_etapa(db))

    assert r[CanjeEtapa.EN_REVISION].activos.casos == 1
    assert r[CanjeEtapa.EN_REVISION].activos.promedio == 4
    assert r[CanjeEtapa.EN_REVISION].inactivos.casos == 1
    assert r[CanjeEtapa.EN_REVISION].inactivos.promedio == 6
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].activos.casos == 0
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].activos.promedio is None
    assert r[CanjeEtapa.PROCESO_DE_ACUERDO].inactivos.promedio == 3
    assert r[CanjeEtapa.EN_OFERTA].inactivos.casos == 0
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

    g = _por_etapa(obtener_duracion_por_etapa(db))[CanjeEtapa.EN_REVISION].activos
    assert (g.casos, g.promedio, g.mediana, g.minimo, g.maximo) == (3, 12.0, 4.0, 2, 30)
