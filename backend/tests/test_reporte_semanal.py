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

Y las tres que se agregaron con la ventana unica (`D-076`):

3. **Un renglon por entidad, no por movimiento**, y los totales de la seccion
   cuentan entidades: una lista de doce renglones bajo una cifra que dice 23 es
   el desajuste que ya se habia arreglado en la bandeja.
4. **La ventana manda en las cuatro cifras**, y el umbral de estancado es su
   largo. Antes el selector movia solo una de las cuatro.
5. **Estancado se mide al cierre de la ventana**, no contra hoy: una ventana
   pasada tiene que decir lo que decia al terminar, o no se puede comparar con
   la siguiente.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, OperacionTipo
from app.models.catalogo import Catalogo, EstadoNegocio, Etapa, ModeloNegocio
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


def _mov(db, entity_type, entity_id, tipo, cuando, etapa=None, comentario="x",
         creado_en=None):
    """Un movimiento. `creado_en` se pasa para simular una carga masiva.

    Dos movimientos con el **mismo** `creado_en` al microsegundo entraron en la
    misma transaccion, que es como el reporte reconoce una carga.
    """
    db.add(Movimiento(
        entity_type=entity_type,
        entity_id=entity_id,
        tipo_movimiento=tipo,
        fecha=cuando,
        etapa_resultante=etapa,
        comentario=comentario,
        **({"creado_en": creado_en} if creado_en is not None else {}),
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
    # Las dos piezas de "que paso" van separadas: la categoria y el comentario de
    # ese registro. La primera version mandaba una sola cadena y en canjes traia
    # la categoria y tiraba el comentario, asi que el dato mas especifico de cada
    # fila no llegaba a la pantalla.
    assert seccion.avanzados[0].tipo == "WA confirmación solicitante"
    assert seccion.avanzados[0].comentario == "x"
    # No movio la etapa, pero la columna igual dice donde quedo: la etapa actual
    # del canje. Antes venia nula y la celda quedaba muda sobre toda la historia
    # migrada del Excel, que lleva `etapa_resultante` nulo a proposito.
    assert seccion.avanzados[0].movio_etapa is False
    assert seccion.avanzados[0].etapa_nombre == "En revisión"


def test_cuando_el_movimiento_si_mueve_la_etapa_la_muestra(db, tipos):
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "PASA_A_OFERTA", _hace(2), etapa="EN_OFERTA")
    db.commit()

    item = _reporte(db).canjes.avanzados[0]
    assert (item.etapa, item.etapa_nombre, item.movio_etapa) == ("EN_OFERTA", "En oferta", True)


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
    # Por que se cayo lo dice el comentario, y la categoria lo acompaña.
    assert (seccion.caidos[0].tipo, seccion.caidos[0].comentario) == ("Cancelación", "se arrepintio")


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
    _canje(db, 1, estado=CanjeEstado.CERRADO, etapa=CanjeEtapa.CERRADO, cierre=_hace(2))
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_cerrados == 1
    assert seccion.monto_cerrado == D("0")
    assert seccion.cerrados[0].detalle == "Ana Solicitante"


def test_un_cancelado_con_la_etapa_en_cierre_no_es_un_cierre(db):
    """**Los 31 del desalineamiento de Dataprop.**

    Llegaron a la etapa de firma y se cayeron igual: la etapa dice hasta donde
    llego el proceso y el estado en que termino (`D-071`). El reporte preguntaba
    por la etapa, asi que uno de esos con fecha de cierre en la ventana habria
    aparecido como un canje cerrado.
    """
    _canje(db, 1, estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.CERRADO, cierre=_hace(2))
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_cerrados == 0, "se cayo, no se cerro"
    # Y aparece donde corresponde: en las caidas, por su fecha de cancelacion.
    assert seccion.total_caidos == 1


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
    assert item.sin_gestion is True


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
    # Siete, no catorce: el umbral sale del largo de la ventana y la ventana por
    # defecto es la semana en curso.
    assert cuerpo["dias_estancado"] == 7
    assert set(cuerpo) == {"desde", "hasta", "dias_estancado", "negocios", "canjes"}


def test_el_endpoint_deja_forzar_el_umbral(cliente):
    r = cliente.get("/api/reportes/semanal", params={"dias_estancado": 30})
    assert r.json()["dias_estancado"] == 30


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


# ------------------------------- un renglon por entidad, no por movimiento


def test_el_canje_con_tres_registros_sale_una_vez_con_el_ultimo(db, tipos):
    """Lo que el usuario vio: VVP-15 tres veces y #364 dos veces en la tabla."""
    _canje(db, 1)
    for dias in (4, 3, 1):
        _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(dias))
    db.commit()

    seccion = _reporte(db).canjes
    # La cifra cuenta canjes y la lista tiene un renglon: los dos numeros cuadran.
    assert (seccion.total_avanzados, len(seccion.avanzados)) == (1, 1)
    # Y los movimientos no se pierden, van aparte.
    assert seccion.movimientos_avanzados == 3
    assert seccion.avanzados[0].registros == 3
    assert seccion.avanzados[0].fecha == _hace(1).date()


