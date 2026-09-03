"""El motor de comisiones de canjes.

**Los casos estan anclados a los 7 canjes activos reales**, con los montos que el
usuario verifico uno por uno contra su propia planilla. No son numeros inventados
para que el test pase: son la referencia contra la que se valido el motor.

La plata de un canje es de **Dataprop**, no de ViveProp: ViveProp opera el Centro
de Canje a nombre de Dataprop y no percibe nada. Por eso nada de lo que sale de aca
se suma con la plata de negocios.
"""
from decimal import Decimal as D

import pytest

from app.services.comisiones_canjes import (
    CORREDORES,
    PCT_CORREDOR_ARRIENDO,
    PCT_CORREDOR_VENTA,
    calcular,
)

# La UF del 27-08-2026, la que se uso para verificar contra la planilla.
UF = D("40868.50")

# Los 7 activos reales: (id, valor guardado, moneda, UF esperada, tramo, pct,
# comision de corredores, comision de Dataprop). Todos venta.
ACTIVOS = [
    (371, D("15900"), "UF", D("15900"), "sobre UF 8.000", D("0.04"), D("25992366"), D("1039695")),
    (370, D("10910"), "UF", D("10910"), "sobre UF 8.000", D("0.04"), D("17835013"), D("713401")),
    (364, D("63000000"), "CLP", D("1541"), "hasta UF 4.000", D("0.06"), D("2520000"), D("151200")),
    (360, D("6590"), "UF", D("6590"), "UF 4.001 a 8.000", D("0.05"), D("10772937"), D("538647")),
    (359, D("3999"), "UF", D("3999"), "hasta UF 4.000", D("0.06"), D("6537325"), D("392240")),
    (344, D("139000000"), "CLP", D("3401"), "hasta UF 4.000", D("0.06"), D("5560000"), D("333600")),
    (334, D("3200"), "UF", D("3200"), "hasta UF 4.000", D("0.06"), D("5231168"), D("313870")),
]


@pytest.mark.parametrize(
    "caso", ACTIVOS, ids=[str(c[0]) for c in ACTIVOS]
)
def test_los_siete_activos_reales(caso):
    """Cada uno con su tramo, su porcentaje y sus dos comisiones.

    Es el test que ancla el motor: si alguien cambia una tasa o un tramo, estos
    siete numeros dejan de dar y hay que decidirlo a proposito.
    """
    _id, valor, moneda, uf_esperada, tramo, pct, corredores, dataprop = caso

    r = calcular("VENTA", valor, moneda, UF)

    assert r is not None
    assert abs(r.valor_uf - uf_esperada) < D("1"), "el valor en UF define el tramo"
    assert r.tramo == tramo
    assert r.pct_dataprop == pct
    assert abs(r.comision_corredores - corredores) < D("1")
    assert abs(r.comision_dataprop - dataprop) < D("1")


def test_el_total_de_los_siete():
    """1.861 millones en propiedades, 74,4 de comision de corredores, 3,48 de Dataprop."""
    total_valor = sum(calcular("VENTA", v, m, UF).valor_clp for _, v, m, *_ in ACTIVOS)
    total_dp = sum(calcular("VENTA", v, m, UF).comision_dataprop for _, v, m, *_ in ACTIVOS)

    assert abs(total_valor - D("1861220232")) < D("10")
    assert abs(total_dp - D("3482652")) < D("10")


# ------------------------------------------------------------------- la regla


def test_los_dos_corredores_cobran_cada_uno():
    """2% cada uno, asi que la comision total es 4% del precio.

    Se confirmo expresamente: no es 2% de la operacion repartido entre los dos.
    """
    r = calcular("VENTA", D("100000000"), "CLP", UF)

    assert r.comision_por_corredor == D("2000000.00")
    assert r.comision_corredores == D("4000000.00")
    assert PCT_CORREDOR_VENTA * CORREDORES == D("0.04")


def test_en_arriendo_cada_corredor_cobra_medio_mes():
    """50% cada uno, o sea un mes completo entre los dos.

    Y Dataprop toma el 8% de esa comision total, no de la de cada uno: en arriendo
    el contrato dice "de la comision total" y en venta "de cada corredor".
    """
    r = calcular("ARRIENDO", D("1000000"), "CLP", UF)

    assert r.comision_por_corredor == D("500000.00")
    assert r.comision_corredores == D("1000000.00"), "un mes"
    assert r.comision_dataprop == D("80000.00"), "8% de un mes"
    assert PCT_CORREDOR_ARRIENDO * CORREDORES == D("1.00")


