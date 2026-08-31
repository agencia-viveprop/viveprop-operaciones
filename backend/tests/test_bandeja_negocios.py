"""Tests de las duraciones y la bandeja de negocios.

Las propiedades que fijan:

1. **El nulo significa "no se sabe", no cero.** Los 7 negocios históricos tienen
   la misma fecha de inicio y de cierre porque el Excel traía una sola, así que su
   duración es desconocida. Decir "duró 0 días" seria presentar un dato malo como
   un hecho -- el mismo error que un porcentaje contra cero.
2. **La última gestión es la del último movimiento, no `actualizado_en`.** Esa
   columna se mueve con cualquier edición: corregir una dirección haría que un
   negocio parezca activo sin que haya pasado nada.
3. **"Cuándo se hizo algo" y "cuándo cambió de etapa" son dos preguntas.** Un
   negocio puede tener diez movimientos de gestión sin salir de E4.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.catalogo import EstadoNegocio, Etapa, ModeloNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.bandeja_negocios import (
    UMBRAL_ADVERTENCIA,
    UMBRAL_CRITICO,
    clasificar,
    duraciones_de,
    obtener_bandeja_negocios,
)

HOY = date(2026, 8, 21)


@pytest.fixture(autouse=True)
def etapas(db):
    db.add_all([
        Etapa(codigo="E2", nombre="Visita", responsable="COMERCIAL", orden=2),
        Etapa(codigo="E4", nombre="Documentación", responsable="OPERACIONES", orden=4),
    ])
    db.commit()


@pytest.fixture
def tipos(db):
    db.add_all([
        TipoMovimiento(codigo="NEG_LLAMADA", entity_type=EntityType.negocio,
                       nombre="Llamada al cliente", etapa_resultante=None,
                       orden=1, sla_es_habil=False, activo=True),
        TipoMovimiento(codigo="NEG_A_E4", entity_type=EntityType.negocio,
                       nombre="Pasa a documentación", etapa_resultante="E4",
                       orden=2, sla_es_habil=False, activo=True),
    ])
    db.commit()
    return db


def _negocio(db, codigo, etapa="E2", hitos=None):
    prop = Propiedad(direccion=f"Calle {codigo}", comuna="Santiago")
    db.add(prop)
    n = Negocio(codigo=codigo, modelo=ModeloNegocio.MERCADO_PRIMARIO, propiedad=prop, etapa=etapa)
    n.hitos = hitos or [NegocioHito(fecha_inicio=date(2026, 1, 10), estado=EstadoNegocio.ACTIVO)]
    db.add(n)
    db.commit()
    return n


def _mov(db, negocio_id, tipo, dias_atras, etapa=None):
    db.add(Movimiento(
        entity_type=EntityType.negocio, entity_id=negocio_id, tipo_movimiento=tipo,
        etapa_resultante=etapa,
        fecha=datetime.combine(HOY, datetime.min.time(), tzinfo=timezone.utc)
        - timedelta(days=dias_atras),
        comentario="x",
    ))
    db.commit()


# ------------------------------------------------- el nulo no es cero


def test_si_inicio_y_cierre_coinciden_las_dos_duraciones_son_desconocidas():
    """El caso de los 7 historicos: el Excel traia una sola fecha.

    Las **dos** son nulas, y esa correccion vino de ver el resultado real: el
    listado mostraba `dias_abierto = 0` para VVP-1, que empezo en agosto de 2025,
    y la tabla lo pintaba como "hoy". No sabemos que cerro el dia que empezo;
    sabemos que la migracion puso la misma fecha en las dos columnas.
    """
    d = duraciones_de(date(2026, 3, 9), date(2026, 3, 9), None, None, HOY, abierto=False)

    assert d.dias_hasta_el_cierre is None
    assert d.dias_abierto is None


def test_con_fechas_distintas_si_hay_duracion():
    d = duraciones_de(date(2026, 1, 10), date(2026, 3, 9), None, None, HOY, abierto=False)

    assert d.dias_hasta_el_cierre == 58


def test_un_negocio_abierto_cuenta_hasta_hoy():
    d = duraciones_de(date(2026, 1, 10), None, None, None, HOY, abierto=True)

    assert d.dias_abierto == 223
    assert d.dias_hasta_el_cierre is None


def test_un_negocio_cerrado_no_sigue_envejeciendo():
    """Llevo lo que duro, no lo que lleva desde que empezo."""
    cerrado = duraciones_de(date(2026, 1, 10), date(2026, 3, 9), None, None, HOY, abierto=False)
    abierto = duraciones_de(date(2026, 1, 10), None, None, None, HOY, abierto=True)

    assert cerrado.dias_abierto == 58
    assert abierto.dias_abierto == 223


def test_sin_movimientos_las_dos_duraciones_de_gestion_son_nulas():
    d = duraciones_de(date(2026, 1, 10), None, None, None, HOY, abierto=True)

    assert d.dias_sin_gestion is None
    assert d.dias_en_etapa is None


# ------------------------------------- gestion y cambio de etapa son distintos


def test_diez_gestiones_sin_cambiar_de_etapa(db, tipos):
    """El caso que obliga a separar las dos preguntas."""
    n = _negocio(db, "VVP-100")
    _mov(db, n.id, "NEG_A_E4", 60, etapa="E4")   # cambio de etapa hace dos meses
    for dias in (10, 8, 5, 2):                    # gestion reciente, misma etapa
        _mov(db, n.id, "NEG_LLAMADA", dias)

    b = obtener_bandeja_negocios(db, hoy=HOY)
    d = b.filas[0].duraciones

    assert d.dias_sin_gestion == 2    # se trabajo hace dos dias
    assert d.dias_en_etapa == 60      # pero lleva dos meses en la misma etapa


def test_el_nombre_del_ultimo_movimiento_es_el_del_ultimo(db, tipos):
    n = _negocio(db, "VVP-100")
    _mov(db, n.id, "NEG_A_E4", 30, etapa="E4")
    _mov(db, n.id, "NEG_LLAMADA", 3)

    fila = obtener_bandeja_negocios(db, hoy=HOY).filas[0]

    assert fila.ultimo_movimiento_nombre == "Llamada al cliente"


# ------------------------------------------------------------ semaforo


@pytest.mark.parametrize("dias, esperado", [
    (None, "sin_gestion"),
    (0, "al_dia"),
    (13, "al_dia"),
    (UMBRAL_ADVERTENCIA, "advertencia"),
    (29, "advertencia"),
    (UMBRAL_CRITICO, "critico"),
    (200, "critico"),
])
def test_los_umbrales_son_en_dias(dias, esperado):
    """En horas no distinguirian nada: acá los procesos duran meses."""
    assert clasificar(dias) == esperado


def test_sin_gestion_es_un_nivel_aparte_no_critico(db, tipos):
    """Misma razon que en canjes (`D-029`): si no, la bandeja abre toda en rojo."""
    _negocio(db, "VVP-100")                       # sin movimientos
    n2 = _negocio(db, "VVP-101")
    _mov(db, n2.id, "NEG_LLAMADA", 60)            # abandonado

    r = obtener_bandeja_negocios(db, hoy=HOY).resumen

    assert (r.sin_gestion, r.critico) == (1, 1)


def test_el_orden_pone_primero_lo_que_nunca_se_toco(db, tipos):
    _negocio(db, "AL-DIA")
    n2 = _negocio(db, "CRITICO")
    n3 = _negocio(db, "SIN-TOCAR")
    _mov(db, n2.id, "NEG_LLAMADA", 60)
    _mov(db, db.query(Negocio).filter_by(codigo="AL-DIA").one().id, "NEG_LLAMADA", 1)

    codigos = [f.codigo for f in obtener_bandeja_negocios(db, hoy=HOY).filas]

    assert codigos.index("SIN-TOCAR") < codigos.index("CRITICO")
    assert codigos.index("CRITICO") < codigos.index("AL-DIA")
    assert n3.codigo == "SIN-TOCAR"


def test_dentro_del_mismo_nivel_manda_lo_mas_antiguo(db):
    """Lo que lleva mas tiempo abierto acumula mas riesgo."""
    _negocio(db, "NUEVO", hitos=[NegocioHito(fecha_inicio=date(2026, 8, 1), estado=EstadoNegocio.ACTIVO)])
    _negocio(db, "VIEJO", hitos=[NegocioHito(fecha_inicio=date(2026, 1, 5), estado=EstadoNegocio.ACTIVO)])

    codigos = [f.codigo for f in obtener_bandeja_negocios(db, hoy=HOY).filas]

    assert codigos == ["VIEJO", "NUEVO"]


# --------------------------------------------------- que entra en la bandeja


def test_solo_entran_los_que_tienen_una_liquidacion_abierta(db):
    _negocio(db, "ACTIVO")
    _negocio(db, "CERRADO", hitos=[
        NegocioHito(fecha_inicio=date(2026, 1, 10), fecha_cierre=date(2026, 3, 1),
                    estado=EstadoNegocio.CERRADO)])
    _negocio(db, "PERDIDO", hitos=[
        NegocioHito(fecha_inicio=date(2026, 1, 10), estado=EstadoNegocio.PERDIDO)])

    codigos = [f.codigo for f in obtener_bandeja_negocios(db, hoy=HOY).filas]

    assert codigos == ["ACTIVO"]


def test_un_negocio_con_la_promesa_cerrada_y_la_escritura_abierta_sigue_pendiente(db):
    """El estado vive en el hito (`D-027`), asi que basta uno abierto."""
    _negocio(db, "VVP-3", hitos=[
        NegocioHito(nombre="PROMESA", fecha_inicio=date(2026, 1, 10),
                    fecha_cierre=date(2026, 2, 1), estado=EstadoNegocio.CERRADO),
        NegocioHito(nombre="ESCRITURA", fecha_inicio=date(2026, 2, 5),
                    estado=EstadoNegocio.ACTIVO),
    ])

    filas = obtener_bandeja_negocios(db, hoy=HOY).filas

    assert len(filas) == 1
    # La antiguedad se mide desde el hito abierto mas antiguo, no desde el cerrado.
    assert filas[0].duraciones.dias_abierto == (HOY - date(2026, 2, 5)).days


def test_un_negocio_aparece_una_sola_vez_con_dos_hitos_abiertos(db):
    _negocio(db, "VVP-100", hitos=[
        NegocioHito(fecha_inicio=date(2026, 1, 10), estado=EstadoNegocio.ACTIVO),
        NegocioHito(fecha_inicio=date(2026, 2, 10), estado=EstadoNegocio.ACTIVO),
    ])

    assert len(obtener_bandeja_negocios(db, hoy=HOY).filas) == 1


def test_una_cartera_vacia_no_rompe(db):
    b = obtener_bandeja_negocios(db, hoy=HOY)

    assert b.filas == []
    assert b.resumen.sin_gestion == 0


# ------------------------------------------------------------ endpoints


def test_el_endpoint_de_la_bandeja_responde(cliente, db):
    _negocio(db, "VVP-100")

    r = cliente.get("/api/negocios/bandeja")

    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["umbral_critico_dias"] == UMBRAL_CRITICO
    assert cuerpo["filas"][0]["codigo"] == "VVP-100"
    assert cuerpo["filas"][0]["nivel"] == "sin_gestion"


def test_el_listado_trae_las_duraciones(cliente, db, tipos):
    """La tabla de Negocios no tenia ninguna columna de fecha."""
    n = _negocio(db, "VVP-100")
    _mov(db, n.id, "NEG_LLAMADA", 5)

    fila = cliente.get("/api/negocios").json()[0]

    # El endpoint usa el día de hoy de verdad, no `HOY`: se calcula la
    # diferencia en vez de fijar un número, que se rompería al cruzar la
    # medianoche UTC.
    esperado = (datetime.now(timezone.utc).date() - (HOY - timedelta(days=5))).days

    assert fila["fecha_inicio"] == "2026-01-10"
    assert fila["duraciones"]["dias_sin_gestion"] == esperado
    assert fila["duraciones"]["dias_abierto"] is not None


def test_el_listado_no_inventa_duracion_de_cierre(cliente, db):
    """El caso de los historicos, visto desde la API."""
    _negocio(db, "VVP-100", hitos=[
        NegocioHito(fecha_inicio=date(2026, 3, 9), fecha_cierre=date(2026, 3, 9),
                    estado=EstadoNegocio.CERRADO)])

    fila = cliente.get("/api/negocios").json()[0]

    assert fila["duraciones"]["dias_hasta_el_cierre"] is None


def test_un_negocio_resuelto_sin_fecha_de_cierre_no_envejece_para_siempre():
    """El tercer caso, el que obliga a pasar `abierto`.

    Un negocio perdido en enero no "lleva 8 meses abierto": no se sabe cuanto
    duro, porque nadie registro cuando se cayo. Contar hasta hoy daria un numero
    que crece solo y que alguien leeria como un negocio activo desatendido.
    """
    d = duraciones_de(date(2026, 1, 10), None, None, None, HOY, abierto=False)

    assert d.dias_abierto is None
    assert d.dias_hasta_el_cierre is None


# ------------------------------------------- el compromiso manda sobre el tiempo


def test_el_compromiso_manda_sobre_el_semaforo():
    """La misma regla que canjes (`D-059`), y por el mismo motivo.

    El semaforo *infiere* que algo esta abandonado por el tiempo que paso; el
    compromiso dice que se prometio. Cuando los dos opinan, gana el que no
    infiere: un negocio agendado para el jueves esta al dia el martes aunque lleve
    dos meses sin tocarse, y uno con el compromiso vencido esta atrasado aunque se
    haya tocado ayer.
    """
    assert clasificar(60, dias_de_atraso=-2) == "agendado"
    assert clasificar(60, dias_de_atraso=0) == "para_hoy"
    # Tres y cinco días de atraso siguen siendo "vencido": en un proceso que dura
    # meses eso es recién vencido, y el escalamiento empieza a los 15 (`D-094`).
    assert clasificar(60, dias_de_atraso=3) == "vencido"
    assert clasificar(1, dias_de_atraso=5) == "vencido"
    # Pero deja de quedarse ahí para siempre.
    assert clasificar(1, dias_de_atraso=15) == "advertencia"
    assert clasificar(1, dias_de_atraso=31) == "critico"
    # Sin compromiso sigue mandando el semaforo de 30/14 dias.
    assert clasificar(31, dias_de_atraso=None) == "critico"
    assert clasificar(None, dias_de_atraso=None) == "sin_gestion"


def test_el_agendado_a_futuro_no_se_lista_pero_se_cuenta(db, tipos):
    """La pantalla se llama "que me toca hoy", y este negocio no toca hoy.

    Se cuenta aparte para que no parezca que desaparecio: sin ese numero, el
    resumen se lee como si fueran los unicos negocios abiertos.
    """
    n = _negocio(db, "AG-1")
    _mov(db, n.id, "NEG_LLAMADA", 10)
    # El movimiento agenda para dentro de cuatro dias.
    mov = db.query(Movimiento).filter_by(entity_id=n.id).one()
    mov.proximo_seguimiento = HOY + timedelta(days=4)
    db.commit()

    b = obtener_bandeja_negocios(db, hoy=HOY)

    assert b.filas == []
    assert b.resumen.agendados == 1


def test_un_movimiento_sin_compromiso_no_borra_el_anterior(db, tipos):
    """Corregir algo no puede borrar lo que se prometio (`D-061`).

    Si se mirara el compromiso del **ultimo** movimiento, un movimiento sin
    seguimiento --un cambio de etapa hecho a mano, por ejemplo-- dejaria el
    negocio sin compromiso y lo devolveria a la lista sin que nadie lo decidiera.
    """
    n = _negocio(db, "CM-1")
    _mov(db, n.id, "NEG_LLAMADA", 10)
    db.query(Movimiento).filter_by(entity_id=n.id).one().proximo_seguimiento = HOY + timedelta(days=5)
    db.commit()
    # Un segundo movimiento, mas nuevo y sin compromiso.
    _mov(db, n.id, "NEG_A_E4", 1, etapa="E4")

    b = obtener_bandeja_negocios(db, hoy=HOY)

    # Sigue agendado: el compromiso vigente es el ultimo que **existe**.
    assert b.filas == []
    assert b.resumen.agendados == 1


def test_el_compromiso_recien_vencido_no_le_gana_al_abandonado(db, tipos):
    """El compromiso vencido sigue contando, pero ya no va al tope por serlo.

    Antes este test se llamaba "el compromiso vencido sube al tope" y esperaba
    `F-1` primero: el compromiso le ganaba al semáforo siempre. Con el
    escalamiento (`D-094`) el orden es por severidad, y dos días de atraso en un
    proceso que dura meses es "recién vencido", mientras 40 días sin que nadie
    toque `V-1` es abandono. Ese es el que hay que mirar primero.

    Lo que **no** cambió: `F-1` se tocó ayer y aun así aparece, porque lo
    prometido no se cumplió.
    """
    viejo = _negocio(db, "V-1")
    fresco = _negocio(db, "F-1")
    _mov(db, viejo.id, "NEG_LLAMADA", 40)          # critico por tiempo
    _mov(db, fresco.id, "NEG_LLAMADA", 1)          # al dia por tiempo
    db.query(Movimiento).filter_by(entity_id=fresco.id).one().proximo_seguimiento = (
        HOY - timedelta(days=2)
    )
    db.commit()

    b = obtener_bandeja_negocios(db, hoy=HOY)

    assert [f.codigo for f in b.filas] == ["V-1", "F-1"]
    assert b.filas[0].nivel == "critico"
    assert b.filas[1].nivel == "vencido"
    assert b.filas[1].dias_de_atraso == 2
    assert b.resumen.vencido == 1


def test_el_atraso_de_un_negocio_escala_con_sus_propios_umbrales(db, tipos):
    """15 días de atraso son advertencia; 31, crítico. Con un día de gracia.

    Los umbrales son los del dominio --14 y 30 días, no las 48 horas de canjes--
    porque acá los procesos duran de un mes a varios. Un negocio con el
    compromiso vencido hace tres días no está abandonado; hace cinco semanas, sí.
    """
    casos = {"A-1": 1, "A-2": 15, "A-3": 31, "A-4": 200}
    for codigo, atraso in casos.items():
        n = _negocio(db, codigo)
        _mov(db, n.id, "NEG_LLAMADA", 1)
        db.query(Movimiento).filter_by(entity_id=n.id).one().proximo_seguimiento = (
            HOY - timedelta(days=atraso)
        )
        db.commit()

    b = obtener_bandeja_negocios(db, hoy=HOY)
    nivel = {f.codigo: f.nivel for f in b.filas}

    assert nivel["A-1"] == "vencido"
    assert nivel["A-2"] == "advertencia"
    assert nivel["A-3"] == "critico"
    assert nivel["A-4"] == "critico"