def test_el_negocio_muestra_el_comentario_del_ultimo_registro(db, tipos):
    n = _negocio(db, "VVP-1")
    _mov(db, EntityType.negocio, n.id, "NEG_LLAMADA", _hace(3), comentario="primero")
    _mov(db, EntityType.negocio, n.id, "NEG_LLAMADA", _hace(1), comentario="ultimo")
    db.commit()

    seccion = _reporte(db).negocios
    assert (seccion.total_avanzados, seccion.movimientos_avanzados) == (1, 2)
    assert seccion.avanzados[0].comentario == "ultimo"
    # Negocios tambien trae la categoria, para que las dos secciones respondan
    # "que paso" de la misma forma.
    assert seccion.avanzados[0].tipo == "Llamada"
    assert seccion.avanzados[0].registros == 2


def test_los_avanzados_van_del_mas_nuevo_al_mas_viejo(db, tipos):
    """Al reves que los estancados: con la lista topeada, lo que sobra es lo viejo."""
    for id_, dias in ((1, 1), (2, 4), (3, 2)):
        _canje(db, id_)
        _mov(db, EntityType.canje, id_, "WA_SOLICITANTE", _hace(dias))
    db.commit()

    assert [i.referencia for i in _reporte(db).canjes.avanzados] == ["#1", "#3", "#2"]


# ------------------------------ la ventana manda en las cuatro cifras


def _cuatro_semanas(db):
    return obtener_reporte_semanal(db, DOMINGO - timedelta(days=27), DOMINGO, ahora=AHORA)


def test_el_umbral_de_estancado_sale_del_largo_de_la_ventana(db):
    """Sin parametro explicito: una semana da 7 y cuatro semanas dan 28."""
    assert obtener_reporte_semanal(db, LUNES, DOMINGO, ahora=AHORA).dias_estancado == 7
    assert _cuatro_semanas(db).dias_estancado == 28


def test_la_ventana_larga_alcanza_lo_que_la_corta_deja_afuera(db, tipos):
    """La misma actividad en dos ventanas: es lo que el selector tiene que mover.

    Antes el selector solo cambiaba el umbral de estancado, asi que tres de las
    cuatro casillas no se movian y el control se leia como si moviera las cuatro.
    """
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(20))
    db.commit()

    una = obtener_reporte_semanal(db, LUNES, DOMINGO, ahora=AHORA)
    assert (una.canjes.total_avanzados, _cuatro_semanas(db).canjes.total_avanzados) == (0, 1)


def test_estancado_se_mide_al_cierre_de_la_ventana_y_no_contra_hoy(db, tipos):
    """Una ventana pasada tiene que decir lo que decia al terminar."""
    _canje(db, 1, dias_solicitud=400)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE",
         datetime(2026, 7, 10, 12, tzinfo=timezone.utc))
    db.commit()

    # Al domingo 12 de julio llevaba dos dias quieto: no estaba estancado.
    pasada = obtener_reporte_semanal(db, date(2026, 7, 6), date(2026, 7, 12), ahora=AHORA)
    assert pasada.canjes.total_estancados == 0

    # En la ventana en curso el corte es ahora, y ahi si lleva 42 dias.
    en_curso = obtener_reporte_semanal(db, LUNES, DOMINGO, ahora=AHORA)
    assert en_curso.canjes.estancados[0].dias_sin_movimiento == 42


# -------------------------------------- de que propiedad se esta hablando


@pytest.fixture
def alianza(db):
    c = Catalogo(tipo="alianza", codigo="ASSETPLAN", nombre="Assetplan")
    db.add(c)
    db.flush()
    return c


