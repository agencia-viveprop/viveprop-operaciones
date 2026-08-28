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
        # El que escribe el sistema al editar la etapa en la ficha. Inactivo
        # porque nadie lo elige, pero tiene que existir: `movimientos.
        # tipo_movimiento` tiene clave foránea contra el catálogo.
        TipoMovimiento(codigo="CAMBIO_ETAPA", entity_type=EntityType.canje,
                       nombre="Cambio de etapa", etapa_resultante=None, orden=90,
                       sla_es_habil=False, activo=False),
    ])
    db.add(Canje(id=1, fecha_solicitud=SOLICITUD, estado=CanjeEstado.ACTIVO,
                 etapa=CanjeEtapa.EN_REVISION, comuna="Santiago"))
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

    assert base.get(Canje, 1).etapa == CanjeEtapa.EN_REVISION


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


def test_el_ciclo_tiene_cinco_etapas_y_arranca_en_revision():
    """`RECEPCION` se fue, y con ella la etapa que nadie usaba (`D-081`).

    Nacio como `SIN_ETAPA` --describia que el export de Dataprop no traia etapa--
    y `b8f3a71c904e` la renombro suponiendo que un canje que entro y no avanzo
    esta "en recepcion". Medido en produccion: los tramos daban 0 dias y los 75
    canjes que la tenian estaban todos cancelados.

    El valor sigue en el tipo de Postgres porque un enum no admite quitarlo; lo
    que se fija aca es que la app no lo conoce mas.
    """
    assert not hasattr(CanjeEtapa, "RECEPCION")
    assert not hasattr(CanjeEtapa, "SIN_ETAPA")
    assert [e.value for e in CanjeEtapa] == [
        "EN_REVISION", "PROCESO_DE_ACUERDO", "EN_OFERTA", "EN_NEGOCIO", "CERRADO",
    ]


def test_un_canje_nuevo_arranca_en_revision(db):
    """La primera etapa en la que alguien hace algo."""
    canje = Canje(id=900, fecha_solicitud=SOLICITUD)
    db.add(canje)
    db.commit()

    assert db.get(Canje, 900).etapa == CanjeEtapa.EN_REVISION


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


# --------------------------------- el rastro del cambio hecho en la ficha


def test_cambiar_la_etapa_en_la_ficha_deja_rastro(cliente, base):
    """El hueco que esto cierra.

    La etapa se puede cambiar por dos caminos --registrar un movimiento o editar
    la ficha-- y el segundo no dejaba nada en la linea de tiempo. Medido en `dev`:
    se editaba la ficha a «En oferta» y la bitacora seguia mostrando que el ultimo
    movimiento la habia dejado en «En negocio». Las dos pantallas decian cosas
    distintas y el cambio no tenia fecha ni autor.
    """
    ficha = cliente.get("/api/canjes/1").json()
    assert ficha["etapa"] == "EN_REVISION"

    r = cliente.patch("/api/canjes/1", json={"etapa": "EN_OFERTA"})

    assert r.status_code == 200, r.text
    assert r.json()["etapa"] == "EN_OFERTA"

    movs = cliente.get("/api/canjes/1/movimientos").json()
    assert len(movs) == 1, "el cambio quedo registrado"
    assert movs[0]["tipo_movimiento"] == "CAMBIO_ETAPA"
    assert movs[0]["etapa_resultante"] == "EN_OFERTA"
    # El comentario dice de donde a donde, con los rotulos y no los codigos: lo
    # lee una persona en la linea de tiempo, y "EN_OFERTA" ahi es ruido.
    assert "En revisión" in movs[0]["comentario"]
    assert "En oferta" in movs[0]["comentario"]
    assert "ficha del canje" in movs[0]["comentario"]


def test_editar_la_ficha_sin_tocar_la_etapa_no_registra_nada(cliente, base):
    """Solo el cambio de etapa deja rastro. Corregir un email no es historial."""
    r = cliente.patch("/api/canjes/1", json={"comuna": "Providencia"})

    assert r.status_code == 200
    assert cliente.get("/api/canjes/1/movimientos").json() == []


def test_guardar_la_misma_etapa_no_registra_nada(cliente, base):
    """Apretar Guardar sin cambiar la etapa no puede ensuciar la bitacora."""
    cliente.patch("/api/canjes/1", json={"etapa": "EN_REVISION"})

    assert cliente.get("/api/canjes/1/movimientos").json() == []


def test_el_tipo_del_rastro_no_se_ofrece_en_el_selector(cliente, base):
    """Nadie lo elige: lo escribe el sistema. Existe para la clave foranea."""
    codigos = [t["codigo"] for t in cliente.get("/api/tipos-movimiento?entity_type=canje").json()]

    assert "CAMBIO_ETAPA" not in codigos


