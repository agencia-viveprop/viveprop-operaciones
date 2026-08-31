"""Facturación y pago: el monto esperado, el registrado y la historia.

El test que da sentido al archivo es
`test_el_monto_del_corredor_viveprop_saca_al_captador_de_la_alianza`: es el mapeo
que costó resolver, y el único de los seis que no es una columna del motor tal
cual. Los datos del Excel lo decidieron --VVP-15 tiene la comisión del broker en
cero con esta fila en un estado real, así que no puede ser la del broker-- y en 17
de las 19 liquidaciones da idéntico a la bruta, así que un error acá pasaría
inadvertido casi siempre.
"""
from datetime import date, datetime, timezone
from decimal import Decimal as D

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo
from app.models.catalogo import Catalogo, EstadoNegocio, ModeloNegocio
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.models.uf import UFDiaria

SOLICITUD = datetime(2026, 8, 1, tzinfo=timezone.utc)


@pytest.fixture
def estados(db):
    """El circuito que pidió el usuario, más un catálogo de otro tipo.

    El de otro tipo está a propósito: `catalogos` es una tabla genérica (`D-021`)
    y nada en la base impide que `estado_id` apunte a una alianza. La validación
    vive en el servicio y hay un test que la ejerce.
    """
    filas = {
        codigo: Catalogo(tipo="estado_facturacion", codigo=codigo, nombre=nombre, orden=i)
        for i, (codigo, nombre) in enumerate(
            (
                ("POR_FACTURAR", "Por Facturar"),
                ("FACTURADO", "Facturado"),
                ("POR_PAGAR", "Por Pagar"),
                ("PAGADO", "Pagado"),
                ("NO_APLICA_CAPTADOR", "No Aplica Captador"),
            ),
            start=1,
        )
    }
    filas["alianza"] = Catalogo(tipo="alianza", codigo="ASSETPLAN", nombre="Assetplan", orden=1)
    filas["de_baja"] = Catalogo(
        tipo="estado_facturacion", codigo="POR_LIQUIDAR", nombre="Por Liquidar",
        orden=9, activo=False,
    )
    db.add_all(list(filas.values()))
    db.commit()
    return {k: v.id for k, v in filas.items()}


@pytest.fixture
def liquidacion(db):
    """Una liquidación con tercero, como los dos hitos de VVP-3.

    Con tercero a propósito: es el único caso donde «Facturación corredor
    ViveProp» y la comisión VP bruta dan distinto, así que sin tercero el test del
    mapeo no probaría nada.
    """
    propiedad = Propiedad(direccion="Ladislao Errázuriz 2037", comuna="Providencia")
    negocio = Negocio(codigo="VVP-3", propiedad=propiedad, modelo=ModeloNegocio.MERCADO_PRIMARIO)
    negocio.hitos = [
        NegocioHito(
            nombre="PROMESA",
            fecha_inicio=date(2025, 12, 16),
            estado=EstadoNegocio.CERRADO,
            comision_total=D("4835110.00"),
            comision_broker=D("0.00"),
            comision_vp_bruta=D("1211314.00"),
            comision_tercero=D("36339.42"),
            comision_equipo=D("117497.46"),
            comision_real_vp=D("1057477.12"),
        )
    ]
    db.add(negocio)
    db.commit()
    return negocio


@pytest.fixture
def canje(db):
    """Un canje cerrado con la comisión de Dataprop ya registrada."""
    c = Canje(
        id=364,
        fecha_solicitud=SOLICITUD,
        estado=CanjeEstado.CERRADO,
        etapa=CanjeEtapa.CERRADO,
        comuna="La Florida",
        corredor_solicitante_nombre="JORGE ROMAN VIVANCO",
        corredor_propietario_nombre="DATABROKERS",
        tipo_operacion=OperacionTipo.VENTA,
        valor_prop=D("4000"),
        moneda_valor=MonedaTipo.UF,
        comision_dataprop=D("1000000.00"),
    )
    db.add(c)
    db.commit()
    return c