def test_el_negocio_trae_direccion_comuna_alianza_y_el_texto_de_la_etapa(db, tipos, alianza):
    n = _negocio(db, "VVP-1")
    n.alianza_id = alianza.id
    n.propiedad.unidad = "1802"
    _mov(db, EntityType.negocio, n.id, "NEG_LLAMADA", _hace(1))
    db.commit()

    item = _reporte(db).negocios.avanzados[0]
    assert item.direccion == "Calle VVP-1 1802"
    assert (item.comuna, item.alianza) == ("Nunoa", "Assetplan")
    # El texto de la etapa, no solo el codigo: "E2" no le dice nada a quien lee.
    assert (item.etapa, item.etapa_nombre) == ("E2", "Visita")


def test_el_canje_trae_operacion_direccion_y_comuna(db, tipos):
    _canje(db, 1)
    db.flush()
    canje = db.get(Canje, 1)
    canje.tipo_operacion = OperacionTipo.ARRIENDO
    canje.direccion = "Av. Siempre Viva 742"
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(1))
    db.commit()

    item = _reporte(db).canjes.avanzados[0]
    # El rotulo, no el valor guardado: "ARRIENDO" es el enum, "Arriendo" se lee.
    assert item.operacion == "Arriendo"
    assert (item.direccion, item.comuna) == ("Av. Siempre Viva 742", "Providencia")


def test_los_estancados_y_los_cerrados_tambien_dicen_de_que_hablan(db):
    """Las cuatro listas de la seccion llevan las mismas columnas."""
    _canje(db, 1, dias_solicitud=400)
    _negocio(db, "G-1", EstadoNegocio.CERRADO, cierre=date(2026, 8, 19), real=D("10"))
    db.commit()

    r = _reporte(db)
    estancado = r.canjes.estancados[0]
    assert (estancado.comuna, estancado.etapa_nombre) == ("Providencia", "En revisión")
    cerrado = r.negocios.cerrados[0]
    assert (cerrado.direccion, cerrado.comuna) == ("Calle G-1", "Nunoa")


def test_el_umbral_de_estancado_se_puede_cambiar_desde_la_query(cliente, db, tipos):
    _canje(db, 1)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", _hace(20))
    db.commit()

    assert cliente.get("/api/reportes/semanal",
                       params={"dias_estancado": 14}).json()["canjes"]["total_estancados"] == 1
    assert cliente.get("/api/reportes/semanal",
                       params={"dias_estancado": 30}).json()["canjes"]["total_estancados"] == 0


# ------------------------- los movimientos con fecha de carga no son actividad


# El instante exacto en que "corrio el script": dos o mas movimientos que lo
# comparten entraron juntos.
CARGA = AHORA - timedelta(hours=3)


def test_una_limpieza_masiva_no_llena_se_cayo(db, tipos):
    """**El caso que el usuario vio.**

    Una limpieza marco como cancelados los canjes que Dataprop dejo de exportar y
    les creo el movimiento con la fecha del dia en que corrio. En una ventana que
    incluye ese dia, «Se cayo» mostraba 215 sobre 303 canjes: cierto sobre los
    movimientos y falso sobre el negocio, porque esos canjes se cayeron en algun
    momento desconocido de los ultimos anos.
    """
    for id_ in (1, 2, 3):
        _canje(db, id_, estado=CanjeEstado.CANCELADO)
        _mov(db, EntityType.canje, id_, "CANCELACION", CARGA,
             comentario="Cancelado en la limpieza", creado_en=CARGA)
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_caidos == 0, "la fecha la puso el script, no la gestion"
    # Pero no en silencio: la pantalla tiene que poder decir que existen.
    assert seccion.movimientos_con_fecha_de_carga == 3


def test_una_carga_con_fechas_reales_si_cuenta(db, tipos):
    """**No alcanza con "vino de una carga".**

    Las 11 cancelaciones migradas del Excel entraron todas juntas, pero con las
    fechas que traia el archivo. Esas pertenecen a la ventana donde caen.
    """
    _canje(db, 1, estado=CanjeEstado.CANCELADO)
    _canje(db, 2, estado=CanjeEstado.CANCELADO)
    # Las dos comparten el instante de creacion --misma transaccion-- pero sus
    # fechas son de dias distintos y anteriores.
    _mov(db, EntityType.canje, 1, "CANCELACION", _hace(2), creado_en=CARGA)
    _mov(db, EntityType.canje, 2, "CANCELACION", _hace(3), creado_en=CARGA)
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_caidos == 2
    assert seccion.movimientos_con_fecha_de_carga == 0


