"""Los 22 casos del motor de comisiones (sprint 7).

Tres vienen de la hoja `REGLAS CALCULO` y diecinueve de los negocios reales, en
`datos_historicos.py`. Los tests se escribieron antes del motor: la referencia es
el comportamiento observado, no lo que el motor haga.

**Tolerancias.** La planilla guarda `comision_total` redondeada al peso y los
demás montos con todos sus decimales, así que se compara con 1 peso de tolerancia
en el total y 1 centavo en el resto. No es laxitud: es que el Excel redondea ese
campo y el motor no.
"""
from decimal import Decimal as D

import pytest

from app.services.comisiones import calcular
from tests.datos_historicos import HISTORICOS

TOLERANCIA = {"comision_total": D("1"), "_default": D("0.01")}

# Filas que ninguna formula consistente puede reproducir, porque la planilla se
# contradice consigo misma. Van como xfail estricto: si algun dia se corrigen y
# el test empieza a pasar, pytest avisa en vez de dejarlo silenciosamente verde.
INCONSISTENTES = {
    "VVP-2": (
        "La Comision Total se bajo a mano por el ajuste de costo de credito "
        "(3.260.207 en vez de 4.164.010) pero Broker y VP Bruta siguieron "
        "calculados sobre la base original. Broker + VP Bruta supera al total en "
        "903.803. Hay que resolverlo al cargar, en el sprint 10."
    ),
}


def _comparar(obtenido, esperado: dict, contexto: str):
    errores = []
    for campo, valor_esperado in esperado.items():
        valor = getattr(obtenido, campo)
        tol = TOLERANCIA.get(campo, TOLERANCIA["_default"])
        if abs(valor - valor_esperado) > tol:
            errores.append(
                f"    {campo}: motor={valor:,.4f}  excel={valor_esperado:,.4f}  "
                f"dif={valor - valor_esperado:,.4f}"
            )
    assert not errores, f"{contexto} no reproduce el Excel:\n" + "\n".join(errores)


# --------------------------------------------------------------------------
# Los 19 casos de regresión: negocios reales
# --------------------------------------------------------------------------

@pytest.mark.parametrize("caso", HISTORICOS, ids=[c.codigo for c in HISTORICOS])
def test_reproduce_el_excel(caso, request):
    if caso.codigo in INCONSISTENTES:
        request.applymarker(
            pytest.mark.xfail(reason=INCONSISTENTES[caso.codigo], strict=True)
        )
    resultado = calcular(
        modelo=caso.modelo,
        estado=caso.estado,
        base=caso.base_comision,
        **caso.tasas,
    )
    _comparar(resultado, caso.esperado, caso.codigo)


def test_los_19_negocios_estan_cubiertos():
    """Red contra que el fixture se regenere incompleto sin que nadie lo note."""
    assert len(HISTORICOS) == 19
    assert len({c.codigo for c in HISTORICOS}) == 19


def test_los_tres_modelos_estan_cubiertos():
    modelos = {c.modelo for c in HISTORICOS}
    assert modelos == {
        "MERCADO_PRIMARIO",
        "SECUNDARIO_CONCENTRADORES",
        "SECUNDARIO_AGENCIA",
    }


def test_hay_casos_con_y_sin_rebate_y_con_y_sin_tercero():
    """Si el histórico dejara de cubrir estas variantes, el motor quedaría ciego."""
    con_rebate = [c for c in HISTORICOS if c.esperado["rebate_concentrador"] > 0]
    con_tercero = [c for c in HISTORICOS if c.esperado["comision_tercero"] > 0]
    con_manual = [c for c in HISTORICOS if c.base_manual is not None]

    assert len(con_rebate) == 3, "VVP-15, VVP-16 y VVP-17"
    assert len(con_tercero) == 2, "los dos hitos de VVP-3"
    assert len(con_manual) == 1, "VVP-2, el único con liquidación externa (D-017)"


# --------------------------------------------------------------------------
# Los 3 casos documentados en REGLAS CALCULO
# --------------------------------------------------------------------------

def test_reglas_calculo_mercado_primario():
    """5.000 UF al 4%: total 200, broker 125, VP 75, equipo 22,5, real 52,5."""
    r = calcular(
        modelo="MERCADO_PRIMARIO",
        estado="CERRADO",
        base=D("5000"),
        pct_lado_vendedor=D("0.04"),
        pct_lado_comprador=D("0"),
        pct_rebate_concentrador=D("0"),
        pct_broker_vendedor=D("0.025"),
        pct_broker_comprador=D("0"),
        pct_vp_vendedor=D("0.015"),
        pct_vp_comprador=D("0"),
        pct_equipo=D("0.30"),
        pct_tercero=D("0"),
    )
    assert r.comision_total == D("200")
    assert r.comision_broker == D("125")
    assert r.comision_vp_bruta == D("75")
    assert r.comision_equipo == D("22.5")
    assert r.comision_real_vp == D("52.5")


