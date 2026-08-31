"""Cuándo hay que volver a mirar un canje, y cómo eso ordena «Qué me toca hoy».

**Qué cambia.** La bandeja ordenaba por horas sin gestión, que es un proxy: mide
cuánto hace que nadie toca un canje, no qué se prometió hacer. Ahora un movimiento
puede agendar su próximo seguimiento, y ese compromiso manda sobre el semáforo.

**Los feriados no se saltan, y es una decisión declarada.** El default corre el fin
de semana y nada más. Saltar feriados necesita la lista de los de Chile --con los
movibles de la ley de traslado, Pascua y los días de elección-- y calcularla mal
dejaría el error escondido hasta que alguien agende un seguimiento para el 18 de
septiembre. Hay un test que fija que hoy **no** se saltan, para que el día que se
agreguen sea un cambio deliberado y no una sorpresa.
"""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.services.bandeja_canjes import obtener_bandeja
from app.services.movimientos import (
    DIAS_SEGUIMIENTO,
    crear_movimiento_canje,
    proximo_habil,
    seguimiento_por_defecto,
)

AHORA = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)  # un martes
HOY = AHORA.date()


@pytest.fixture
def base(db):
    db.add(TipoMovimiento(
        codigo="GESTION", entity_type=EntityType.canje, nombre="Gestión",
        etapa_resultante=None, orden=1, sla_es_habil=False, activo=True,
    ))
    db.commit()
    return db


def _canje(db, id_canje: int, dias_atras: int = 30) -> Canje:
    c = Canje(
        id=id_canje,
        fecha_solicitud=AHORA - timedelta(days=dias_atras),
        estado=CanjeEstado.ACTIVO,
        etapa=CanjeEtapa.EN_REVISION,
        comuna="Santiago",
    )
    db.add(c)
    return c


# ------------------------------------------------- el cálculo del día hábil


def test_son_dos_dias_corridos_cuando_cae_en_semana():
    """Dos corridos, no dos hábiles.

    Un martes más dos da jueves. Contar hábiles daría lo mismo acá, pero no el
    viernes, y "te llamo en un par de días" son días de calendario.
    """
    assert DIAS_SEGUIMIENTO == 2
    assert proximo_habil(date(2026, 8, 25)) == date(2026, 8, 27)  # mar -> jue


@pytest.mark.parametrize("desde,esperado,por_que", [
    (date(2026, 8, 27), date(2026, 8, 31), "jue + 2 = sábado, se corre a lunes"),
    (date(2026, 8, 28), date(2026, 8, 31), "vie + 2 = domingo, se corre a lunes"),
    (date(2026, 8, 29), date(2026, 8, 31), "sáb + 2 = lunes, ya es hábil"),
    (date(2026, 8, 30), date(2026, 9, 1), "dom + 2 = martes, ya es hábil"),
])
def test_el_fin_de_semana_se_corre_al_lunes(desde, esperado, por_que):
    assert proximo_habil(desde) == esperado, por_que


def test_los_feriados_todavia_no_se_saltan():
    """Fija la decisión: hoy solo se corre el fin de semana.

    El 18 de septiembre de 2026 es viernes, y el 16 es miércoles: un seguimiento
    agendado el 16 cae el 18, que es feriado, y el sistema no lo mueve. Está
    documentado en `D-059`. Este test existe para que agregar feriados sea un
    cambio deliberado --lo va a hacer fallar-- y no algo que pase de casualidad.
    """
    assert proximo_habil(date(2026, 9, 16)) == date(2026, 9, 18)


def test_el_default_se_ancla_al_mas_nuevo_de_los_dos():
    """Anotar hoy una gestión de hace tres meses no agenda un vencido de entonces.

    Anclarlo solo a la fecha del movimiento llenaría la bandeja de vencidos que
    nadie prometió; anclarlo solo a hoy perdería el caso normal. El mayor de los
    dos resuelve los dos.
    """
    # Gestión vieja, anotada hoy: el seguimiento sale de hoy.
    assert seguimiento_por_defecto(date(2026, 5, 10), HOY) == date(2026, 8, 27)
    # Gestión de hoy: lo mismo.
    assert seguimiento_por_defecto(HOY, HOY) == date(2026, 8, 27)