def test_una_cancelacion_registrada_hoy_en_la_app_cuenta(db, tipos):
    """Tambien tiene fecha de hoy, y esa **si** es una gestion.

    Lo que la distingue de la limpieza es que su `creado_en` no lo comparte nadie:
    entro sola.
    """
    _canje(db, 1, estado=CanjeEstado.CANCELADO)
    _mov(db, EntityType.canje, 1, "CANCELACION", AHORA, creado_en=AHORA)
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_caidos == 1
    assert seccion.movimientos_con_fecha_de_carga == 0


def test_la_regla_no_es_solo_para_las_cancelaciones(db, tipos):
    """Vale para cualquier tipo: lo que se descarta es una fecha inventada."""
    _canje(db, 1)
    _canje(db, 2)
    _mov(db, EntityType.canje, 1, "WA_SOLICITANTE", CARGA, creado_en=CARGA)
    _mov(db, EntityType.canje, 2, "WA_SOLICITANTE", CARGA, creado_en=CARGA)
    db.commit()

    seccion = _reporte(db).canjes
    assert (seccion.total_avanzados, seccion.movimientos_avanzados) == (0, 0)
    assert seccion.movimientos_con_fecha_de_carga == 2


def test_los_negocios_usan_la_misma_regla(db, tipos):
    """El historial de negocios se cargo con fechas reales, asi que no cambia.

    Pero la regla esta puesta igual: una carga futura que estampe "hoy" no puede
    aparecer como actividad de la ventana.
    """
    n1 = _negocio(db, "VVP-1")
    n2 = _negocio(db, "VVP-2")
    _mov(db, EntityType.negocio, n1.id, "NEG_LLAMADA", CARGA, creado_en=CARGA)
    _mov(db, EntityType.negocio, n2.id, "NEG_LLAMADA", CARGA, creado_en=CARGA)
    # Y uno con fecha real cargado en la misma transaccion.
    _mov(db, EntityType.negocio, n1.id, "NEG_LLAMADA", _hace(2), creado_en=CARGA)
    db.commit()

    seccion = _reporte(db).negocios
    assert seccion.total_avanzados == 1, "solo el de fecha real"
    assert seccion.movimientos_con_fecha_de_carga == 2


# ------------------ las cancelaciones que solo existen como fecha de cierre


def test_una_cancelacion_sin_movimiento_se_cuenta_por_su_fecha_de_cierre(db):
    """**El defecto que el usuario encontro.**

    Dataprop manda la fecha de cancelacion de los canjes recientes --47 de 293, y
    nueve en agosto-- y esos canjes no tienen movimiento de cancelacion: no se
    cancelaron en la app. Mirando solo los movimientos, «Se cayo» daba cero en
    todas las ventanas y el usuario sabia que en agosto si hubo cancelaciones.
    """
    _canje(db, 1, estado=CanjeEstado.CANCELADO, cierre=_hace(2))
    _canje(db, 2, estado=CanjeEstado.CANCELADO, cierre=_hace(30))
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_caidos == 1, "solo el de la ventana"
    item = seccion.caidos[0]
    assert (item.referencia, item.fecha) == ("#1", _hace(2).date())
    # La fila no tiene autor ni comentario, asi que dice de donde viene la fecha.
    assert item.tipo == "Cancelado"
    assert "export de Dataprop" in item.comentario
    assert item.registros == 0


def test_el_movimiento_le_gana_a_la_fecha_de_cierre(db, tipos):
    """Si la app registro la cancelacion, esa es la version con autor y comentario.

    Sin esta preferencia el canje saldria dos veces: una por el movimiento y otra
    por la fecha del export.
    """
    _canje(db, 1, estado=CanjeEstado.CANCELADO, cierre=_hace(2))
    _mov(db, EntityType.canje, 1, "CANCELACION", _hace(3), comentario="se arrepintio")
    db.commit()

    seccion = _reporte(db).canjes
    assert seccion.total_caidos == 1, "un canje, una caida"
    assert seccion.caidos[0].comentario == "se arrepintio"
    assert seccion.caidos[0].registros == 1


def test_un_cancelado_sin_fecha_de_cierre_no_cae_en_ninguna_ventana(db):
    """Los 246 viejos: la fecha no existe, y no se puede inventar.

    Aparecen en el dashboard como cancelados --eso es estado, no fecha-- pero
    ninguna ventana puede reclamarlos.
    """
    _canje(db, 1, estado=CanjeEstado.CANCELADO, cierre=None)
    db.commit()

    assert _reporte(db).canjes.total_caidos == 0
