"""Que la etapa y el tipo de movimiento sean dos datos que conviven.

**Qué cambió.** Registrar una gestión de canje pedía un solo dato --el tipo-- y la
etapa salía implícita de él: `ACUERDO_FIRMADO` movía el canje a «Proceso de
acuerdo» y `CLIENTE_CALIFICADO` no lo movía a ninguna parte. Eso ataba dos cosas
distintas: **qué se hizo** y **dónde quedó el canje**. Con una llamada de
seguimiento no había forma de decir que el canje avanzó, ni de avanzarlo sin
inventar un tipo que lo hiciera.

Ahora la etapa se elige aparte y gana sobre la del tipo. El cambio es aditivo: sin
etapa indicada, el comportamiento es el de antes.
"""
from datetime import date, datetime, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.services.movimientos import crear_movimiento_canje, eliminar_movimiento_canje

SOLICITUD = datetime(2026, 6, 1, tzinfo=timezone.utc)


@pytest.fixture
def base(db):
    db.add_all([
        # Los cuatro que se ofrecen: ninguno impone etapa.
        TipoMovimiento(codigo="GESTION_INICIAL", entity_type=EntityType.canje,
                       nombre="Gestión inicial", etapa_resultante=None, orden=1,
                       sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="SEG_LLAMADO", entity_type=EntityType.canje,
                       nombre="Seguimiento - Llamado", etapa_resultante=None, orden=2,
                       sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="SEG_WHATSAPP", entity_type=EntityType.canje,
                       nombre="Seguimiento - Whatsapp", etapa_resultante=None, orden=3,
                       sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="RESPUESTA_CORREDOR", entity_type=EntityType.canje,
                       nombre="Respuesta Corredor", etapa_resultante=None, orden=4,
                       sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="CANCELACION", entity_type=EntityType.canje,
                       nombre="Cancelación", etapa_resultante=None, orden=9,
                       sla_es_habil=False, activo=True),
        # Uno viejo, inactivo, que sí imponía etapa. Sigue existiendo para el
        # historial y para verificar la compatibilidad hacia atrás.
        TipoMovimiento(codigo="ACUERDO_FIRMADO", entity_type=EntityType.canje,
                       nombre="Acuerdo de canje firmado",
                       etapa_resultante="PROCESO_DE_ACUERDO", orden=20,
                       sla_es_habil=False, activo=False),
    ])
    db.add(Canje(id=1, fecha_solicitud=SOLICITUD, estado=CanjeEstado.ACTIVO,
                 etapa=CanjeEtapa.RECEPCION, comuna="Santiago"))
    db.commit()
    return db


# ------------------------------------------------- los dos campos conviven


def test_la_etapa_elegida_mueve_el_canje(base):
    """Una llamada de seguimiento puede avanzar el canje. Antes no podía."""
    m = crear_movimiento_canje(
        base, 1, "SEG_LLAMADO", autor_id=None, etapa=CanjeEtapa.EN_OFERTA
    )

    assert m.tipo_movimiento == "SEG_LLAMADO"
    assert m.etapa_resultante == "EN_OFERTA"
    assert base.get(Canje, 1).etapa == CanjeEtapa.EN_OFERTA


def test_el_tipo_no_impone_la_etapa(base):
    """Dos gestiones del mismo tipo pueden dejar el canje en etapas distintas.

    Es el punto de separarlos: el tipo describe la gestión, no su desenlace.
    """
    crear_movimiento_canje(base, 1, "SEG_WHATSAPP", autor_id=None,
                           etapa=CanjeEtapa.EN_REVISION,
                           fecha=datetime(2026, 7, 1, tzinfo=timezone.utc))
    crear_movimiento_canje(base, 1, "SEG_WHATSAPP", autor_id=None,
                           etapa=CanjeEtapa.EN_NEGOCIO,
                           fecha=datetime(2026, 7, 10, tzinfo=timezone.utc))

    assert base.get(Canje, 1).etapa == CanjeEtapa.EN_NEGOCIO
    etapas = [m.etapa_resultante for m in base.query(Movimiento).order_by(Movimiento.fecha)]
    assert etapas == ["EN_REVISION", "EN_NEGOCIO"]


def test_la_misma_etapa_repetida_no_es_un_problema(base):
    """Confirmar que el canje sigue donde estaba es información, no ruido.

    Una llamada que no movió nada igual registra la etapa: la línea de tiempo
    queda diciendo "el 10 de julio seguía en revisión", que es un dato.
    """
    crear_movimiento_canje(base, 1, "SEG_LLAMADO", autor_id=None,
                           etapa=CanjeEtapa.EN_REVISION,
                           fecha=datetime(2026, 7, 1, tzinfo=timezone.utc))
    crear_movimiento_canje(base, 1, "SEG_LLAMADO", autor_id=None,
                           etapa=CanjeEtapa.EN_REVISION,
                           fecha=datetime(2026, 7, 10, tzinfo=timezone.utc))

    assert base.get(Canje, 1).etapa == CanjeEtapa.EN_REVISION
    assert base.query(Movimiento).count() == 2


def test_la_etapa_puede_retroceder_si_se_elige(base):
    """El sistema no opina: si alguien devuelve el canje a revisión, se devuelve.

    Distinto del caso de `D-052`, donde la etapa retrocedía **sola** por atrasar
    la fecha de un movimiento. Acá es una decisión explícita.
    """
    crear_movimiento_canje(base, 1, "SEG_LLAMADO", autor_id=None,
                           etapa=CanjeEtapa.EN_NEGOCIO,
                           fecha=datetime(2026, 7, 1, tzinfo=timezone.utc))
    crear_movimiento_canje(base, 1, "RESPUESTA_CORREDOR", autor_id=None,
                           etapa=CanjeEtapa.EN_REVISION,
                           fecha=datetime(2026, 7, 10, tzinfo=timezone.utc))

    assert base.get(Canje, 1).etapa == CanjeEtapa.EN_REVISION


