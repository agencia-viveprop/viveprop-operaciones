"""El listado de canjes activos con su estado de gestion.

Lo que se fija: que es un **reporte** y no una lista de trabajo. La diferencia
concreta es que muestra todos los activos, incluso los agendados a futuro que la
bandeja esconde a proposito, y que el estado se calcula sobre `fecha` --cuando se
hizo la gestion-- y no sobre `creado_en` --cuando quedo registrada--.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.services.canjes_activos import (
    AL_DIA,
    PENDIENTE,
    clasificar,
    obtener_listado,
)

AHORA = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
HOY = AHORA.date()


@pytest.fixture(autouse=True)
def tipos(db):
    db.add_all([
        TipoMovimiento(
            codigo="SEG_LLAMADO", nombre="Seguimiento - Llamado",
            entity_type=EntityType.canje, activo=True, orden=2,
        ),
        TipoMovimiento(
            codigo="GESTION_INICIAL", nombre="Gestion Inicial",
            entity_type=EntityType.canje, activo=True, orden=1,
        ),
    ])
    db.commit()


def _canje(db, id_, etapa=CanjeEtapa.EN_REVISION, estado=CanjeEstado.ACTIVO):
    c = Canje(
        id=id_, fecha_solicitud=datetime(2026, 6, 1, tzinfo=timezone.utc),
        estado=estado, etapa=etapa, comuna="Santiago",
        corredor_solicitante_nombre="Ana", corredor_propietario_nombre="Beto",
    )
    db.add(c)
    db.commit()
    return c


def _mov(db, canje_id, fecha, codigo="SEG_LLAMADO", seguimiento=None, creado_en=None, comentario=None):
    m = Movimiento(
        entity_type=EntityType.canje, entity_id=canje_id, tipo_movimiento=codigo,
        fecha=fecha, proximo_seguimiento=seguimiento, comentario=comentario,
    )
    if creado_en is not None:
        m.creado_en = creado_en
    db.add(m)
    db.commit()
    return m


# ------------------------------------------------------------- la clasificacion


def test_el_compromiso_manda_sobre_el_tiempo():
    """Un canje agendado a futuro esta al dia aunque lleve un mes sin gestion.

    Es exactamente lo que significa haberlo agendado. La misma regla que la
    bandeja: el tiempo sin gestion es una inferencia y el compromiso es un hecho.
    """
    assert clasificar(horas=720, dias_de_atraso=-3) == AL_DIA
    assert clasificar(horas=720, dias_de_atraso=0) == AL_DIA
    assert clasificar(horas=720, dias_de_atraso=1) == PENDIENTE
    # Y al reves: recien gestionado pero con el compromiso vencido.
    assert clasificar(horas=1, dias_de_atraso=5) == PENDIENTE


def test_sin_compromiso_manda_el_umbral():
    assert clasificar(horas=47.9, dias_de_atraso=None) == AL_DIA
    assert clasificar(horas=48, dias_de_atraso=None) == PENDIENTE


def test_nunca_gestionado_es_pendiente():
    """Trabajo sin empezar. En un reporte de dos estados no hay otro lugar."""
    assert clasificar(horas=None, dias_de_atraso=None) == PENDIENTE


# --------------------------------------------------------------- el listado


def test_muestra_los_agendados_a_futuro_que_la_bandeja_esconde(db):
    """La diferencia que separa este reporte de la lista de trabajo.

    La bandeja saca de la vista lo agendado para adelante --si te comprometiste a
    llamar el jueves, el martes no es tu problema--. Un reporte no puede: alguien
    lo lee para saber cuantos canjes abiertos hay.
    """
    _canje(db, 1)
    _mov(db, 1, AHORA - timedelta(days=10), seguimiento=HOY + timedelta(days=4))

    listado = obtener_listado(db, ahora=AHORA)

    assert [f.canje_id for f in listado.filas] == [1]
    assert listado.filas[0].estado == AL_DIA
    assert listado.filas[0].dias_de_atraso == -4


def test_el_estado_sale_de_la_fecha_de_gestion_no_de_la_de_registro(db):
    """Dos canjes con el mismo registro y distinta gestion.

    El que se gestiono hoy esta al dia aunque se haya cargado igual que el otro;
    el que se gestiono hace una semana esta pendiente aunque se haya registrado
    recien. "Hace cuanto que nadie toca este canje" es una pregunta sobre el
    trabajo, no sobre cuando se tipeo.
    """
    _canje(db, 1)
    _canje(db, 2)
    _mov(db, 1, AHORA - timedelta(hours=2), creado_en=AHORA)
    _mov(db, 2, AHORA - timedelta(days=7), creado_en=AHORA)

    por_id = {f.canje_id: f for f in obtener_listado(db, ahora=AHORA).filas}

    assert por_id[1].estado == AL_DIA
    assert por_id[2].estado == PENDIENTE


def test_el_registro_tardio_se_informa_sin_cambiar_el_estado(db):
    """El dato va al lado del movimiento, no en el semaforo.

    Si se registro tarde no cambia que la gestion ocurrio cuando ocurrio. Pero se
    dice, porque sin eso un registro atrasado deja un canje con cara de al dia y
    nadie puede saber por que.
    """
    _canje(db, 1)
    # Gestionado hace dos horas y registrado en el momento: nada que informar.
    _mov(db, 1, AHORA - timedelta(hours=2), creado_en=AHORA)
    # Gestionado hace tres horas, registrado nueve dias despues.
    _mov(db, 1, AHORA - timedelta(hours=3), creado_en=AHORA + timedelta(days=9))

    fila = obtener_listado(db, ahora=AHORA).filas[0]

    assert fila.estado == AL_DIA, "el estado no lo decide el registro"
    tardios = [m.dias_hasta_el_registro for m in fila.movimientos]
    assert tardios == [None, 9], "el mas reciente primero: el de las 2 horas"


def test_el_historial_va_del_mas_nuevo_al_mas_viejo(db):
    """Lo primero que se lee es lo ultimo que paso.

    Se desplego al reves --cronologico, para leerlo como una historia-- hasta que
    el usuario lo uso con sus datos: en un canje con catorce registros, lo que uno
    abre a mirar es en que quedo, y con orden ascendente habia que recorrer la
    lista entera para llegar. El cambio de criterio es de `D-080`.

    **La lista interna del servicio sigue siendo ascendente**: `movimientos[-1]`
    es la ultima gestion y las cargas se cuentan recorriendo en orden. Lo que se
    invierte es la respuesta.
    """
    _canje(db, 1)
    for dia, texto in ((3, "primero"), (2, "segundo"), (1, "tercero")):
        _mov(db, 1, AHORA - timedelta(days=dia), comentario=texto)

    fila = obtener_listado(db, ahora=AHORA).filas[0]

    assert [m.comentario for m in fila.movimientos] == ["tercero", "segundo", "primero"]
    # Y la cifra de la fila no se movio con el orden: sigue siendo la mas nueva.
    # Se compara la fecha y no el instante porque SQLite --la base de los tests--
    # devuelve el timestamp sin zona y Postgres con ella.
    assert fila.ultima_gestion.date() == (AHORA - timedelta(days=1)).date()


def test_un_movimiento_sin_seguimiento_no_borra_el_compromiso(db):
    """La regla de `D-061`, que este listado tiene que respetar igual.

    Corregir la etapa crea un movimiento sin compromiso. Si se mirara el del
    ultimo movimiento, esa correccion borraria lo que se prometio antes.
    """
    _canje(db, 1)
    _mov(db, 1, AHORA - timedelta(days=5), seguimiento=HOY + timedelta(days=2))
    _mov(db, 1, AHORA - timedelta(days=1))

    fila = obtener_listado(db, ahora=AHORA).filas[0]

    assert fila.proximo_seguimiento == HOY + timedelta(days=2)
    assert fila.estado == AL_DIA


def test_los_cancelados_y_los_cerrados_no_entran(db):
    """Abierto es ACTIVO y etapa distinta de Cierre, igual que la bandeja."""
    _canje(db, 1)
    _canje(db, 2, estado=CanjeEstado.CANCELADO)
    _canje(db, 3, etapa=CanjeEtapa.CERRADO)

    assert [f.canje_id for f in obtener_listado(db, ahora=AHORA).filas] == [1]


def test_primero_los_pendientes_y_el_mas_abandonado_arriba(db):
    """El orden en que uno querria atacarlos."""
    _canje(db, 1)
    _canje(db, 2)
    _canje(db, 3)
    _mov(db, 1, AHORA - timedelta(hours=1))       # al dia
    _mov(db, 2, AHORA - timedelta(days=3))        # pendiente
    _mov(db, 3, AHORA - timedelta(days=30))       # pendiente, el peor

    listado = obtener_listado(db, ahora=AHORA)

    assert [f.canje_id for f in listado.filas] == [3, 2, 1]
    assert listado.pendientes == 2
    assert listado.al_dia == 1
    assert listado.umbral_horas == 48


def test_sin_canjes_abiertos_no_falla(db):
    listado = obtener_listado(db, ahora=AHORA)
    assert listado.filas == []
    assert listado.pendientes == 0


def test_las_horas_sin_gestion_son_nulas_y_no_cero(db):
    """Nulo es "nunca se gestiono"; cero seria "se gestiono ahora mismo"."""
    _canje(db, 1)

    fila = obtener_listado(db, ahora=AHORA).filas[0]

    assert fila.horas_sin_gestion is None
    assert fila.ultima_gestion is None
    assert fila.movimientos == []
    assert fila.estado == PENDIENTE


def test_el_endpoint_responde(cliente):
    r = cliente.get("/api/canjes/reportes/activos")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert set(cuerpo) == {"filas", "al_dia", "pendientes", "umbral_horas"}


def test_los_registros_de_una_carga_no_llevan_el_aviso_de_atraso(db):
    """Una carga masiva es, por definicion, un registro posterior a la gestion.

    Decirlo en cada linea deja de ser una senal y se vuelve empapelado: en el
    historico son 605 movimientos, todos con el mismo aviso. Se distinguen porque
    **comparten el `creado_en` al microsegundo**: una carga es una sola
    transaccion, y esa coincidencia exacta no pasa por casualidad.

    La primera hipotesis --"los migrados no tienen autor"-- era falsa: 384 de
    ellos si tienen, porque la carga corrio como el usuario admin.
    """
    _canje(db, 1)
    carga = AHORA - timedelta(days=1)
    # Tres que entraron juntos, con gestiones viejas.
    for dia in (40, 30, 20):
        _mov(db, 1, AHORA - timedelta(days=dia), creado_en=carga)
    # Y uno registrado desde la app, tarde, con su propio instante.
    _mov(db, 1, AHORA - timedelta(days=9), creado_en=AHORA)

    fila = obtener_listado(db, ahora=AHORA).filas[0]

    de_carga = [m.de_carga_masiva for m in fila.movimientos]
    assert de_carga == [False, True, True, True], "el de la app es el mas reciente"
    # Los tres de la carga, sin aviso; el de la app, con el suyo.
    avisos = [m.dias_hasta_el_registro for m in fila.movimientos]
    assert avisos == [9, None, None, None]

    assert fila.registros_de_carga == 3
    assert fila.fecha_de_carga == carga.date()


def test_un_movimiento_solo_no_es_una_carga(db):
    """Si entro solo, su instante no lo comparte nadie y el aviso aplica."""
    _canje(db, 1)
    _mov(db, 1, AHORA - timedelta(days=20), creado_en=AHORA)

    fila = obtener_listado(db, ahora=AHORA).filas[0]

    assert fila.movimientos[0].de_carga_masiva is False
    assert fila.movimientos[0].dias_hasta_el_registro == 20
    assert fila.registros_de_carga == 0
    assert fila.fecha_de_carga is None