def _negocio_simple(db, codigo):
    """Un negocio con una liquidacion y sin comisiones calculadas.

    Con propiedad porque `negocios.propiedad_id` es obligatorio: un negocio sin
    propiedad no existe en el modelo.
    """
    negocio = Negocio(
        codigo=codigo,
        propiedad=Propiedad(direccion=f"Calle {codigo}", comuna="Nunoa"),
        modelo=ModeloNegocio.SECUNDARIO_AGENCIA,
    )
    negocio.hitos = [NegocioHito(fecha_inicio=date(2026, 6, 1), estado=EstadoNegocio.ACTIVO)]
    db.add(negocio)
    db.commit()
    return negocio


def _url(negocio):
    return f"/api/negocios/{negocio.id}/hitos/{negocio.hitos[0].id}/obligaciones"


def _por_tipo(filas):
    return {f["tipo"]: f for f in filas}


# ------------------------------------------------------ los montos esperados


def test_las_seis_partes_aparecen_aunque_no_haya_nada_registrado(cliente, liquidacion, estados):
    """«Sin registrar» es información, y omitir la fila la esconde.

    Si la pantalla mostrara solo lo registrado, una liquidación recién cerrada se
    vería vacía y no habría dónde hacer el primer registro.
    """
    r = cliente.get(_url(liquidacion))
    assert r.status_code == 200, r.text

    filas = r.json()
    assert [f["tipo"] for f in filas] == [
        "FACT_COMISION_TOTAL",
        "PAGO_PARTNER_COMERCIAL",
        "FACT_CORREDOR_VP",
        "FACT_CAPTADOR_ALIANZA",
        "PAGO_EQUIPO_VP",
        "PAGO_COMISION_REAL_VP",
    ]
    assert all(f["registrada"] is False for f in filas)
    assert all(f["estado_codigo"] is None and f["monto"] is None for f in filas)
    # Y el esperado ya está, que es lo que permite prellenar el formulario.
    assert all(f["monto_esperado"] is not None for f in filas)


def test_el_monto_del_corredor_viveprop_saca_al_captador_de_la_alianza(
    cliente, liquidacion, estados
):
    """Bruta **menos** tercero, no la bruta.

    Lo que ViveProp factura por sí mismo no incluye lo que le corresponde al
    captador de la alianza, que se factura aparte en la fila siguiente. Sumar las
    dos tiene que dar la bruta completa.
    """
    filas = _por_tipo(cliente.get(_url(liquidacion)).json())

    vp = D(filas["FACT_CORREDOR_VP"]["monto_esperado"])
    captador = D(filas["FACT_CAPTADOR_ALIANZA"]["monto_esperado"])

    assert vp == D("1211314.00") - D("36339.42")
    assert captador == D("36339.42")
    assert vp + captador == D("1211314.00"), "las dos partes son la bruta completa"


def test_las_otras_cuatro_partes_son_columnas_del_motor(cliente, liquidacion, estados):
    filas = _por_tipo(cliente.get(_url(liquidacion)).json())

    assert D(filas["FACT_COMISION_TOTAL"]["monto_esperado"]) == D("4835110.00")
    assert D(filas["PAGO_PARTNER_COMERCIAL"]["monto_esperado"]) == D("0.00")
    assert D(filas["PAGO_EQUIPO_VP"]["monto_esperado"]) == D("117497.46")
    assert D(filas["PAGO_COMISION_REAL_VP"]["monto_esperado"]) == D("1057477.12")


def test_una_liquidacion_sin_comisiones_calculadas_no_muestra_ceros(cliente, db, estados):
    """Nulo y cero dicen cosas distintas.

    Un hito sin liquidar no tiene comisión calculada. Mostrar cero diría «no
    corresponde plata» cuando lo que pasa es que todavía no se sabe.
    """
    negocio = _negocio_simple(db, "VVP-99")

    filas = cliente.get(_url(negocio)).json()

    assert all(f["monto_esperado"] is None for f in filas)


# ------------------------------------------------------ registrar y la historia


