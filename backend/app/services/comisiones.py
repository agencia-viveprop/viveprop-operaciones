"""Motor de comisiones. Funcion pura: no toca la base de datos.

La formula esta verificada contra las 19 filas del Excel historico y los 3
ejemplos de la hoja `REGLAS CALCULO` (ver tests/test_comisiones.py). Donde la
hoja y los datos discrepan, mandan los datos, y esta documentado abajo.

**Que significa cada tasa.** `pct_lado_vendedor` y `pct_lado_comprador` son "que
porcentaje paga cada lado de la operacion". Su destino depende del modelo:

- **Mercado Primario** -- paga la inmobiliaria, del lado vendedor. La comision
  del negocio es `base x pct_lado_vendedor`.
- **Secundario Concentradores** -- paga el comprador. Lo del lado vendedor lo
  cobra el concentrador y **no es ingreso ViveProp**: solo sirve de base para el
  rebate que el concentrador comparte (D-018). Ese detalle es el que tenia
  trabado el sprint, porque el Excel llama a esa columna "% Comision Vendedor".
- **Secundario Agencia** -- pagan los dos lados y la comision es la suma. En
  arriendo son 50% y 50% de un mes.

**Dos diferencias con REGLAS CALCULO**, ambas resueltas a favor de los datos:

1. El porcentaje del equipo se aplica **despues** de sacar al tercero, no sobre
   la VP Bruta completa. Solo se nota en los dos hitos de VVP-3, que son los
   unicos con tercero, pero ahi son 7.252 pesos de diferencia.
2. La hoja ejemplifica el aporte del concentrador como un monto fijo en UF. En
   la practica es una tasa (12%) sobre lo que el concentrador cobra al vendedor.

**Cuidado al leer la planilla.** Tiene columnas pobladas que el modelo no usa:
en las 13 filas de Concentradores, `% Comision Comprador` vale 0,02 y `% VP
Vendedor` vale 0,008 sin participar del calculo. Por eso el reparto se resuelve
con una rama explicita por modelo y no sumando los dos lados.
"""
from dataclasses import dataclass
from decimal import Decimal

MERCADO_PRIMARIO = "MERCADO_PRIMARIO"
SECUNDARIO_CONCENTRADORES = "SECUNDARIO_CONCENTRADORES"
SECUNDARIO_AGENCIA = "SECUNDARIO_AGENCIA"

MODELOS = (MERCADO_PRIMARIO, SECUNDARIO_CONCENTRADORES, SECUNDARIO_AGENCIA)

# Un negocio que no prospero no genera rebate: en los 10 perdidos del historico
# la tasa esta registrada y el monto es cero.
ESTADOS_SIN_REBATE = ("PERDIDO", "DESISTIDO")

CERO = Decimal("0")


@dataclass(frozen=True)
class Comisiones:
    """Los montos del orden universal, sin redondear.

    Se devuelven en precision completa a proposito: el redondeo es decision de
    quien persiste o muestra, no del calculo. Las columnas de la base son
    `numeric(16,2)`.
    """

    comision_total: Decimal
    comision_broker: Decimal
    rebate_concentrador: Decimal
    comision_vp_bruta: Decimal
    comision_equipo: Decimal
    comision_tercero: Decimal
    comision_real_vp: Decimal


def _reparto(
    modelo: str,
    base: Decimal,
    pct_lado_vendedor: Decimal,
    pct_lado_comprador: Decimal,
    pct_broker_vendedor: Decimal,
    pct_broker_comprador: Decimal,
    pct_vp_vendedor: Decimal,
    pct_vp_comprador: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Comision total, broker y VP bruta. Cada modelo lee el lado que le toca.

    Ojo: NO se pueden sumar los dos lados asumiendo que el otro es cero. La
    planilla puebla columnas que ese modelo no usa -- en las 13 filas de
    Concentradores, `% VP Vendedor` vale 0,008 y `% Comision Comprador` vale
    0,02 sin participar del calculo. Sumar duplicaba la VP Bruta.
    """
    if modelo == MERCADO_PRIMARIO:
        # Paga la inmobiliaria, del lado vendedor.
        return (
            base * pct_lado_vendedor,
            base * pct_broker_vendedor,
            base * pct_vp_vendedor,
        )

    if modelo == SECUNDARIO_CONCENTRADORES:
        # Paga el comprador. Lo del lado vendedor lo cobra el concentrador y
        # solo entra como base del rebate.
        return (
            base * pct_lado_comprador,
            base * pct_broker_comprador,
            base * pct_vp_comprador,
        )

    # Secundario Agencia: pagan los dos lados y todo se suma.
    return (
        base * (pct_lado_vendedor + pct_lado_comprador),
        base * (pct_broker_vendedor + pct_broker_comprador),
        base * (pct_vp_vendedor + pct_vp_comprador),
    )


def calcular(
    *,
    modelo: str,
    estado: str,
    base: Decimal,
    pct_lado_vendedor: Decimal = CERO,
    pct_lado_comprador: Decimal = CERO,
    pct_rebate_concentrador: Decimal = CERO,
    pct_broker_vendedor: Decimal = CERO,
    pct_broker_comprador: Decimal = CERO,
    pct_vp_vendedor: Decimal = CERO,
    pct_vp_comprador: Decimal = CERO,
    pct_equipo: Decimal = CERO,
    pct_tercero: Decimal = CERO,
) -> Comisiones:
    """Calcula las comisiones de un hito.

    `base` es la base de comision de D-017: `valor_clp_manual` si existe, si no
    `valor_clp_calculado`. El motor no sabe de donde vino ni le importa.
    """
    if modelo not in MODELOS:
        raise ValueError(
            f"Modelo de negocio desconocido: '{modelo}'. "
            f"Los validos son: {', '.join(MODELOS)}."
        )

    comision_total, comision_broker, comision_vp_bruta = _reparto(
        modelo,
        base,
        pct_lado_vendedor,
        pct_lado_comprador,
        pct_broker_vendedor,
        pct_broker_comprador,
        pct_vp_vendedor,
        pct_vp_comprador,
    )

    if modelo == SECUNDARIO_CONCENTRADORES and estado not in ESTADOS_SIN_REBATE:
        rebate = base * pct_lado_vendedor * pct_rebate_concentrador
    else:
        rebate = CERO

    comision_tercero = comision_vp_bruta * pct_tercero
    # El tercero sale antes de aplicar el porcentaje del equipo.
    comision_equipo = (comision_vp_bruta - comision_tercero) * pct_equipo

    comision_real_vp = comision_vp_bruta - comision_tercero - comision_equipo + rebate

    return Comisiones(
        comision_total=comision_total,
        comision_broker=comision_broker,
        rebate_concentrador=rebate,
        comision_vp_bruta=comision_vp_bruta,
        comision_equipo=comision_equipo,
        comision_tercero=comision_tercero,
        comision_real_vp=comision_real_vp,
    )