def test_los_tres_tramos_de_venta():
    """Los cortes exactos, incluidos los bordes."""
    def tramo_de(uf):
        return calcular("VENTA", D(str(uf)), "UF", UF).tramo

    assert tramo_de(1) == "hasta UF 4.000"
    assert tramo_de(4000) == "hasta UF 4.000", "el tope entra en el tramo"
    assert tramo_de("4000.01") == "UF 4.001 a 8.000"
    assert tramo_de(8000) == "UF 4.001 a 8.000"
    assert tramo_de("8000.01") == "sobre UF 8.000"


def test_aplicar_el_pct_a_cada_corredor_da_igual_que_al_total():
    """El detalle de redaccion que no cambia el numero.

    El contrato dice "% de la comision de **cada** corredor participante". Como los
    dos cobran lo mismo, aplicarlo a cada uno y sumar es identico a aplicarlo al
    total. La ambiguedad existe pero es inocua, y conviene que este fijado para que
    nadie la "arregle" en una direccion equivocada.
    """
    r = calcular("VENTA", D("200000000"), "CLP", UF)

    por_cada_uno = r.comision_por_corredor * r.pct_dataprop * CORREDORES
    al_total = r.comision_corredores * r.pct_dataprop

    assert por_cada_uno == al_total == r.comision_dataprop


def test_todo_neto_sin_iva():
    """El IVA no es ingreso ni egreso: se recauda y se entrega.

    Se confirmo expresamente. Si algun dia hace falta el bruto, es este numero por
    1,19 y va como una columna aparte, no reemplazando esta.
    """
    r = calcular("VENTA", D("100000000"), "CLP", UF)

    # 6% de 2.000.000 por corredor, por dos: 240.000. Con IVA seria 285.600.
    assert r.comision_dataprop == D("240000.00")


# -------------------------------------------------------- lo que no se calcula


@pytest.mark.parametrize("faltante", ["valor", "moneda", "operacion"])
def test_sin_los_datos_devuelve_nulo_y_no_cero(faltante):
    """Cero dice "no genera comision"; nulo dice "no se sabe". Son distintos.

    Con 303 canjes migrados de un Excel, confundirlos convertiria un dato faltante
    en un cero que se suma y baja los promedios.
    """
    args = {"operacion": "VENTA", "valor": D("1000"), "moneda": "UF", "uf": UF}
    args[faltante] = None

    assert calcular(**args) is None


def test_un_valor_en_cero_no_es_una_comision_de_cero():
    """El canje 18 tenia valor 0: es un dato faltante, no un canje gratis."""
    assert calcular("VENTA", D("0"), "CLP", UF) is None


def test_una_operacion_sin_regla_no_se_inventa():
    """`OTRO` existe en el catalogo y el contrato no le fija comision."""
    assert calcular("OTRO", D("1000"), "UF", UF) is None


def test_una_moneda_sin_conversion_no_se_inventa():
    assert calcular("VENTA", D("1000"), "OTRA", UF) is None


def test_sin_uf_no_se_calcula():
    """Falla el dia que falte el tramo de UF, en vez de agarrar cualquier valor."""
    assert calcular("VENTA", D("1000"), "UF", None) is None


# ------------------------------------------------------ la plata agregada