def test_reglas_calculo_secundario_concentradores():
    """4.000 UF al 2% del comprador, más 30 UF de concentrador.

    El ejemplo de la hoja pone el aporte del concentrador como monto fijo. Acá se
    expresa como tasa sobre el lado vendedor, que es la forma verificada en las
    13 filas reales (D-018): 4.000 × 2% × 37,5% = 30.
    """
    r = calcular(
        modelo="SECUNDARIO_CONCENTRADORES",
        estado="CERRADO",
        base=D("4000"),
        pct_lado_vendedor=D("0.02"),
        pct_lado_comprador=D("0.02"),
        pct_rebate_concentrador=D("0.375"),
        pct_broker_vendedor=D("0"),
        pct_broker_comprador=D("0.02"),
        pct_vp_vendedor=D("0"),
        pct_vp_comprador=D("0.02"),
        pct_equipo=D("0.40"),
        pct_tercero=D("0"),
    )
    assert r.comision_total == D("80")
    assert r.comision_broker == D("80")
    assert r.comision_vp_bruta == D("80")
    assert r.comision_equipo == D("32")
    assert r.rebate_concentrador == D("30")
    assert r.comision_real_vp == D("78")


def test_reglas_calculo_secundario_agencia():
    """3.500 UF: 3% del vendedor más 2% del comprador."""
    r = calcular(
        modelo="SECUNDARIO_AGENCIA",
        estado="CERRADO",
        base=D("3500"),
        pct_lado_vendedor=D("0.03"),
        pct_lado_comprador=D("0.02"),
        pct_rebate_concentrador=D("0"),
        pct_broker_vendedor=D("0.015"),
        pct_broker_comprador=D("0.02"),
        pct_vp_vendedor=D("0.015"),
        pct_vp_comprador=D("0.02"),
        pct_equipo=D("0.35"),
        pct_tercero=D("0"),
    )
    assert r.comision_total == D("175")
    assert r.comision_broker == D("122.5")
    assert r.comision_vp_bruta == D("122.5")
    assert abs(r.comision_equipo - D("42.875")) < D("0.01")
    assert abs(r.comision_real_vp - D("79.625")) < D("0.01")


# --------------------------------------------------------------------------
# Reglas del motor, aisladas
# --------------------------------------------------------------------------

def _concentrador(estado, **extra):
    tasas = dict(
        pct_lado_vendedor=D("0.02"),
        pct_lado_comprador=D("0.02"),
        pct_rebate_concentrador=D("0.12"),
        pct_broker_vendedor=D("0"),
        pct_broker_comprador=D("0.012"),
        pct_vp_vendedor=D("0"),
        pct_vp_comprador=D("0.008"),
        pct_equipo=D("0.10"),
        pct_tercero=D("0"),
    )
    tasas.update(extra)
    return calcular(
        modelo="SECUNDARIO_CONCENTRADORES", estado=estado, base=D("100000000"), **tasas
    )


@pytest.mark.parametrize("estado", ["ACTIVO", "CERRADO"])
def test_el_rebate_existe_mientras_el_negocio_viva(estado):
    assert _concentrador(estado).rebate_concentrador == D("240000")


@pytest.mark.parametrize("estado", ["PERDIDO", "DESISTIDO"])
def test_no_hay_rebate_si_el_negocio_no_prospero(estado):
    """Los 10 perdidos tienen la tasa registrada y el monto en cero."""
    assert _concentrador(estado).rebate_concentrador == D("0")


def test_el_rebate_no_entra_en_la_comision_total():
    """Por eso Real VP puede superar la Comisión Total."""
    r = _concentrador("CERRADO")
    assert r.comision_total == D("2000000")
    assert r.rebate_concentrador == D("240000")
    assert r.comision_real_vp > r.comision_vp_bruta