# --------------------------------------------- lo que guarda el movimiento


def test_sin_indicar_nada_se_agenda_solo(base):
    _canje(base, 1)
    base.commit()

    m = crear_movimiento_canje(base, 1, "GESTION", autor_id=None)

    assert m.proximo_seguimiento is not None, "nunca queda en nulo"
    assert m.proximo_seguimiento.weekday() < 5, "y nunca cae fin de semana"


def test_una_fecha_indicada_se_respeta_tal_cual(base):
    """Es el punto de que el campo exista: el default es una comodidad."""
    _canje(base, 2)
    base.commit()

    m = crear_movimiento_canje(
        base, 2, "GESTION", autor_id=None, proximo_seguimiento=date(2026, 12, 24)
    )

    assert m.proximo_seguimiento == date(2026, 12, 24)


def test_se_puede_agendar_un_fin_de_semana_a_mano(base):
    """El default los evita; indicarlo explícito no se corrige.

    Si alguien escribe sábado es porque va a trabajar el sábado. Corregirle la
    fecha que acaba de escribir sería el sistema opinando sobre su agenda.
    """
    _canje(base, 3)
    base.commit()

    m = crear_movimiento_canje(
        base, 3, "GESTION", autor_id=None, proximo_seguimiento=date(2026, 8, 29)
    )

    assert m.proximo_seguimiento == date(2026, 8, 29)
    assert m.proximo_seguimiento.weekday() == 5


# --------------------------------------------------- cómo ordena la bandeja


def _con_seguimiento(db, id_canje: int, seguimiento: date | None, horas_atras: int = 1):
    """Un canje con un movimiento que agenda --o no-- su seguimiento."""
    _canje(db, id_canje)
    db.add(Movimiento(
        entity_type=EntityType.canje,
        entity_id=id_canje,
        tipo_movimiento="GESTION",
        fecha=AHORA - timedelta(hours=horas_atras),
        proximo_seguimiento=seguimiento,
    ))


def test_el_compromiso_vencido_escala_por_el_semaforo(base):
    """**Un compromiso incumplido deja de proteger** (`D-094`).

    Antes este test decía lo contrario: el nivel se quedaba en "vencido" para
    siempre, con el compromiso ganándole al semáforo. El usuario mostró el
    problema con sus propios datos --cinco canjes con 3 y 4 días de espera y el
    recuadro de crítico en cero-- y lo dijo preciso: *"cualquier fecha puesta de
    seguimiento oculta la realidad de gestión"*.

    Ahora el atraso pasa por los mismos umbrales: tres días vencido son 72 horas
    efectivas tras el día de gracia, o sea crítico. Y un crítico va antes que un
    compromiso que vence hoy, porque "para hoy" todavía no se incumplió.
    """
    _con_seguimiento(base, 10, HOY - timedelta(days=3))   # vencido → crítico
    _con_seguimiento(base, 11, HOY)                       # para hoy
    _con_seguimiento(base, 12, None, horas_atras=200)     # crítico por semáforo
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)

    assert [f.nivel for f in b.filas] == ["critico", "critico", "para_hoy"]
    # Entre dos críticos manda el atraso: el 10 tiene 3 días, el 12 ninguno.
    assert [f.canje_id for f in b.filas] == [10, 12, 11]


def test_el_atraso_escala_con_un_dia_de_gracia(base):
    """Recién vencido no es abandonado, y sin la gracia "vencido" no existiría.

    Estar vencido implica **al menos un día** de atraso, y un día son las 24 horas
    del umbral de advertencia. Sin el día de gracia el nivel "vencido" quedaría
    vacío por definición y su recuadro sería un cartel que siempre marca cero, que
    es justo el defecto que se arregló en `D-093`.
    """
    _con_seguimiento(base, 30, HOY - timedelta(days=1))   # recién vencido
    _con_seguimiento(base, 31, HOY - timedelta(days=2))   # 24 h de atraso
    _con_seguimiento(base, 32, HOY - timedelta(days=3))   # 48 h de atraso
    _con_seguimiento(base, 33, HOY - timedelta(days=30))
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)
    nivel = {f.canje_id: f.nivel for f in b.filas}

    assert nivel[30] == "vencido"
    assert nivel[31] == "advertencia"
    assert nivel[32] == "critico"
    assert nivel[33] == "critico"