def test_las_tres_cifras_significan_cosas_distintas(db):
    """Cobrada, potencial y no concretada no son el mismo numero en tres estados.

    La **cobrada** sale del campo manual: cuando un canje cierra, la comision se
    negocia y se factura, asi que es un hecho que se registra. Las otras dos salen
    del motor, porque son proyecciones sobre canjes que no generaron nada todavia.
    """
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))
    db.add(UFDiaria(fecha=date(2026, 6, 1), valor=UF))
    db.add_all([
        # Cerrado: su comision es la que se registro, no la que dice la regla.
        Canje(id=1, fecha_solicitud=datetime(2026, 6, 1, tzinfo=timezone.utc),
              fecha_cierre=datetime(2026, 6, 1, tzinfo=timezone.utc),
              estado=CanjeEstado.CERRADO, etapa=CanjeEtapa.CERRADO, comuna="Santiago",
              tipo_operacion=OperacionTipo.VENTA, valor_prop=10000,
              moneda_valor=MonedaTipo.UF, comision_dataprop=999999),
        # Activo: potencial, con la regla y la UF de hoy.
        Canje(id=2, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
              estado=CanjeEstado.ACTIVO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago",
              tipo_operacion=OperacionTipo.VENTA, valor_prop=10000,
              moneda_valor=MonedaTipo.UF),
        # Cancelado: lo que no se llego a cobrar.
        Canje(id=3, fecha_solicitud=datetime(2026, 6, 1, tzinfo=timezone.utc),
              fecha_cierre=datetime(2026, 6, 15, tzinfo=timezone.utc),
              estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago",
              tipo_operacion=OperacionTipo.VENTA, valor_prop=10000,
              moneda_valor=MonedaTipo.UF),
    ])
    db.commit()

    r = obtener_plata_canjes(db, hoy=hoy)

    # La cobrada es el numero registrado, no el que sale de la regla.
    assert r.cobrada.comision_dataprop == D("999999")
    assert r.cobrada.canjes == 1
    # Las otras dos salen del motor: UF 10.000 esta sobre el tramo de 8.000, o sea
    # 4% de la comision de cada corredor.
    esperado = calcular("VENTA", D("10000"), "UF", UF).comision_dataprop
    assert r.potencial.comision_dataprop == esperado
    assert r.no_concretada.comision_dataprop == esperado


def test_un_cerrado_sin_comision_registrada_cuenta_pero_no_suma(db):
    """Cerro y todavia nadie escribio cuanto se cobro. No es cobrar cero."""
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))
    db.add(Canje(id=1, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
                 estado=CanjeEstado.CERRADO, etapa=CanjeEtapa.CERRADO, comuna="Santiago"))
    db.commit()

    r = obtener_plata_canjes(db, hoy=hoy)

    assert r.cobrada.canjes == 1
    assert r.cobrada.con_monto == 0, "cerro, pero no se registro cuanto"
    assert r.cobrada.comision_dataprop == D("0")


def test_los_plazos_separan_sobrevivencia_de_edad(db):
    """Y ninguna de las dos mide "cuanto tarda en cerrar": no hay un solo caso.

    Llamar "duracion" a la mediana de las cancelaciones seria publicar el tiempo que
    tardan en morir como si fuera el que tardan en cerrar.
    """
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))
    db.add_all([
        # Se cayo a los 10 dias.
        Canje(id=1, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
              fecha_cierre=datetime(2026, 8, 11, tzinfo=timezone.utc),
              estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        # Se cayo a los 20.
        Canje(id=2, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
              fecha_cierre=datetime(2026, 8, 21, tzinfo=timezone.utc),
              estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        # Cancelado sin fecha: su duracion es desconocida y no entra en la mediana.
        Canje(id=3, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
              estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        # Abierto desde hace 7 dias.
        Canje(id=4, fecha_solicitud=datetime(2026, 8, 20, tzinfo=timezone.utc),
              estado=CanjeEstado.ACTIVO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
    ])
    db.commit()

    p = obtener_plata_canjes(db, hoy=hoy).plazos

    assert (p.sobrevivencia_n, p.sobrevivencia_mediana) == (2, 15)
    assert (p.sobrevivencia_min, p.sobrevivencia_max) == (10, 20)
    assert (p.edad_n, p.edad_mediana) == (1, 7)
    assert p.sin_fecha_de_termino == 1


def test_una_duracion_de_cero_dias_es_desconocida(db):
    """Las dos fechas iguales no se distinguen de "el origen traia una sola"."""
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))
    db.add(Canje(id=1, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
                 fecha_cierre=datetime(2026, 8, 1, tzinfo=timezone.utc),
                 estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"))
    db.commit()

    p = obtener_plata_canjes(db, hoy=hoy).plazos

    assert p.sobrevivencia_n == 0
    assert p.sin_fecha_de_termino == 1


def test_sin_uf_para_su_fecha_el_canje_queda_sin_monto(db):
    """No se valoriza con la UF de otro dia: se informa que no se pudo.

    Es el caso real de produccion, donde la serie de UF empieza en 2026 y 178
    canjes se solicitaron antes.
    """
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))
    db.add(Canje(id=1, fecha_solicitud=datetime(2023, 5, 1, tzinfo=timezone.utc),
                 fecha_cierre=datetime(2023, 5, 20, tzinfo=timezone.utc),
                 estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago",
                 tipo_operacion=OperacionTipo.VENTA, valor_prop=5000,
                 moneda_valor=MonedaTipo.UF))
    db.commit()

    r = obtener_plata_canjes(db, hoy=hoy)

    assert r.no_concretada.canjes == 1
    assert r.no_concretada.con_monto == 0
    assert r.no_concretada.comision_dataprop == D("0")


def test_el_potencial_desde_oferta_es_un_subconjunto_de_los_activos(db):
    """Los activos desde EN_OFERTA en adelante, y ninguno mas.

    El usuario pidio ver aparte "la comision potencial de los canjes activos desde
    la etapa oferta en adelante": un activo en revision o negociando el acuerdo
    puede terminar en nada, y uno que llego a oferta ya tiene una contraparte
    poniendo un numero.
    """
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))

    def activo(id_, etapa):
        return Canje(id=id_, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
                     estado=CanjeEstado.ACTIVO, etapa=etapa, comuna="Santiago",
                     tipo_operacion=OperacionTipo.VENTA, valor_prop=10000,
                     moneda_valor=MonedaTipo.UF)

    db.add_all([
        # Antes de la oferta: entran al total y no al de oferta en adelante.
        activo(1, CanjeEtapa.EN_REVISION),
        activo(2, CanjeEtapa.PROCESO_DE_ACUERDO),
        # Desde la oferta: entran a los dos.
        activo(3, CanjeEtapa.EN_OFERTA),
        activo(4, CanjeEtapa.EN_NEGOCIO),
        activo(5, CanjeEtapa.CERRADO),
    ])
    db.commit()

    r = obtener_plata_canjes(db, hoy=hoy)
    uno = calcular("VENTA", D("10000"), "UF", UF).comision_dataprop

    assert r.potencial.canjes == 5
    assert r.potencial.comision_dataprop == uno * 5
    assert r.potencial_desde_oferta.canjes == 3
    assert r.potencial_desde_oferta.comision_dataprop == uno * 3
    # Es un subconjunto: nunca puede pasarse del total.
    assert r.potencial_desde_oferta.comision_dataprop <= r.potencial.comision_dataprop