def test_registrar_crea_la_obligacion_con_su_primer_avance(cliente, liquidacion, estados):
    r = cliente.post(
        _url(liquidacion),
        json={
            "tipo": "FACT_COMISION_TOTAL",
            "estado_id": estados["FACTURADO"],
            "monto": "4835110.00",
            "fecha": "2026-08-20",
        },
    )
    assert r.status_code == 200, r.text

    fila = _por_tipo(r.json())["FACT_COMISION_TOTAL"]
    assert fila["registrada"] is True
    assert fila["estado_codigo"] == "FACTURADO"
    assert D(fila["monto"]) == D("4835110.00")
    assert fila["fecha"] == "2026-08-20"
    assert len(fila["avances"]) == 1
    assert fila["avances"][0]["autor"] == "Test"

    # Las otras cinco siguen sin registrar: se registra una parte a la vez.
    otras = [f for f in r.json() if f["tipo"] != "FACT_COMISION_TOTAL"]
    assert all(f["registrada"] is False for f in otras)


def test_el_segundo_avance_no_pisa_lo_que_se_facturo(cliente, liquidacion, estados):
    """La fila espeja el último avance y la historia guarda el anterior.

    Es la razón por la que el avance tiene monto y fecha propios: al facturar se
    registran los de la factura y al pagar los del pago. Con un solo par de campos,
    «cuánto se facturó» se perdería al pagar.
    """
    cliente.post(_url(liquidacion), json={
        "tipo": "PAGO_EQUIPO_VP", "estado_id": estados["FACTURADO"],
        "monto": "117497.46", "fecha": "2026-08-20",
    })
    r = cliente.post(_url(liquidacion), json={
        "tipo": "PAGO_EQUIPO_VP", "estado_id": estados["PAGADO"],
        "monto": "117000.00", "fecha": "2026-08-28",
    })
    assert r.status_code == 200, r.text

    fila = _por_tipo(r.json())["PAGO_EQUIPO_VP"]
    assert fila["estado_codigo"] == "PAGADO"
    assert D(fila["monto"]) == D("117000.00")

    # Del más reciente al más antiguo, como el resto de los historiales.
    assert [a["estado_codigo"] for a in fila["avances"]] == ["PAGADO", "FACTURADO"]
    assert D(fila["avances"][1]["monto"]) == D("117497.46")
    assert fila["avances"][1]["fecha"] == "2026-08-20"


def test_el_monto_registrado_puede_diferir_del_calculado(cliente, liquidacion, estados):
    """El ajuste por acuerdo es un hecho, no un error, y los dos quedan a la vista.

    El usuario lo pidió explícito: «lo que sí debe estar es la opción de poder
    modificar lo que calculaste, ya que podrían existir ajustes o cambios por
    acuerdos o por características de negocios».
    """
    r = cliente.post(_url(liquidacion), json={
        "tipo": "FACT_CORREDOR_VP", "estado_id": estados["FACTURADO"],
        "monto": "1000000.00", "fecha": "2026-08-20",
    })

    fila = _por_tipo(r.json())["FACT_CORREDOR_VP"]
    assert D(fila["monto"]) == D("1000000.00")
    assert D(fila["monto_esperado"]) == D("1174974.58"), "el calculado no se toca"


def test_se_puede_saltar_del_por_facturar_al_pagado(cliente, liquidacion, estados):
    """No se exige el orden del circuito, y el salto queda en la historia.

    En la operación real pasa --se entera de la factura y del pago juntos-- y el
    sistema que lo prohíbe termina con la plata anotada en un campo de texto.
    """
    cliente.post(_url(liquidacion), json={
        "tipo": "PAGO_COMISION_REAL_VP", "estado_id": estados["POR_FACTURAR"],
        "monto": None, "fecha": None,
    })
    r = cliente.post(_url(liquidacion), json={
        "tipo": "PAGO_COMISION_REAL_VP", "estado_id": estados["PAGADO"],
        "monto": "1057477.12", "fecha": "2026-08-28",
    })

    fila = _por_tipo(r.json())["PAGO_COMISION_REAL_VP"]
    assert [a["estado_codigo"] for a in fila["avances"]] == ["PAGADO", "POR_FACTURAR"]


def test_facturado_sin_monto_conocido_se_puede_registrar(cliente, liquidacion, estados):
    """Cero diría «no corresponde plata». Nulo dice «todavía no se sabe cuánto»."""
    r = cliente.post(_url(liquidacion), json={
        "tipo": "FACT_CAPTADOR_ALIANZA", "estado_id": estados["NO_APLICA_CAPTADOR"],
    })
    assert r.status_code == 200, r.text

    fila = _por_tipo(r.json())["FACT_CAPTADOR_ALIANZA"]
    assert fila["registrada"] is True
    assert fila["monto"] is None and fila["fecha"] is None