def test_lo_agendado_a_futuro_no_escala_aunque_nadie_lo_toque(base):
    """El compromiso **vigente** sí protege, y tiene que seguir protegiendo.

    Un canje agendado para dentro de diez días no tiene gestión en el intertanto
    por definición. Someterlo al reloj pondría en rojo todo lo agendado a más de
    dos días y agendar dejaría de servir. Este canje lleva 200 horas sin gestión y
    aun así no se lista: se cuenta en `agendados`.
    """
    _con_seguimiento(base, 40, HOY + timedelta(days=10), horas_atras=200)
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)

    assert [f.canje_id for f in b.filas] == []
    assert b.resumen.agendados == 1
    assert b.resumen.critico == 0


def test_entre_dos_vencidos_va_primero_el_mas_atrasado(base):
    _con_seguimiento(base, 20, HOY - timedelta(days=1))
    _con_seguimiento(base, 21, HOY - timedelta(days=9))
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)

    assert [f.canje_id for f in b.filas] == [21, 20]
    assert [f.dias_de_atraso for f in b.filas] == [9, 1]


def test_lo_agendado_para_despues_no_se_lista_pero_se_cuenta(base):
    """La pantalla se llama «qué me toca hoy»: lo que no toca no va en la lista."""
    _con_seguimiento(base, 30, HOY + timedelta(days=4))
    _con_seguimiento(base, 31, HOY + timedelta(days=1))
    _con_seguimiento(base, 32, HOY)
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)

    assert [f.canje_id for f in b.filas] == [32]
    assert b.resumen.agendados == 2
    # Y no se cuelan en los otros niveles.
    assert b.resumen.al_dia == 0


def test_el_compromiso_manda_sobre_el_semaforo(base):
    """Un canje sin tocar hace días pero agendado para mañana no es urgente.

    El semáforo lo pondría en crítico --200 horas sin gestión-- y el compromiso
    dice que se sigue mañana. Cuando los dos opinan, gana el que no es una
    inferencia.
    """
    _con_seguimiento(base, 40, HOY + timedelta(days=1), horas_atras=200)
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)

    assert b.filas == []
    assert b.resumen.agendados == 1
    assert b.resumen.critico == 0


def test_los_canjes_sin_compromiso_siguen_con_el_semaforo(base):
    """El cambio es aditivo: lo que no tiene fecha se clasifica como antes."""
    _con_seguimiento(base, 50, None, horas_atras=200)  # crítico
    _con_seguimiento(base, 51, None, horas_atras=30)   # advertencia
    _canje(base, 52)                                   # sin gestión
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)

    por_id = {f.canje_id: f for f in b.filas}
    assert por_id[50].nivel == "critico"
    assert por_id[51].nivel == "advertencia"
    assert por_id[52].nivel == "sin_gestion"
    assert all(f.proximo_seguimiento is None for f in b.filas)
    assert all(f.dias_de_atraso is None for f in b.filas)


def test_el_compromiso_vigente_es_el_del_movimiento_mas_reciente(base):
    """Igual que la etapa: se deriva de la línea de tiempo, no se acumula.

    Así, borrar el último movimiento devuelve el compromiso anterior sin ningún
    paso extra.
    """
    _canje(base, 60)
    base.add_all([
        Movimiento(
            entity_type=EntityType.canje, entity_id=60, tipo_movimiento="GESTION",
            fecha=AHORA - timedelta(days=5),
            proximo_seguimiento=HOY - timedelta(days=3),
        ),
        Movimiento(
            entity_type=EntityType.canje, entity_id=60, tipo_movimiento="GESTION",
            fecha=AHORA - timedelta(hours=2),
            proximo_seguimiento=HOY + timedelta(days=2),
        ),
    ])
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)

    # El vigente es el del movimiento de hace dos horas: agendado, no vencido.
    assert b.filas == []
    assert b.resumen.agendados == 1