def test_la_etapa_cerrado_de_un_activo_cuenta_desde_oferta(db):
    """La etapa CERRADO no es el estado CERRADO.

    Un canje puede estar en la etapa de cierre --el tramite-- y seguir activo. De
    esos hay 31 en produccion contra cero cerrados de verdad, asi que dejarlos
    fuera vaciaria la cifra.
    """
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))
    db.add(Canje(id=1, fecha_solicitud=datetime(2026, 8, 1, tzinfo=timezone.utc),
                 estado=CanjeEstado.ACTIVO, etapa=CanjeEtapa.CERRADO, comuna="Santiago",
                 tipo_operacion=OperacionTipo.VENTA, valor_prop=10000,
                 moneda_valor=MonedaTipo.UF))
    db.commit()

    r = obtener_plata_canjes(db, hoy=hoy)

    assert r.potencial_desde_oferta.canjes == 1
    # Y no cuenta como cobrado: no cerro, esta cerrando.
    assert r.cobrada.canjes == 0


def test_un_cancelado_avanzado_no_entra_al_potencial_desde_oferta(db):
    """El corte es por etapa **sobre los activos**, no por etapa a secas."""
    from datetime import date, datetime, timezone

    from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
    from app.models.uf import UFDiaria
    from app.services.plata_canjes import obtener_plata_canjes

    hoy = date(2026, 8, 27)
    db.add(UFDiaria(fecha=hoy, valor=UF))
    db.add(UFDiaria(fecha=date(2026, 6, 1), valor=UF))
    db.add(Canje(id=1, fecha_solicitud=datetime(2026, 6, 1, tzinfo=timezone.utc),
                 fecha_cierre=datetime(2026, 6, 15, tzinfo=timezone.utc),
                 estado=CanjeEstado.CANCELADO, etapa=CanjeEtapa.EN_NEGOCIO, comuna="Santiago",
                 tipo_operacion=OperacionTipo.VENTA, valor_prop=10000,
                 moneda_valor=MonedaTipo.UF))
    db.commit()

    r = obtener_plata_canjes(db, hoy=hoy)

    assert r.potencial.canjes == 0
    assert r.potencial_desde_oferta.canjes == 0
    assert r.no_concretada.canjes == 1