# ------------------------------------------------------ lo que no se permite


def test_una_parte_de_canje_no_se_puede_registrar_en_un_negocio(cliente, liquidacion, estados):
    """Los dos dominios comparten tabla, no catálogo de partes.

    Una factura «al corredor solicitante» no existe en un negocio, y el CHECK de
    la base no puede impedirlo porque el tipo es válido para la columna.
    """
    r = cliente.post(_url(liquidacion), json={
        "tipo": "FACT_CORREDOR_SOLICITANTE", "estado_id": estados["FACTURADO"],
    })
    assert r.status_code == 400
    assert "no corresponde a un negocio" in r.json()["detail"]


def test_una_parte_de_negocio_no_se_puede_registrar_en_un_canje(cliente, canje, estados):
    r = cliente.post(f"/api/canjes/{canje.id}/obligaciones", json={
        "tipo": "PAGO_EQUIPO_VP", "estado_id": estados["FACTURADO"],
    })
    assert r.status_code == 400
    assert "no corresponde a un canje" in r.json()["detail"]


def test_el_estado_tiene_que_ser_de_facturacion(cliente, liquidacion, estados):
    """El costo de la tabla genérica de catálogos (`D-021`), pagado en el servicio."""
    r = cliente.post(_url(liquidacion), json={
        "tipo": "FACT_COMISION_TOTAL", "estado_id": estados["alianza"],
    })
    assert r.status_code == 400
    assert "estado de facturación" in r.json()["detail"]


def test_un_estado_dado_de_baja_no_se_puede_elegir(cliente, liquidacion, estados):
    r = cliente.post(_url(liquidacion), json={
        "tipo": "FACT_COMISION_TOTAL", "estado_id": estados["de_baja"],
    })
    assert r.status_code == 400
    assert "dado de baja" in r.json()["detail"]


def test_una_liquidacion_de_otro_negocio_es_404(cliente, db, liquidacion, estados):
    """Sin esta verificación la URL mentiría y se mostraría plata ajena."""
    otro = _negocio_simple(db, "VVP-77")

    r = cliente.get(f"/api/negocios/{liquidacion.id}/hitos/{otro.hitos[0].id}/obligaciones")

    assert r.status_code == 404


# ------------------------------------------------------ canjes


def test_el_canje_tiene_dos_facturas_una_por_corredor(cliente, canje, estados):
    """La regla que confirmó el usuario: «una factura por corredor»."""
    r = cliente.get(f"/api/canjes/{canje.id}/obligaciones")
    assert r.status_code == 200, r.text

    filas = r.json()
    assert [f["tipo"] for f in filas] == [
        "FACT_CORREDOR_SOLICITANTE",
        "FACT_CORREDOR_PROPIETARIO",
    ]
    # Mitad y mitad de la comisión registrada de Dataprop: «por regla general
    # deben ser iguales».
    assert all(D(f["monto_esperado"]) == D("500000") for f in filas)


def test_la_comision_registrada_le_gana_al_calculo(cliente, db, canje, estados):
    """De un canje cerrado importa lo que se cobró, no lo que la regla estimaba.

    Es la misma jerarquía de la vista de plata de canjes: la comisión de un cerrado
    se negocia y se registra. Acá se comprueba comparando contra lo que daría el
    motor con la UF cargada, que es un número distinto.
    """
    db.add(UFDiaria(fecha=date(2026, 8, 15), valor=D("40000")))
    canje.fecha_cierre = datetime(2026, 8, 15, tzinfo=timezone.utc)
    db.commit()

    con_registro = cliente.get(f"/api/canjes/{canje.id}/obligaciones").json()
    assert D(con_registro[0]["monto_esperado"]) == D("500000")

    # Sin comisión registrada manda el motor: 4.000 UF a 40.000 = 160.000.000, 2%
    # por corredor y 6% del tramo, o sea 384.000 de Dataprop; 192.000 cada uno.
    canje.comision_dataprop = None
    db.commit()

    sin_registro = cliente.get(f"/api/canjes/{canje.id}/obligaciones").json()
    assert D(sin_registro[0]["monto_esperado"]) == D("192000")


