"""Que la fecha de un movimiento se pueda atrasar, pero no adelantar.

**Qué se abrió.** La pantalla de seguimiento fijaba la fecha en "ahora", así que
registrar la gestión del viernes el lunes la anotaba con la fecha del lunes. Ahora
se puede elegir, que es el caso real de trabajo: uno anota después.

**Qué hay que cerrar al abrirla.** La API acepta cualquier `datetime`, y una fecha
futura envenena el reloj de la bandeja --`horas_sin_gestion` es
`ahora - ultimo_movimiento`, así que daría **horas negativas** en pantalla-- y con
él el semáforo y el reporte semanal. Y una fecha anterior a que la cosa existiera
no es un dato, es un tipeo.

Los dos dominios comparten la validación porque los dos endpoints ya aceptaban
`fecha` desde antes: el hueco existía en canjes **y** en negocios, aunque solo la
pantalla de canjes lo exponga hoy.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio, Etapa, ModeloNegocio
from app.models.movimiento import EntityType, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.movimientos import (
    HOLGURA_RELOJ,
    MovimientoError,
    crear_movimiento_canje,
    crear_movimiento_negocio,
)

SOLICITUD = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def canje(db):
    db.add(TipoMovimiento(
        codigo="GESTION_INICIAL", entity_type=EntityType.canje, nombre="Gestión inicial",
        etapa_resultante="EN_REVISION", orden=1, sla_es_habil=False, activo=True,
    ))
    db.add(Canje(
        id=500,
        fecha_solicitud=SOLICITUD,
        estado=CanjeEstado.ACTIVO,
        etapa=CanjeEtapa.RECEPCION,
        comuna="Santiago",
    ))
    db.commit()
    return db


@pytest.fixture
def negocio(db):
    # La etapa tiene clave foránea desde `negocios.etapa`: sin la fila del
    # catálogo, aplicar el movimiento falla al actualizar el negocio.
    db.add(Etapa(codigo="E2", nombre="Visita", responsable="COMERCIAL", orden=2))
    db.add(TipoMovimiento(
        codigo="NEG_E2_VISITA", entity_type=EntityType.negocio, nombre="Visita",
        etapa_resultante="E2", orden=2, sla_es_habil=False, activo=True,
    ))
    prop = Propiedad(direccion="Calle 1", comuna="Santiago")
    db.add(prop)
    db.flush()
    n = Negocio(codigo="VVP-90", modelo=ModeloNegocio.MERCADO_PRIMARIO, propiedad_id=prop.id)
    n.hitos.append(NegocioHito(fecha_inicio=date(2026, 6, 1), estado=EstadoNegocio.ACTIVO))
    db.add(n)
    db.commit()
    return db, n.id


# --------------------------------------------------------- lo que sí se acepta


def test_sin_fecha_queda_la_de_ahora(canje):
    """El camino de siempre: no mandar fecha sigue funcionando igual.

    Es el defecto de la pantalla --el campo va vacío-- así que este es el caso
    habitual y no puede haber cambiado.
    """
    m = crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None)

    fecha = m.fecha if m.fecha.tzinfo else m.fecha.replace(tzinfo=timezone.utc)
    assert abs((datetime.now(timezone.utc) - fecha).total_seconds()) < 60


def test_una_fecha_pasada_se_guarda_tal_cual(canje):
    """El caso que motivó todo: anotar el lunes lo que pasó el viernes."""
    viernes = datetime(2026, 7, 10, 15, 30, tzinfo=timezone.utc)

    m = crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None, fecha=viernes)

    fecha = m.fecha if m.fecha.tzinfo else m.fecha.replace(tzinfo=timezone.utc)
    assert fecha == viernes
    # Y la etapa se aplica igual: atrasar la fecha no cambia el efecto.
    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_REVISION


def test_la_fecha_de_solicitud_misma_es_valida(canje):
    """El borde de abajo es inclusivo: gestionar el mismo día que llegó se puede."""
    m = crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None, fecha=SOLICITUD)

    assert m.id is not None


def test_se_tolera_el_desfase_de_reloj_del_navegador(canje):
    """La fecha la arma el navegador, y su reloj puede ir unos minutos adelante.

    Sin holgura, registrar un movimiento "ahora" desde una máquina adelantada se
    rechazaría por venir del futuro, que es un error incomprensible para quien lo
    ve.
    """
    apenas_futuro = datetime.now(timezone.utc) + HOLGURA_RELOJ - timedelta(seconds=30)

    m = crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None, fecha=apenas_futuro)

    assert m.id is not None


# -------------------------------------------------------- lo que se rechaza


def test_una_fecha_futura_se_rechaza(canje):
    """El que protege el reloj de la bandeja."""
    manana = datetime.now(timezone.utc) + timedelta(days=1)

    with pytest.raises(MovimientoError, match="no puede ser futura"):
        crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None, fecha=manana)


def test_una_fecha_anterior_a_la_solicitud_se_rechaza(canje):
    antes = SOLICITUD - timedelta(days=1)

    with pytest.raises(MovimientoError, match="anterior a la fecha de solicitud"):
        crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None, fecha=antes)


def test_el_rechazo_dice_cual_era_el_minimo(canje):
    """El mensaje trae las dos fechas: sin el mínimo no se sabe qué corregir."""
    with pytest.raises(MovimientoError) as exc:
        crear_movimiento_canje(
            canje, 500, "GESTION_INICIAL", autor_id=None,
            fecha=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )

    assert "15-01-2026" in str(exc.value)
    assert "01-06-2026" in str(exc.value)


def test_nada_se_guarda_cuando_la_fecha_se_rechaza(canje):
    """El movimiento no queda a medias ni el canje marcado como gestionado."""
    from app.models.movimiento import Movimiento

    with pytest.raises(MovimientoError):
        crear_movimiento_canje(
            canje, 500, "GESTION_INICIAL", autor_id=None,
            fecha=datetime.now(timezone.utc) + timedelta(days=5),
        )

    canje.rollback()
    assert canje.query(Movimiento).count() == 0
    c = canje.get(Canje, 500)
    assert c.gestionado_en_app is False
    assert c.etapa == CanjeEtapa.RECEPCION


# ------------------------------------------------------------------ negocios


def test_negocios_valida_igual_aunque_su_pantalla_no_lo_exponga(negocio):
    """El endpoint de negocios ya aceptaba `fecha`, así que tenía el mismo hueco.

    Su pantalla todavía no ofrece el campo, pero la API sí: cerrar el agujero en
    un dominio y dejarlo abierto en el otro habría sido arreglar la mitad.
    """
    db, negocio_id = negocio

    with pytest.raises(MovimientoError, match="no puede ser futura"):
        crear_movimiento_negocio(
            db, negocio_id, "NEG_E2_VISITA", autor_id=None,
            fecha=datetime.now(timezone.utc) + timedelta(days=2),
        )


def test_en_negocios_el_minimo_es_el_hito_mas_antiguo(negocio):
    """Un negocio empieza cuando empieza su primera liquidación."""
    db, negocio_id = negocio

    with pytest.raises(MovimientoError, match="anterior a la fecha de inicio del negocio"):
        crear_movimiento_negocio(
            db, negocio_id, "NEG_E2_VISITA", autor_id=None,
            fecha=datetime(2026, 5, 20, tzinfo=timezone.utc),
        )

    # Y el mismo día del inicio sí entra.
    m = crear_movimiento_negocio(
        db, negocio_id, "NEG_E2_VISITA", autor_id=None,
        fecha=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
    )
    assert m.id is not None


# ------------------------------------------------------------------ endpoint


def test_el_endpoint_rechaza_la_fecha_futura(cliente, canje):
    futuro = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    r = cliente.post(
        "/api/canjes/500/movimientos",
        json={"tipo_movimiento": "GESTION_INICIAL", "fecha": futuro},
    )

    assert r.status_code == 400, r.text
    assert "no puede ser futura" in r.json()["detail"]


def test_el_endpoint_acepta_una_fecha_pasada(cliente, canje):
    r = cliente.post(
        "/api/canjes/500/movimientos",
        json={
            "tipo_movimiento": "GESTION_INICIAL",
            "fecha": "2026-07-10T15:30:00+00:00",
            "comentario": "Se llamó al corredor el viernes",
        },
    )

    assert r.status_code == 201, r.text
    assert r.json()["fecha"].startswith("2026-07-10T15:30")


# ------------------------------------------------- la etapa no retrocede sola


def test_atrasar_un_movimiento_no_devuelve_la_etapa_atras(canje):
    """El defecto que el campo de fecha creaba, y que se arregló con él.

    Se registra el 20 un paso a «En negocio», y despues se anota --con fecha
    atrasada al 10-- una gestion anterior. Antes, la etapa del canje quedaba en la
    del movimiento recien insertado, asi que **retrocedia a «En revision»** contra
    un movimiento posterior que seguia ahi.

    La etapa vigente se deriva de la linea de tiempo, no de lo ultimo que se
    guardo.
    """
    canje.add(TipoMovimiento(
        codigo="PASO_NEGOCIO", entity_type=EntityType.canje, nombre="En negocio",
        etapa_resultante="EN_NEGOCIO", orden=5, sla_es_habil=False, activo=True,
    ))
    canje.commit()

    crear_movimiento_canje(
        canje, 500, "PASO_NEGOCIO", autor_id=None,
        fecha=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )
    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_NEGOCIO

    crear_movimiento_canje(
        canje, 500, "GESTION_INICIAL", autor_id=None,
        fecha=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )

    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_NEGOCIO, (
        "la etapa retrocedio: el movimiento del 20-07 sigue siendo el mas reciente"
    )


def test_un_movimiento_mas_nuevo_si_mueve_la_etapa(canje):
    """El otro lado: derivar de la linea de tiempo no puede congelar la etapa."""
    canje.add(TipoMovimiento(
        codigo="PASO_NEGOCIO", entity_type=EntityType.canje, nombre="En negocio",
        etapa_resultante="EN_NEGOCIO", orden=5, sla_es_habil=False, activo=True,
    ))
    canje.commit()

    crear_movimiento_canje(
        canje, 500, "GESTION_INICIAL", autor_id=None,
        fecha=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )
    crear_movimiento_canje(
        canje, 500, "PASO_NEGOCIO", autor_id=None,
        fecha=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_NEGOCIO


def test_un_comentario_atrasado_no_toca_la_etapa(canje):
    """Los tipos sin `etapa_resultante` no entran en el calculo.

    Un comentario es gestion --mueve el reloj del semaforo-- pero no mueve el
    canje de etapa, ni hacia adelante ni hacia atras.
    """
    canje.add(TipoMovimiento(
        codigo="COMENTARIO", entity_type=EntityType.canje, nombre="Comentario",
        etapa_resultante=None, orden=9, sla_es_habil=False, activo=True,
    ))
    canje.commit()

    crear_movimiento_canje(
        canje, 500, "GESTION_INICIAL", autor_id=None,
        fecha=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )
    crear_movimiento_canje(
        canje, 500, "COMENTARIO", autor_id=None,
        fecha=datetime(2026, 7, 25, tzinfo=timezone.utc), comentario="Se insiste",
    )

    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_REVISION


def test_la_cancelacion_no_se_revierte_con_gestion_posterior(canje):
    """El estado no se deriva de la linea de tiempo, y es a proposito.

    Un canje que se cancelo quedo cancelado. Que despues alguien anote otra
    gestion --o que la anote con fecha posterior-- no lo revive: deshacer una
    cancelacion es una edicion manual, no un movimiento.
    """
    canje.add(TipoMovimiento(
        codigo="CANCELACION", entity_type=EntityType.canje, nombre="Cancelación",
        etapa_resultante=None, orden=8, sla_es_habil=False, activo=True,
    ))
    canje.commit()

    crear_movimiento_canje(
        canje, 500, "CANCELACION", autor_id=None,
        fecha=datetime(2026, 7, 10, tzinfo=timezone.utc),
    )
    assert canje.get(Canje, 500).estado == CanjeEstado.CANCELADO

    crear_movimiento_canje(
        canje, 500, "GESTION_INICIAL", autor_id=None,
        fecha=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    assert canje.get(Canje, 500).estado == CanjeEstado.CANCELADO


# ---------------------------------------------------- borrar un movimiento


def test_borrar_el_unico_movimiento_no_borra_la_etapa(canje):
    """La etapa **no** se resetea, y eso se corrigio despues de romperlo.

    La primera version la devolvia a `RECEPCION` razonando que la habia puesto el
    movimiento borrado. Es cierto para un canje creado en la app y falso para los
    297 que vinieron de Dataprop: su etapa la trajo el export y ninguno de sus
    movimientos migrados declara una. Medido: borrar cualquier movimiento del canje
    360 lo mandaba de «En oferta» a «Recepcion».

    Quedarse con una etapa vieja es preferible a borrar una que era correcta.
    """
    from app.models.movimiento import Movimiento
    from app.services.movimientos import eliminar_movimiento_canje

    m = crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None,
                               comentario="Validacion interesado")
    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_REVISION

    eliminar_movimiento_canje(canje, 500, m.id)

    c = canje.get(Canje, 500)
    assert c.etapa == CanjeEtapa.EN_REVISION, "la etapa sobrevive al borrado"
    assert canje.get(Movimiento, m.id) is None
    # Y el canje sigue marcado como gestionado en la app: esa marca tambien la
    # pone editarlo a mano, asi que revertirla dejaria que la importacion
    # sobreescriba en silencio datos corregidos por una persona.
    assert c.gestionado_en_app is True


def test_borrar_uno_deja_la_etapa_del_que_queda(canje):
    """Con dos movimientos, borrar el mas nuevo devuelve la etapa al anterior."""
    from app.services.movimientos import eliminar_movimiento_canje

    canje.add(TipoMovimiento(
        codigo="PASO_NEGOCIO", entity_type=EntityType.canje, nombre="En negocio",
        etapa_resultante="EN_NEGOCIO", orden=5, sla_es_habil=False, activo=True,
    ))
    canje.commit()

    crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None,
                           fecha=datetime(2026, 7, 10, tzinfo=timezone.utc))
    nuevo = crear_movimiento_canje(canje, 500, "PASO_NEGOCIO", autor_id=None,
                                   fecha=datetime(2026, 7, 20, tzinfo=timezone.utc))
    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_NEGOCIO

    eliminar_movimiento_canje(canje, 500, nuevo.id)

    assert canje.get(Canje, 500).etapa == CanjeEtapa.EN_REVISION


def test_borrar_la_cancelacion_reactiva_el_canje(canje):
    """Si registrarla fue el error, el canje no estaba cancelado."""
    from app.services.movimientos import eliminar_movimiento_canje

    canje.add(TipoMovimiento(
        codigo="CANCELACION", entity_type=EntityType.canje, nombre="Cancelación",
        etapa_resultante=None, orden=8, sla_es_habil=False, activo=True,
    ))
    canje.commit()

    m = crear_movimiento_canje(canje, 500, "CANCELACION", autor_id=None)
    assert canje.get(Canje, 500).estado == CanjeEstado.CANCELADO

    eliminar_movimiento_canje(canje, 500, m.id)

    assert canje.get(Canje, 500).estado == CanjeEstado.ACTIVO


def test_si_queda_otra_cancelacion_el_canje_no_revive(canje):
    """Borrar una de dos cancelaciones no deshace la que sigue registrada."""
    from app.services.movimientos import eliminar_movimiento_canje

    canje.add(TipoMovimiento(
        codigo="CANCELACION", entity_type=EntityType.canje, nombre="Cancelación",
        etapa_resultante=None, orden=8, sla_es_habil=False, activo=True,
    ))
    canje.commit()

    primera = crear_movimiento_canje(canje, 500, "CANCELACION", autor_id=None,
                                     fecha=datetime(2026, 7, 10, tzinfo=timezone.utc))
    crear_movimiento_canje(canje, 500, "CANCELACION", autor_id=None,
                           fecha=datetime(2026, 7, 20, tzinfo=timezone.utc))

    eliminar_movimiento_canje(canje, 500, primera.id)

    assert canje.get(Canje, 500).estado == CanjeEstado.CANCELADO


def test_borrar_una_gestion_no_reactiva_un_canje_cancelado_por_la_importacion(canje):
    """El estado que vino de Dataprop no se toca al borrar gestion cualquiera.

    Solo borrar la cancelacion reactiva. Un canje que llego cancelado del export
    --sin movimiento de cancelacion en la app-- se queda cancelado.
    """
    from app.services.movimientos import eliminar_movimiento_canje

    c = canje.get(Canje, 500)
    c.estado = CanjeEstado.CANCELADO
    canje.commit()

    m = crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None)
    eliminar_movimiento_canje(canje, 500, m.id)

    assert canje.get(Canje, 500).estado == CanjeEstado.CANCELADO


def test_no_se_puede_borrar_un_movimiento_de_otro_canje(canje):
    """El id del movimiento no alcanza: tiene que pertenecer a ese canje."""
    from app.services.movimientos import MovimientoError, eliminar_movimiento_canje

    canje.add(Canje(
        id=501, fecha_solicitud=SOLICITUD, estado=CanjeEstado.ACTIVO,
        etapa=CanjeEtapa.RECEPCION, comuna="Santiago",
    ))
    canje.commit()
    m = crear_movimiento_canje(canje, 500, "GESTION_INICIAL", autor_id=None)

    with pytest.raises(MovimientoError, match="no pertenece al canje"):
        eliminar_movimiento_canje(canje, 501, m.id)

    from app.models.movimiento import Movimiento
    assert canje.get(Movimiento, m.id) is not None


def test_el_endpoint_borra_y_devuelve_204(cliente, canje):
    creado = cliente.post(
        "/api/canjes/500/movimientos", json={"tipo_movimiento": "GESTION_INICIAL"}
    ).json()

    r = cliente.delete(f"/api/canjes/500/movimientos/{creado['id']}")

    assert r.status_code == 204, r.text
    assert cliente.get("/api/canjes/500/movimientos").json() == []
    # La etapa no se resetea: ver `test_borrar_el_unico_movimiento_no_borra_la_etapa`.
    assert cliente.get("/api/canjes/500").json()["etapa"] == "EN_REVISION"


def test_el_endpoint_rechaza_un_movimiento_de_otro_canje(cliente, canje):
    """Con los dos canjes existiendo, para que falle por la pertenencia y no
    porque el canje no exista --que es otro error y otro camino."""
    canje.add(Canje(
        id=501, fecha_solicitud=SOLICITUD, estado=CanjeEstado.ACTIVO,
        etapa=CanjeEtapa.RECEPCION, comuna="Santiago",
    ))
    canje.commit()
    creado = cliente.post(
        "/api/canjes/500/movimientos", json={"tipo_movimiento": "GESTION_INICIAL"}
    ).json()

    r = cliente.delete(f"/api/canjes/501/movimientos/{creado['id']}")

    assert r.status_code == 400, r.text
    assert "no pertenece al canje" in r.json()["detail"]
    assert len(cliente.get("/api/canjes/500/movimientos").json()) == 1


def test_el_endpoint_404_no_aplica_a_un_canje_inexistente(cliente, canje):
    """Un canje que no existe da 400 con su propio mensaje, no el de pertenencia."""
    creado = cliente.post(
        "/api/canjes/500/movimientos", json={"tipo_movimiento": "GESTION_INICIAL"}
    ).json()

    r = cliente.delete(f"/api/canjes/999/movimientos/{creado['id']}")

    assert r.status_code == 400
    assert "Canje no encontrado" in r.json()["detail"]