# ------------------------------------------------------ hacia atrás sigue igual


def test_sin_etapa_indicada_manda_la_del_tipo(base):
    """El cambio es aditivo: quien llame sin etapa se comporta como antes.

    Es lo que mantiene funcionando a la migración de cancelación masiva y a
    cualquier otro llamador que no pase el parámetro.
    """
    m = crear_movimiento_canje(base, 1, "ACUERDO_FIRMADO", autor_id=None)

    assert m.etapa_resultante == "PROCESO_DE_ACUERDO"
    assert base.get(Canje, 1).etapa == CanjeEtapa.PROCESO_DE_ACUERDO


def test_sin_etapa_y_con_un_tipo_que_no_la_impone_el_canje_no_se_mueve(base):
    crear_movimiento_canje(base, 1, "SEG_LLAMADO", autor_id=None)

    assert base.get(Canje, 1).etapa == CanjeEtapa.RECEPCION


def test_la_cancelacion_sigue_cancelando(base):
    """Quedó como opción aparte de los cuatro: es la única forma de dejar la
    cancelación registrada en la línea de tiempo."""
    crear_movimiento_canje(base, 1, "CANCELACION", autor_id=None,
                           etapa=CanjeEtapa.CERRADO)

    c = base.get(Canje, 1)
    assert c.estado == CanjeEstado.CANCELADO
    assert c.etapa == CanjeEtapa.CERRADO


# ----------------------------------------------- borrar devuelve la anterior


def test_borrar_un_movimiento_devuelve_la_etapa_que_habia(base):
    """Sigue funcionando con la etapa elegida a mano, no solo con la del tipo.

    Es la consecuencia de derivarla de la línea de tiempo (`D-052`): el compromiso
    y la etapa se leen, no se acumulan.
    """
    crear_movimiento_canje(base, 1, "SEG_LLAMADO", autor_id=None,
                           etapa=CanjeEtapa.EN_REVISION,
                           fecha=datetime(2026, 7, 1, tzinfo=timezone.utc))
    ultimo = crear_movimiento_canje(base, 1, "SEG_LLAMADO", autor_id=None,
                                    etapa=CanjeEtapa.EN_NEGOCIO,
                                    fecha=datetime(2026, 7, 10, tzinfo=timezone.utc))
    assert base.get(Canje, 1).etapa == CanjeEtapa.EN_NEGOCIO

    eliminar_movimiento_canje(base, 1, ultimo.id)

    assert base.get(Canje, 1).etapa == CanjeEtapa.EN_REVISION


# ---------------------------------------------------------------- el catálogo


def test_la_etapa_de_entrada_se_llama_recepcion():
    """Se llamaba `SIN_ETAPA`, que describía la falta de dato en el export de
    Dataprop y no un estado del negocio."""
    assert CanjeEtapa.RECEPCION.value == "RECEPCION"
    assert not hasattr(CanjeEtapa, "SIN_ETAPA")
    assert [e.value for e in CanjeEtapa] == [
        "RECEPCION", "EN_REVISION", "PROCESO_DE_ACUERDO",
        "EN_OFERTA", "EN_NEGOCIO", "CERRADO",
    ]


def test_los_tipos_viejos_siguen_existiendo_para_el_historial(base):
    """Inactivo quiere decir "no se ofrece más", no "no existió".

    605 movimientos los referencian y son la línea de tiempo de los 297 canjes.
    """
    viejo = base.get(TipoMovimiento, "ACUERDO_FIRMADO")

    assert viejo is not None
    assert viejo.activo is False
    # Y se le puede seguir asociando historia: la clave foránea sigue viva.
    m = crear_movimiento_canje(base, 1, "ACUERDO_FIRMADO", autor_id=None)
    assert m.tipo_movimiento == "ACUERDO_FIRMADO"


# ------------------------------------------------------------------ endpoint


def test_el_endpoint_acepta_las_dos_cosas(cliente, base):
    r = cliente.post("/api/canjes/1/movimientos", json={
        "tipo_movimiento": "SEG_LLAMADO",
        "etapa": "EN_OFERTA",
        "comentario": "Llamé y quedó en revisar la oferta",
    })

    assert r.status_code == 201, r.text
    assert r.json()["etapa_resultante"] == "EN_OFERTA"
    assert cliente.get("/api/canjes/1").json()["etapa"] == "EN_OFERTA"


def test_el_endpoint_rechaza_una_etapa_que_no_existe(cliente, base):
    r = cliente.post("/api/canjes/1/movimientos", json={
        "tipo_movimiento": "SEG_LLAMADO",
        "etapa": "EN_TRAMITE",
    })

    assert r.status_code == 422


def test_el_endpoint_solo_ofrece_los_activos(cliente, base):
    tipos = cliente.get("/api/tipos-movimiento?entity_type=canje").json()

    codigos = [t["codigo"] for t in tipos]
    assert "ACUERDO_FIRMADO" not in codigos, "inactivo: no se ofrece"
    assert codigos == [
        "GESTION_INICIAL", "SEG_LLAMADO", "SEG_WHATSAPP", "RESPUESTA_CORREDOR", "CANCELACION",
    ]