def test_un_canje_sin_uf_para_su_fecha_no_inventa_un_monto(cliente, db, canje, estados):
    """Nulo antes que valorizar con una UF que ese canje nunca tuvo (`D-046`)."""
    canje.comision_dataprop = None
    canje.fecha_cierre = datetime(2022, 5, 10, tzinfo=timezone.utc)
    db.commit()

    filas = cliente.get(f"/api/canjes/{canje.id}/obligaciones").json()

    assert all(f["monto_esperado"] is None for f in filas)


def test_un_canje_cancelado_no_tiene_monto_que_esperar(cliente, db, canje, estados):
    """De un canje que se cayó no hay nada que facturar.

    Se descubrió mirando la pantalla: un cancelado de 2022 mostraba
    $5.721.959.600 por corredor. El motor estaba bien; el canje trae el valor mal
    etiquetado en el Excel de origen --3.500.000 marcado en UF en un arriendo-- y
    valorizarlo con la UF de hoy da miles de millones. Aun con el valor correcto,
    el número no sería un esperado: es una cifra sin destinatario.

    Lo registrado sí se respeta: si alguien alcanzó a facturar antes de que se
    cayera, eso es un hecho.
    """
    canje.estado = CanjeEstado.CANCELADO
    canje.comision_dataprop = None
    db.commit()

    filas = cliente.get(f"/api/canjes/{canje.id}/obligaciones").json()

    assert all(f["monto_esperado"] is None for f in filas)


def test_la_mitad_de_cada_corredor_se_puede_corregir_a_mano(cliente, canje, estados):
    """«Sería bueno tener la opción de modificar manualmente»."""
    r = cliente.post(f"/api/canjes/{canje.id}/obligaciones", json={
        "tipo": "FACT_CORREDOR_PROPIETARIO", "estado_id": estados["FACTURADO"],
        "monto": "600000", "fecha": "2026-08-20",
    })
    assert r.status_code == 200, r.text

    filas = _por_tipo(r.json())
    assert D(filas["FACT_CORREDOR_PROPIETARIO"]["monto"]) == D("600000")
    assert D(filas["FACT_CORREDOR_PROPIETARIO"]["monto_esperado"]) == D("500000")
    assert filas["FACT_CORREDOR_SOLICITANTE"]["registrada"] is False


# ------------------------------------------------------ cobranza


def test_la_cobranza_totaliza_por_parte_y_nunca_en_una_gran_suma(
    cliente, liquidacion, canje, estados
):
    """Los seis conceptos son dos niveles de la misma plata.

    La comisión total se reparte, y lo que le queda a ViveProp se reparte otra vez.
    Un total general contaría la misma plata dos veces, así que la respuesta no
    tiene ninguno: cada parte trae el suyo.
    """
    cliente.post(_url(liquidacion), json={
        "tipo": "FACT_COMISION_TOTAL", "estado_id": estados["FACTURADO"],
        "monto": "4835110.00", "fecha": "2026-08-20",
    })
    cliente.post(_url(liquidacion), json={
        "tipo": "PAGO_EQUIPO_VP", "estado_id": estados["PAGADO"],
        "monto": "117497.46", "fecha": "2026-08-25",
    })

    r = cliente.get("/api/reportes/cobranza")
    assert r.status_code == 200, r.text
    cuerpo = r.json()

    assert not any(k.startswith("total") for k in cuerpo), "no hay ningún total general"

    partes = {p["tipo"]: p for p in cuerpo["negocios"]}
    # La liquidación es CERRADO, así que su plata va en «ganado» y no en las otras
    # dos columnas: lo ganado, lo que está en curso y lo que no se concretó no se
    # suman (`D-063`, `D-095`).
    total = partes["FACT_COMISION_TOTAL"]["registrado"]
    assert D(total["logrado"]) == D("4835110.00")
    assert D(total["en_curso"]) == 0 and D(total["no_concretado"]) == 0
    assert D(partes["PAGO_EQUIPO_VP"]["registrado"]["logrado"]) == D("117497.46")
    # Las partes sin nada registrado están igual, en cero y con cero casos.
    assert partes["PAGO_PARTNER_COMERCIAL"]["casos"] == 0


