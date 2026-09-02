"""Tests del reporte semanal: el mes semana a semana, contra los anteriores.

**El contrato cambió entero** (`D-098`). Antes esta pantalla medía una ventana
móvil de semanas corridas y devolvía cuatro cifras con listas por entidad. Ahora
el eje es la semana del mes y los meses anteriores van superpuestos, que es lo que
el usuario pidió para poder comparar.

Las propiedades que se protegen acá:

1. **Las semanas se cuentan desde el día 1 y la última es parcial.** Un mes de 31
   días da cinco tramos, febrero cuatro. Sin eso el «mes» del reporte no coincide
   con el mes.
2. **«Avanzaron» cuenta entidades, no movimientos.** Dos avances del mismo canje
   en la semana son un canje que avanzó.
3. **«Se cayeron» suma las dos fuentes sin duplicar** (`D-086`) y **descuenta las
   fechas que estampó una carga masiva** (`D-085`). Las dos reglas se heredan de
   la versión anterior y siguen valiendo.
4. **El embudo trae todas las etapas, incluso en cero.** Se lee por su forma: una
   etapa que desaparece parece no existir.
5. **Lo que no se puede medir se declara.** En negocios «avanzaron» y «se cayeron»
   no tienen de dónde salir, y decirlo es distinto de dibujar ceros.
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import EstadoNegocio, Etapa, ModeloNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services.metricas_periodo import semanas_del_mes
from app.services.reporte_semanal import MESES_DEFECTO, obtener_reporte_semanal

# Un miércoles de septiembre: el mes que se mira por defecto en los tests es
# agosto, ya cerrado, para que las semanas no dependan de la hora.
AHORA = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)
HOY = AHORA.date()


@pytest.fixture(autouse=True)
def etapas(db):
    """`negocios.etapa` apunta a `etapas.codigo` y la clave foránea está activa."""
    db.add_all([
        Etapa(codigo="E2", nombre="Visita", responsable="COMERCIAL", orden=2),
        Etapa(codigo="E4", nombre="Documentación", responsable="OPERACIONES", orden=4),
    ])
    db.commit()


@pytest.fixture
def tipos(db):
    db.add_all([
        TipoMovimiento(codigo="WA_SOLICITANTE", entity_type=EntityType.canje,
                       nombre="WA confirmación", etapa_resultante=None,
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
        TipoMovimiento(codigo="NEG_E4", entity_type=EntityType.negocio,
                       nombre="Pasa a E4", etapa_resultante="E4",
                       orden=2, sla_es_habil=False, activo=True),
    ])
    db.commit()
    return db


def _dia(dia: int, mes: int = 8, anio: int = 2026) -> datetime:
    return datetime(anio, mes, dia, 10, 0, tzinfo=timezone.utc)


def _canje(db, id_, dia=1, mes=8, etapa=CanjeEtapa.EN_REVISION,
           estado=CanjeEstado.ACTIVO, cierre=None):
    db.add(Canje(
        id=id_,
        fecha_solicitud=_dia(dia, mes),
        fecha_cierre=cierre,
        estado=estado,
        etapa=etapa,
        comuna="Providencia",
    ))


def _mov(db, entity_type, entity_id, tipo, cuando, etapa=None, creado_en=None):
    """Un movimiento. `creado_en` se pasa para simular una carga masiva: dos
    movimientos con el mismo timestamp al microsegundo entraron en la misma
    transacción, que es como el reporte reconoce una carga (`D-085`)."""
    db.add(Movimiento(
        entity_type=entity_type,
        entity_id=entity_id,
        tipo_movimiento=tipo,
        fecha=cuando,
        etapa_resultante=etapa,
        comentario="x",
        **({"creado_en": creado_en} if creado_en is not None else {}),
    ))


def _negocio(db, codigo, inicio, estado=EstadoNegocio.ACTIVO, cierre=None,
             real=D("0"), etapa="E2"):
    prop = Propiedad(direccion=f"Calle {codigo}", comuna="Nunoa")
    db.add(prop)
    n = Negocio(codigo=codigo, modelo=ModeloNegocio.MERCADO_PRIMARIO,
                propiedad=prop, etapa=etapa)
    n.hitos = [NegocioHito(
        fecha_inicio=inicio, fecha_cierre=cierre, estado=estado, comision_real_vp=real,
    )]
    db.add(n)
    db.flush()
    return n


def _reporte(db, meses=MESES_DEFECTO, anio=2026, mes=8):
    return obtener_reporte_semanal(db, anio, mes, meses, hoy=HOY)


# ------------------------------------------------------------------ semanas


def test_las_semanas_se_cuentan_desde_el_dia_uno():
    """Del 1 al 7, del 8 al 14, y la última cortada donde termina el mes.

    No son semanas calendario: lunes a domingo haría que la primera y la última se
    metieran en el mes vecino, y la base del reporte es el mes.
    """
    semanas = semanas_del_mes(2026, 8)

    assert [s.etiqueta for s in semanas] == [
        "S1 1-7", "S2 8-14", "S3 15-21", "S4 22-28", "S5 29-31"
    ]
    assert semanas[0].desde == date(2026, 8, 1)
    assert semanas[-1].hasta == date(2026, 8, 31)


def test_la_ultima_semana_es_parcial_y_lo_dice():
    """Tres días en un mes de 31, así que siempre se va a ver más baja. `dias` es
    lo que permite a la pantalla decir que la caída es del calendario."""
    assert [s.dias for s in semanas_del_mes(2026, 8)] == [7, 7, 7, 7, 3]


def test_febrero_tiene_cuatro_semanas():
    """«Variable de acuerdo a la cantidad de semanas reales de cada mes.»"""
    assert len(semanas_del_mes(2026, 2)) == 4
    assert [s.dias for s in semanas_del_mes(2026, 2)] == [7, 7, 7, 7]


# ------------------------------------------------------------------- el flujo


def test_el_flujo_reparte_las_entradas_en_su_semana(db, tipos):
    _canje(db, 1, dia=3)    # S1
    _canje(db, 2, dia=5)    # S1
    _canje(db, 3, dia=10)   # S2
    _canje(db, 4, dia=30)   # S5
    db.commit()

    r = _reporte(db, meses=1)

    del_mes = r.canjes.flujo[0]
    assert del_mes.mes == "2026-08"
    assert del_mes.entraron == [2, 1, 0, 0, 1]


def test_avanzaron_cuenta_canjes_y_no_movimientos(db, tipos):
    """Dos avances del mismo canje en la semana son **un** canje que avanzó."""
    _canje(db, 1, dia=1)
    db.commit()
    _mov(db, EntityType.canje, 1, "PASA_A_OFERTA", _dia(3), etapa="EN_OFERTA")
    _mov(db, EntityType.canje, 1, "PASA_A_OFERTA", _dia(5), etapa="EN_NEGOCIO")
    db.commit()

    r = _reporte(db, meses=1)

    assert r.canjes.flujo[0].avanzaron == [1, 0, 0, 0, 0]


def test_se_cayeron_suma_las_dos_fuentes_sin_duplicar(db, tipos):
    """**Las dos fuentes son parciales** (`D-086`).

    Dataprop manda la fecha de cancelación de los canjes recientes y cancelar en
    la app no escribe ese campo, así que hay que sumar las dos. Y un canje que
    tenga las dos no puede contarse dos veces.
    """
    # Uno solo con movimiento.
    _canje(db, 1, dia=1, estado=CanjeEstado.CANCELADO)
    # Uno solo con fecha de cierre.
    _canje(db, 2, dia=1, estado=CanjeEstado.CANCELADO, cierre=_dia(4))
    # Uno con las dos: cuenta una vez.
    _canje(db, 3, dia=1, estado=CanjeEstado.CANCELADO, cierre=_dia(5))
    db.commit()
    _mov(db, EntityType.canje, 1, "CANCELACION", _dia(2))
    _mov(db, EntityType.canje, 3, "CANCELACION", _dia(5))
    db.commit()

    r = _reporte(db, meses=1)

    assert r.canjes.flujo[0].se_cayeron == [3, 0, 0, 0, 0]


def test_la_fecha_que_estampo_una_carga_masiva_no_es_una_caida(db, tipos):
    """**Las dos condiciones** (`D-085`).

    La limpieza que canceló 215 canjes les puso la fecha del día en que corrió, y
    contarlas daba 215 caídas en una semana. Lo que distingue a esa fila no es
    cómo entró sino que su fecha es un subproducto: el script estampó «hoy». Se
    reconoce porque su `creado_en` lo comparte otra fila **y** coincide con su
    propia fecha.
    """
    momento = _dia(10)
    _canje(db, 1, dia=1, estado=CanjeEstado.CANCELADO)
    _canje(db, 2, dia=1, estado=CanjeEstado.CANCELADO)
    db.commit()
    # Dos movimientos con el mismo `creado_en` y la fecha de ese mismo día.
    _mov(db, EntityType.canje, 1, "CANCELACION", momento, creado_en=momento)
    _mov(db, EntityType.canje, 2, "CANCELACION", momento, creado_en=momento)
    db.commit()

    r = _reporte(db, meses=1)

    assert r.canjes.flujo[0].se_cayeron == [0, 0, 0, 0, 0]


def test_una_cancelacion_registrada_a_mano_si_cuenta(db, tipos):
    """Aunque su fecha sea la de hoy: lo que la distingue de la carga es que su
    `creado_en` no lo comparte nadie."""
    _canje(db, 1, dia=1, estado=CanjeEstado.CANCELADO)
    db.commit()
    _mov(db, EntityType.canje, 1, "CANCELACION", _dia(10), creado_en=_dia(10))
    db.commit()

    r = _reporte(db, meses=1)

    assert r.canjes.flujo[0].se_cayeron == [0, 1, 0, 0, 0]


# ------------------------------------------------------ los meses comparados


def test_el_mes_elegido_va_primero_y_despues_los_anteriores(db, tipos):
    """La pantalla dibuja el primero destacado y el resto como referencia."""
    _canje(db, 1, dia=3, mes=8)
    _canje(db, 2, dia=3, mes=7)
    _canje(db, 3, dia=3, mes=6)
    db.commit()

    r = _reporte(db, meses=3)

    assert [f.mes for f in r.canjes.flujo] == ["2026-08", "2026-07", "2026-06"]
    assert all(f.entraron[0] == 1 for f in r.canjes.flujo)


def test_los_totales_van_del_mas_viejo_al_mas_nuevo(db, tipos):
    """Es el eje del bloque de tendencia, y una serie de tiempo se lee hacia
    adelante."""
    r = _reporte(db, meses=3)

    assert [t.etiqueta for t in r.canjes.totales] == ["2026-06", "2026-07", "2026-08"]


def test_con_un_mes_no_hay_con_que_comparar(db, tipos):
    r = _reporte(db, meses=1)

    assert len(r.canjes.flujo) == 1
    assert len(r.canjes.totales) == 1


def test_los_meses_a_comparar_tienen_tope(db, tipos):
    with pytest.raises(ValueError, match="meses"):
        obtener_reporte_semanal(db, 2026, 8, 13, hoy=HOY)


# ------------------------------------------------------------------ el embudo


def test_el_embudo_trae_todas_las_etapas_aunque_esten_en_cero(db, tipos):
    """**Se lee por su forma**: dónde se angosta. Una etapa que desaparece porque
    nadie pasó por ella parece no existir."""
    _canje(db, 1, dia=3)
    db.commit()
    _mov(db, EntityType.canje, 1, "PASA_A_OFERTA", _dia(4), etapa="EN_OFERTA")
    db.commit()

    r = _reporte(db, meses=1)

    etapas = {e.etapa: e.entraron for e in r.canjes.embudo}
    assert etapas["EN_OFERTA"] == 1
    assert etapas["EN_REVISION"] == 0
    assert len(r.canjes.embudo) == len(CanjeEtapa)


def test_el_embudo_promedia_los_meses_anteriores(db, tipos):
    """El promedio va como número al lado y no como una segunda barra: es la
    referencia, y duplicar las barras es lo que recarga la pantalla."""
    _canje(db, 1, dia=3, mes=8)
    _canje(db, 2, dia=3, mes=7)
    _canje(db, 3, dia=4, mes=7)
    _canje(db, 4, dia=3, mes=6)
    db.commit()
    for id_, mes in ((1, 8), (2, 7), (3, 7), (4, 6)):
        _mov(db, EntityType.canje, id_, "PASA_A_OFERTA", _dia(5, mes), etapa="EN_OFERTA")
    db.commit()

    r = _reporte(db, meses=3)

    oferta = next(e for e in r.canjes.embudo if e.etapa == "EN_OFERTA")
    assert oferta.entraron == 1                      # agosto
    assert float(oferta.promedio_anteriores) == 1.5  # (2 de julio + 1 de junio) / 2


# --------------------------------------------------------------- los abiertos


def test_los_abiertos_traen_casos_plata_y_dias(db, tipos):
    """Y el `n` a la vista: con pocos canjes, el promedio de una etapa puede ser un
    solo caso y sin el `n` se lee como una tendencia."""
    _canje(db, 1, dia=1, etapa=CanjeEtapa.EN_OFERTA)
    _canje(db, 2, dia=1, etapa=CanjeEtapa.EN_OFERTA)
    db.commit()

    r = _reporte(db, meses=1)

    oferta = next(e for e in r.canjes.abiertos if e.etapa == "EN_OFERTA")
    assert oferta.casos == 2
    # Sin movimiento que registre la entrada, el reloj se cuenta desde la
    # solicitud y se dice cuántos son.
    assert oferta.sin_historia == 2


def test_un_canje_cerrado_no_esta_abierto(db, tipos):
    """Abierto es activo y con etapa distinta de cerrada, igual que en la bandeja:
    los que arrastran el desalineamiento del dato de Dataprop no son pendientes."""
    _canje(db, 1, dia=1, etapa=CanjeEtapa.CERRADO)
    _canje(db, 2, dia=1, estado=CanjeEstado.CANCELADO)
    db.commit()

    assert _reporte(db, meses=1).canjes.abiertos == []


# ------------------------------------------------------------------ negocios


def test_negocios_declara_lo_que_no_puede_medir(db, tipos):
    """**Decirlo es distinto de dibujar ceros.** Sin movimientos de pipeline no se
    sabe qué avanzó, y sin fecha en las perdidas no se sabe cuándo se cayeron. Una
    serie de ceros diría «no pasó nada»."""
    _negocio(db, "N-1", date(2026, 8, 3))
    _negocio(db, "N-2", date(2026, 8, 10), estado=EstadoNegocio.PERDIDO)
    db.commit()

    r = _reporte(db, meses=1)

    assert r.negocios.sin_datos == ["avanzaron", "se_cayeron"]
    assert r.negocios.flujo[0].entraron == [1, 1, 0, 0, 0]


def test_cuando_hay_movimientos_de_pipeline_deja_de_avisar(db, tipos):
    """El aviso se calcula y no se escribe fijo: se resuelve solo en cuanto
    alguien registre un avance."""
    n = _negocio(db, "N-1", date(2026, 8, 3))
    db.commit()
    _mov(db, EntityType.negocio, n.id, "NEG_E4", _dia(4), etapa="E4")
    db.commit()

    r = _reporte(db, meses=1)

    assert "avanzaron" not in r.negocios.sin_datos
    assert r.negocios.flujo[0].avanzaron == [1, 0, 0, 0, 0]


def test_la_plata_de_negocios_va_por_fecha_de_cierre(db, tipos):
    """La comisión se gana al cerrar, no al entrar."""
    _negocio(db, "N-1", date(2026, 6, 1), estado=EstadoNegocio.CERRADO,
             cierre=date(2026, 8, 20), real=D("500000"))
    db.commit()

    r = _reporte(db, meses=3)

    por_mes = {t.etiqueta: float(t.comision) for t in r.negocios.totales}
    assert por_mes["2026-08"] == 500000
    assert por_mes["2026-06"] == 0, "el mes en que empezó no cobra nada"


def test_los_abiertos_de_negocios_traen_su_comision_en_juego(db, tipos):
    _negocio(db, "N-1", date(2026, 5, 1), real=D("774691"), etapa="E4")
    db.commit()

    r = _reporte(db, meses=1)

    e4 = next(e for e in r.negocios.abiertos if e.etapa == "E4")
    assert e4.casos == 1
    assert float(e4.comision) == 774691


# ------------------------------------------------------------------ tendencia


def test_la_tendencia_va_sobre_los_meses(db, tipos):
    """No sobre las semanas: cinco puntos con el último de tres días no sostienen
    una curva, y el ajuste bajaría siempre al final por el calendario."""
    r = _reporte(db, meses=3)

    assert set(r.canjes.tendencias) >= {"entraron", "se_cayeron", "comision"}
    assert r.canjes.tendencias["entraron"].puntos == 3


# ------------------------------------------------------------------ endpoint


def test_el_endpoint_devuelve_los_dos_dominios(cliente, db, tipos):
    _canje(db, 1, dia=3)
    db.commit()

    r = cliente.get("/api/reportes/semanal", params={"anio": 2026, "mes": 8, "meses": 3})

    assert r.status_code == 200
    cuerpo = r.json()
    assert set(cuerpo) == {"anio", "mes", "meses", "canjes", "negocios"}
    assert set(cuerpo["canjes"]) == {
        "semanas", "flujo", "embudo", "abiertos", "totales", "tendencias", "sin_datos",
    }


def test_el_endpoint_rechaza_un_tope_de_meses_invalido(cliente):
    assert cliente.get("/api/reportes/semanal", params={"meses": 13}).status_code == 422


def test_el_endpoint_exige_anio_y_mes_juntos(cliente):
    assert cliente.get("/api/reportes/semanal", params={"anio": 2026}).status_code == 400