def test_el_resumen_cuadra_con_lo_que_se_lista(base):
    _con_seguimiento(base, 70, HOY - timedelta(days=1))
    _con_seguimiento(base, 71, HOY)
    _con_seguimiento(base, 72, HOY + timedelta(days=3))
    _con_seguimiento(base, 73, None, horas_atras=200)
    base.commit()

    b = obtener_bandeja(base, ahora=AHORA)
    r = b.resumen

    assert len(b.filas) == r.vencido + r.para_hoy + r.sin_gestion + r.critico + r.advertencia + r.al_dia
    assert r.agendados == 1, "los agendados quedan fuera de las filas"
    assert r.requieren_atencion == 3


# ------------------------------------------------------------------ endpoint


def test_el_endpoint_acepta_el_seguimiento(cliente, base):
    _canje(base, 80)
    base.commit()

    r = cliente.post("/api/canjes/80/movimientos", json={
        "tipo_movimiento": "GESTION",
        "proximo_seguimiento": "2026-09-15",
    })

    assert r.status_code == 201, r.text
    assert r.json()["proximo_seguimiento"] == "2026-09-15"


def test_el_endpoint_lo_agenda_solo_si_no_viene(cliente, base):
    _canje(base, 81)
    base.commit()

    r = cliente.post("/api/canjes/81/movimientos", json={"tipo_movimiento": "GESTION"})

    assert r.status_code == 201, r.text
    agendado = date.fromisoformat(r.json()["proximo_seguimiento"])
    assert agendado > date.today()
    assert agendado.weekday() < 5


def test_la_bandeja_devuelve_el_compromiso(cliente, base):
    _con_seguimiento(base, 82, date.today() - timedelta(days=2))
    base.commit()

    cuerpo = cliente.get("/api/canjes/bandeja").json()

    assert "agendados" in cuerpo["resumen"]
    fila = next(f for f in cuerpo["filas"] if f["canje_id"] == 82)
    # Dos días de atraso son 24 horas efectivas tras el día de gracia: advertencia
    # (`D-094`). Antes era "vencido" a secas, sin importar cuánto llevara.
    assert fila["nivel"] == "advertencia"
    assert fila["dias_de_atraso"] == 2
    assert fila["proximo_seguimiento"] is not None


# --------------------------------------------------- el default de negocios


def test_el_default_de_negocio_son_tres_dias_desde_la_fecha_registrada():
    """Tres dias, y contados desde la fecha del avance y no desde hoy.

    Es distinto de canjes en las dos cosas, y las dos por pedido explicito: alla
    son dos dias y se cuenta desde el mas nuevo entre la gestion y hoy.
    """
    from app.services.movimientos import seguimiento_de_negocio

    # Lunes 17 mas tres da jueves 20.
    assert seguimiento_de_negocio(date(2026, 8, 17)) == date(2026, 8, 20)


def test_el_default_de_negocio_corre_el_fin_de_semana():
    """Misma regla que canjes: tres dias de corrido y despues al lunes."""
    from app.services.movimientos import seguimiento_de_negocio

    # Jueves 20 mas tres da domingo 23 -> lunes 24.
    assert seguimiento_de_negocio(date(2026, 8, 20)) == date(2026, 8, 24)
    # Viernes 21 mas tres da lunes 24: no hay nada que correr.
    assert seguimiento_de_negocio(date(2026, 8, 21)) == date(2026, 8, 24)
    # Miercoles 19 mas tres da sabado 22 -> lunes 24.
    assert seguimiento_de_negocio(date(2026, 8, 19)) == date(2026, 8, 24)


def test_un_avance_atrasado_agenda_un_seguimiento_ya_vencido():
    """La consecuencia de contar desde la fecha registrada, dicha en un test.

    Cargar hoy un avance con fecha de hace un mes agenda un seguimiento vencido
    hace casi un mes, asi que el negocio aparece de inmediato como atrasado. Es la
    lectura correcta --se registro algo viejo, su seguimiento ya esta atrasado--
    pero es una decision y no un efecto secundario. En canjes se resolvio al
    revez, contando desde hoy.
    """
    from app.services.movimientos import seguimiento_de_negocio

    hace_un_mes = date(2026, 7, 20)
    assert seguimiento_de_negocio(hace_un_mes) == date(2026, 7, 23)