def test_la_cobranza_separa_la_plata_de_dataprop_de_la_de_viveprop(
    cliente, liquidacion, canje, estados
):
    """Dos listas y ningún total que las cruce (`D-045`).

    ViveProp opera el Centro de Canje a nombre de Dataprop y no percibe nada de él.
    """
    cliente.post(f"/api/canjes/{canje.id}/obligaciones", json={
        "tipo": "FACT_CORREDOR_SOLICITANTE", "estado_id": estados["FACTURADO"],
        "monto": "500000", "fecha": "2026-08-20",
    })

    cuerpo = cliente.get("/api/reportes/cobranza").json()

    de_canjes = {p["tipo"]: p for p in cuerpo["canjes"]}
    # El canje está CERRADO, así que su plata es «cobrada», la primera columna.
    assert D(de_canjes["FACT_CORREDOR_SOLICITANTE"]["registrado"]["logrado"]) == D("500000")
    # Y en negocios no aparece: son dos mundos.
    assert all(p["tipo"].startswith(("FACT_C", "PAGO_")) for p in cuerpo["negocios"])
    assert all(
        D(p["registrado"][destino]) == 0
        for p in cuerpo["negocios"]
        for destino in ("logrado", "en_curso", "no_concretado")
    )


def test_la_cobranza_dice_cuanto_falta_por_registrar(cliente, liquidacion, canje, estados):
    """Para que la vista no parezca completa cuando casi nada se registró.

    Con una liquidación y un canje en la base y nada registrado, los dos contadores
    van en uno; al registrar una parte de la liquidación, el suyo baja a cero.
    """
    antes = cliente.get("/api/reportes/cobranza").json()
    assert antes["liquidaciones_sin_registrar"] == 1
    assert antes["canjes_sin_registrar"] == 1

    cliente.post(_url(liquidacion), json={
        "tipo": "FACT_COMISION_TOTAL", "estado_id": estados["POR_FACTURAR"],
    })

    despues = cliente.get("/api/reportes/cobranza").json()
    assert despues["liquidaciones_sin_registrar"] == 0
    assert despues["canjes_sin_registrar"] == 1


def test_los_tramos_de_una_parte_vienen_en_el_orden_del_circuito(
    cliente, db, liquidacion, estados
):
    """Por Facturar → Facturado → Por Pagar → Pagado, y los «No Aplica» al final."""
    otro = _negocio_simple(db, "VVP-78")

    cliente.post(_url(liquidacion), json={
        "tipo": "FACT_CAPTADOR_ALIANZA", "estado_id": estados["NO_APLICA_CAPTADOR"],
    })
    cliente.post(_url(otro), json={
        "tipo": "FACT_CAPTADOR_ALIANZA", "estado_id": estados["PAGADO"], "monto": "1",
    })

    partes = {p["tipo"]: p for p in cliente.get("/api/reportes/cobranza").json()["negocios"]}
    tramos = [t["estado_codigo"] for t in partes["FACT_CAPTADOR_ALIANZA"]["tramos"]]

    assert tramos == ["PAGADO", "NO_APLICA_CAPTADOR"]


def test_la_cobranza_no_suma_lo_perdido_con_lo_que_se_espera_cobrar(
    cliente, db, liquidacion, estados
):
    """**El defecto que el usuario encontró comparando dos pantallas** (`D-095`).

    La cobranza mostraba un solo total por parte, y el 38% de esa cifra era de
    negocios perdidos: decía $14.663.624 de comisión real VP mientras el listado
    de negocios decía $8.087.862 ganados más $1.824.272 en pipeline. La diferencia
    eran los 10 negocios caídos, sumados sin decirlo.

    Es la regla de `D-063`, que ya estaba tomada para el listado de negocios y que
    esta pantalla había vuelto a romper.
    """
    perdido = Negocio(
        codigo="VVP-CAIDO",
        propiedad=Propiedad(direccion="Se cayó 100", comuna="Nunoa"),
        modelo=ModeloNegocio.MERCADO_PRIMARIO,
    )
    perdido.hitos = [
        NegocioHito(
            fecha_inicio=date(2026, 1, 1),
            estado=EstadoNegocio.PERDIDO,
            comision_total=D("1000000.00"),
        )
    ]
    db.add(perdido)
    db.commit()

    for negocio in (liquidacion, perdido):
        r = cliente.post(
            f"/api/negocios/{negocio.id}/hitos/{negocio.hitos[0].id}/obligaciones",
            json={"tipo": "FACT_COMISION_TOTAL", "estado_id": estados["POR_FACTURAR"]},
        )
        assert r.status_code == 200, r.text

    partes = {p["tipo"]: p for p in cliente.get("/api/reportes/cobranza").json()["negocios"]}
    calculado = partes["FACT_COMISION_TOTAL"]["calculado"]

    # La cerrada en «ganado», la perdida en «no concretado», y ninguna suma que
    # las cruce.
    assert D(calculado["logrado"]) == D("4835110.00")
    assert D(calculado["no_concretado"]) == D("1000000.00")
    assert D(calculado["en_curso"]) == 0