def test_el_rastro_no_agenda_seguimiento_ni_borra_el_que_habia(cliente, base):
    """Corregir un dato no es una gestion.

    Y por eso la bandeja toma el ultimo compromiso **que exista** y no el del
    ultimo movimiento: si mirara solo el mas reciente, este registro borraria el
    compromiso que habia y el canje reapareceria en «Que me toca hoy» por una
    razon que nadie eligio.
    """
    from datetime import date, timedelta

    from app.services.bandeja_canjes import obtener_bandeja

    manana = date.today() + timedelta(days=1)
    cliente.post("/api/canjes/1/movimientos", json={
        "tipo_movimiento": "SEG_LLAMADO",
        "etapa": "EN_REVISION",
        "proximo_seguimiento": manana.isoformat(),
    })
    assert obtener_bandeja(base).resumen.agendados == 1

    cliente.patch("/api/canjes/1", json={"etapa": "EN_OFERTA"})

    movs = cliente.get("/api/canjes/1/movimientos").json()
    assert movs[0]["tipo_movimiento"] == "CAMBIO_ETAPA"
    assert movs[0]["proximo_seguimiento"] is None, "no agenda nada"
    # Y el compromiso que habia sigue en pie.
    b = obtener_bandeja(base)
    assert b.resumen.agendados == 1, "el canje sigue agendado, no reaparecio"
    assert b.filas == []


def test_las_dos_vias_quedan_en_la_misma_linea_de_tiempo(cliente, base):
    """Es el punto: un solo historial, sin importar por dónde se cambió."""
    cliente.post("/api/canjes/1/movimientos", json={
        "tipo_movimiento": "SEG_LLAMADO", "etapa": "EN_REVISION",
        "fecha": "2026-07-01T10:00:00+00:00",
    })
    cliente.patch("/api/canjes/1", json={"etapa": "EN_NEGOCIO"})

    movs = cliente.get("/api/canjes/1/movimientos").json()

    # Más nuevo primero, que es como los ordena el endpoint.
    assert [m["tipo_movimiento"] for m in movs] == ["CAMBIO_ETAPA", "SEG_LLAMADO"]
    assert [m["etapa_resultante"] for m in movs] == ["EN_NEGOCIO", "EN_REVISION"]
    # Y la ficha coincide con lo último de la bitácora, que es lo que antes no pasaba.
    assert cliente.get("/api/canjes/1").json()["etapa"] == movs[0]["etapa_resultante"]


# ------------------------------- sobre quien se hizo la gestion


def test_se_registra_sobre_cual_corredor(base):
    """El tercer dato de la gestion: que se hizo, donde quedo, y a quien.

    Sin esto, "Seguimiento - Llamado, 3 veces" no dice si se insistio tres veces
    al mismo corredor o una vez a cada uno, y un reporte de gestion no puede
    separar quien no contesta.
    """
    from app.models.canje import CorredorCanje

    m = crear_movimiento_canje(base, 1, "SEG_LLAMADO", autor_id=None,
                               corredor=CorredorCanje.PROPIETARIO)

    assert m.corredor == "PROPIETARIO"


def test_el_corredor_es_optativo(base):
    """Hay gestiones que no son sobre ninguno de los dos.

    Una cancelacion o un comentario general no se le hacen a un corredor.
    Forzar la eleccion obligaria a poner un dato falso.
    """
    m = crear_movimiento_canje(base, 1, "CANCELACION", autor_id=None)

    assert m.corredor is None


def test_los_tres_datos_conviven_en_el_mismo_registro(base):
    """Tipo, etapa y corredor son independientes entre si."""
    from app.models.canje import CorredorCanje

    m = crear_movimiento_canje(base, 1, "SEG_WHATSAPP", autor_id=None,
                               etapa=CanjeEtapa.EN_OFERTA,
                               corredor=CorredorCanje.SOLICITANTE)

    assert (m.tipo_movimiento, m.etapa_resultante, m.corredor) == (
        "SEG_WHATSAPP", "EN_OFERTA", "SOLICITANTE",
    )


def test_el_rastro_de_cambio_de_etapa_no_lleva_corredor(cliente, base):
    """Editar la etapa en la ficha no es una gestion sobre un corredor."""
    cliente.patch("/api/canjes/1", json={"etapa": "EN_OFERTA"})

    movs = cliente.get("/api/canjes/1/movimientos").json()
    assert movs[0]["tipo_movimiento"] == "CAMBIO_ETAPA"
    assert movs[0]["corredor"] is None


def test_el_endpoint_acepta_los_tres(cliente, base):
    r = cliente.post("/api/canjes/1/movimientos", json={
        "tipo_movimiento": "SEG_LLAMADO",
        "etapa": "EN_NEGOCIO",
        "corredor": "PROPIETARIO",
    })

    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert (cuerpo["tipo_movimiento"], cuerpo["etapa_resultante"], cuerpo["corredor"]) == (
        "SEG_LLAMADO", "EN_NEGOCIO", "PROPIETARIO",
    )


def test_el_endpoint_rechaza_un_corredor_que_no_existe(cliente, base):
    r = cliente.post("/api/canjes/1/movimientos", json={
        "tipo_movimiento": "SEG_LLAMADO", "corredor": "AMBOS",
    })

    assert r.status_code == 422


def test_los_migrados_quedan_sin_corredor(base):
    """El Excel no traia el dato: nulo dice la verdad, y adivinarlo habria sido
    inventar historial."""
    base.add(Movimiento(
        entity_type=EntityType.canje, entity_id=1, tipo_movimiento="ACUERDO_FIRMADO",
        fecha=datetime(2026, 7, 1, tzinfo=timezone.utc), comentario="Migrado del Excel",
    ))
    base.commit()

    m = base.query(Movimiento).filter_by(comentario="Migrado del Excel").one()
    assert m.corredor is None