def test_el_equipo_se_calcula_despues_de_sacar_al_tercero():
    """Verificado en las 19 filas: no es VP Bruta × pct_equipo.

    REGLAS CALCULO dice que el porcentaje del equipo aplica sobre la VP Bruta
    completa. Los datos dicen que el tercero sale primero.
    """
    r = calcular(
        modelo="MERCADO_PRIMARIO",
        estado="CERRADO",
        base=D("1000000"),
        pct_lado_vendedor=D("0.02"),
        pct_lado_comprador=D("0"),
        pct_rebate_concentrador=D("0"),
        pct_broker_vendedor=D("0.01"),
        pct_broker_comprador=D("0"),
        pct_vp_vendedor=D("0.01"),
        pct_vp_comprador=D("0"),
        pct_equipo=D("0.10"),
        pct_tercero=D("0.03"),
    )
    assert r.comision_vp_bruta == D("10000")
    assert r.comision_tercero == D("300")
    assert r.comision_equipo == D("970"), "(10000 - 300) x 10%, no 10000 x 10%"
    assert r.comision_real_vp == D("8730")


def test_en_concentradores_el_lado_vendedor_no_entra_en_la_comision():
    """Lo que el concentrador cobra al vendedor no es ingreso ViveProp (D-018)."""
    sin = _concentrador("CERRADO", pct_lado_vendedor=D("0"))
    con = _concentrador("CERRADO", pct_lado_vendedor=D("0.04"))

    assert sin.comision_total == con.comision_total
    assert con.rebate_concentrador == sin.rebate_concentrador * 0 + D("480000")


def test_modelo_desconocido_falla_claro():
    with pytest.raises(ValueError, match="MODELO_INVENTADO"):
        calcular(
            modelo="MODELO_INVENTADO",
            estado="CERRADO",
            base=D("1000"),
            pct_lado_vendedor=D("0.02"),
            pct_lado_comprador=D("0"),
            pct_rebate_concentrador=D("0"),
            pct_broker_vendedor=D("0"),
            pct_broker_comprador=D("0"),
            pct_vp_vendedor=D("0.02"),
            pct_vp_comprador=D("0"),
            pct_equipo=D("0.1"),
            pct_tercero=D("0"),
        )


def test_vvp2_esta_descuadrado_en_el_origen():
    """Deja constancia del descuadre en vez de que se pierda como un xfail.

    No es un problema del motor: es que la planilla bajo la Comision Total sin
    recalcular el reparto. Quien lo lea en el sprint 10 necesita saber cuanto es
    y de donde sale.
    """
    caso = next(c for c in HISTORICOS if c.codigo == "VVP-2")
    e = caso.esperado

    partes = e["comision_broker"] + e["comision_vp_bruta"]
    descuadre = partes - e["comision_total"]

    assert abs(descuadre - D("903802.93")) < D("0.01")

    base_del_broker = e["comision_broker"] / caso.tasas["pct_broker_vendedor"]
    assert abs(base_del_broker - caso.base) < D("1"), (
        "el broker se calculo sobre la base original, no sobre la ajustada"
    )
    assert abs(e["comision_total"] / caso.tasas["pct_lado_vendedor"] - caso.base_manual) < D("1"), (
        "la comision total si uso la base ajustada"
    )


@pytest.mark.parametrize("caso", HISTORICOS, ids=[c.codigo for c in HISTORICOS])
def test_el_reparto_cierra_contra_la_comision_total(caso):
    """La identidad que sostiene el grafico apilado del reparto.

        comision_total + rebate = broker + tercero + equipo + real_vp

    Dicho en palabras: toda la plata que la operacion genera se reparte entre el
    corredor que gestiona, el tercero, el equipo y lo que queda para ViveProp. El
    rebate va del lado izquierdo y no del derecho porque **no es una tajada de la
    comision**: es plata que entra desde afuera, la que el concentrador comparte
    de lo que le cobro al vendedor (`D-018`).

    Este test es la premisa del panel de reparto de `D-064`. Si algun dia deja de
    cerrar, el grafico apilado empieza a mentir: los segmentos ya no suman el alto
    de la barra. Por eso se verifica sobre los 19 historicos y no sobre un caso
    armado, y por eso `VVP-2` va aparte en el test de mas arriba: ahi el descuadre
    es del origen y esta documentado, no del motor.
    """
    if caso.codigo == "VVP-2":
        pytest.skip("descuadrado en el origen; ver test_vvp2_esta_descuadrado_en_el_origen")

    r = calcular(modelo=caso.modelo, estado=caso.estado, base=caso.base_comision, **caso.tasas)

    izquierda = r.comision_total + r.rebate_concentrador
    derecha = r.comision_broker + r.comision_tercero + r.comision_equipo + r.comision_real_vp

    # Sin redondear: el motor devuelve precision completa a proposito, asi que
    # aca la identidad tiene que cerrar exacta. Los centavos de diferencia que se
    # ven en la base salen de guardar los siete montos cuantizados por separado.
    assert izquierda == derecha, f"el reparto no cierra: {izquierda} != {derecha}"