def test_la_cobranza_muestra_el_rebate_aparte_de_las_seis_partes(
    cliente, db, liquidacion, estados
):
    """Sin la fila del rebate, la resta hacia abajo no puede cerrar.

    El rebate entra en la comisión real VP y **no sale de ninguna otra parte**: no
    es un pedazo de la comisión total, es plata que el concentrador comparte con
    ViveProp. Con la fila, la identidad se comprueba: corredor VP − equipo +
    rebate = comisión real VP.
    """
    hito = liquidacion.hitos[0]
    hito.rebate_concentrador = D("50000.00")
    hito.comision_real_vp = D("1107477.12")  # bruta − tercero − equipo + rebate
    db.commit()

    cliente.post(
        _url(liquidacion),
        json={"tipo": "FACT_COMISION_TOTAL", "estado_id": estados["POR_FACTURAR"]},
    )
    cuerpo = cliente.get("/api/reportes/cobranza").json()

    assert D(cuerpo["rebate"]["logrado"]) == D("50000.00")

    partes = {p["tipo"]: p for p in cuerpo["negocios"]}
    vp = D(partes["FACT_CORREDOR_VP"]["calculado"]["logrado"])
    equipo = D(partes["PAGO_EQUIPO_VP"]["calculado"]["logrado"])
    real = D(partes["PAGO_COMISION_REAL_VP"]["calculado"]["logrado"])
    # Las cuatro filas cierran entre sí, que es lo que se pedía: poder comprobar
    # la tabla sumando.
    assert vp - equipo + D(cuerpo["rebate"]["logrado"]) == real


def test_la_cobranza_avisa_cuando_el_reparto_no_cuadra(cliente, db, liquidacion, estados):
    """El descuadre del Excel se dice, no se suma en silencio.

    En el histórico es uno --VVP-2, con $903.803-- y su ficha ya lo avisa en rojo
    desde el sprint 8. La cobranza lo sumaba callada, y ahí la diferencia se lee
    como un error de la pantalla en vez de un dato que hay que corregir.
    """
    hito = liquidacion.hitos[0]
    # Reparto que suma más que la comisión total, como VVP-2.
    hito.comision_broker = D("4000000.00")
    db.commit()

    cliente.post(
        _url(liquidacion),
        json={"tipo": "FACT_COMISION_TOTAL", "estado_id": estados["POR_FACTURAR"]},
    )
    cuerpo = cliente.get("/api/reportes/cobranza").json()

    assert len(cuerpo["descuadres"]) == 1
    descuadre = cuerpo["descuadres"][0]
    assert descuadre["negocio"] == "VVP-3"
    assert descuadre["liquidacion"] == "PROMESA"
    # 4.835.110 − (4.000.000 + 1.211.314) = −376.204
    assert D(descuadre["diferencia"]) == D("4835110.00") - D("4000000.00") - D("1211314.00")


def test_un_reparto_que_cuadra_no_genera_aviso(cliente, db, liquidacion, estados):
    """Un peso de tolerancia: los montos son `numeric(16,2)` y el redondeo no es
    un descuadre."""
    hito = liquidacion.hitos[0]
    hito.comision_broker = D("3623796.00")  # total − bruta, al peso
    db.commit()

    cliente.post(
        _url(liquidacion),
        json={"tipo": "FACT_COMISION_TOTAL", "estado_id": estados["POR_FACTURAR"]},
    )

    assert cliente.get("/api/reportes/cobranza").json()["descuadres"] == []
