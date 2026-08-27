"""Motor de comisiones de canjes. Función pura: no toca la base de datos.

**La plata de un canje es de Dataprop, no de ViveProp.** ViveProp no participa en
los canjes ni percibe nada de ellos: opera el Centro de Canje a nombre de Dataprop.
Por eso todo lo que sale de acá se muestra rotulado como comisión de Dataprop y
**nunca se suma con la plata de negocios**, que sí es ingreso de ViveProp. Son dos
mundos distintos dentro de la misma app.

**Las reglas.** El contrato del Centro de Canje dice:

> 1. Por cada operación de compraventa cerrada, Dataprop percibirá una comisión de
>    administración, supervisión y arbitraje: hasta UF 4.000 → 6% + IVA de la
>    comisión de cada corredor participante; entre UF 4.001 y UF 8.000 → 5%; sobre
>    UF 8.000 → 4%.
> 2. Por cada operación de arriendo cerrada → 8% + IVA de la comisión total.

Y la tasa de corretaje que se asume, confirmada por el usuario: **2% por cada
corredor en venta** y **50% por cada corredor en arriendo**, las dos sobre el precio
de la propiedad. Participan dos corredores --el solicitante y el propietario-- así
que la comisión total es 4% del precio en venta y un mes completo en arriendo.

**El tramo lo define el valor de la operación en UF**, no la comisión. Un canje
guardado en pesos se convierte a UF solo para elegir el tramo.

**Todo neto, sin IVA.** El IVA no es ingreso ni egreso: se recauda y se entrega. La
reportería de gestión se lee neta, igual que toda la plata de negocios en esta app.

**Un detalle de la redacción que no cambia el número.** El contrato dice "% de la
comisión de **cada** corredor participante". Como los dos corredores cobran lo
mismo, aplicar el porcentaje a cada comisión y sumar da idéntico a aplicarlo a la
comisión total. La ambigüedad existe pero es inocua.
"""
from dataclasses import dataclass
from decimal import Decimal

from app.models.canje import MonedaTipo, OperacionTipo

CENTAVO = Decimal("0.01")
CERO = Decimal("0")

# La tasa de corretaje que se asume, por corredor y sobre el precio.
PCT_CORREDOR_VENTA = Decimal("0.02")
PCT_CORREDOR_ARRIENDO = Decimal("0.50")

# Solicitante y propietario. No es una constante de configuración: un canje es un
# intercambio entre dos corredores, y si fueran otros tantos ya no sería un canje.
CORREDORES = 2

# La escala de Dataprop en venta: (tope en UF, porcentaje). El último tramo no
# tiene tope.
TRAMOS_VENTA: tuple[tuple[Decimal | None, Decimal, str], ...] = (
    (Decimal("4000"), Decimal("0.06"), "hasta UF 4.000"),
    (Decimal("8000"), Decimal("0.05"), "UF 4.001 a 8.000"),
    (None, Decimal("0.04"), "sobre UF 8.000"),
)

PCT_ARRIENDO = Decimal("0.08")
TRAMO_ARRIENDO = "8% de la comisión total"


@dataclass(frozen=True)
class ComisionCanje:
    """Los montos de un canje, todos en pesos y todos netos.

    `valor_uf` va aunque el canje esté en pesos: es lo que decide el tramo, así que
    tenerlo a la vista es lo que hace auditable el porcentaje aplicado.
    """

    valor_clp: Decimal
    valor_uf: Decimal
    tramo: str
    pct_dataprop: Decimal
    comision_por_corredor: Decimal
    comision_corredores: Decimal
    comision_dataprop: Decimal


def _tramo(valor_uf: Decimal) -> tuple[Decimal, str]:
    for tope, pct, nombre in TRAMOS_VENTA:
        if tope is None or valor_uf <= tope:
            return pct, nombre
    ultimo = TRAMOS_VENTA[-1]
    return ultimo[1], ultimo[2]


def calcular(
    operacion: OperacionTipo | str | None,
    valor: Decimal | None,
    moneda: MonedaTipo | str | None,
    uf: Decimal,
) -> ComisionCanje | None:
    """La comisión de Dataprop de un canje, o `None` si no se puede calcular.

    Devuelve `None` --y no cero-- cuando falta el valor, la moneda o el tipo de
    operación. Son cosas distintas: cero dice "no genera comisión" y nulo dice "no
    se sabe". Con 303 canjes migrados de un Excel, esa diferencia importa.

    `uf` la elige quien llama, porque depende del caso: la de hoy para un canje
    abierto --es un potencial, vale lo que valdría si cerrara ahora--, la del cierre
    para uno cerrado, y la de la solicitud para uno cancelado, que es cuando se
    registró ese valor de propiedad.
    """
    if valor is None or valor <= CERO or moneda is None or operacion is None:
        return None
    if uf is None or uf <= CERO:
        return None

    op = operacion.value if hasattr(operacion, "value") else str(operacion)
    mon = moneda.value if hasattr(moneda, "value") else str(moneda)
    if op not in ("VENTA", "ARRIENDO"):
        # `OTRO` existe en el catálogo y no tiene regla de comisión definida.
        return None
    if mon not in ("CLP", "UF"):
        return None

    valor = Decimal(valor)
    valor_clp = valor * uf if mon == "UF" else valor
    valor_uf = valor if mon == "UF" else valor / uf

    if op == "VENTA":
        por_corredor = valor_clp * PCT_CORREDOR_VENTA
        pct, tramo = _tramo(valor_uf)
        # "% de la comisión de cada corredor participante", y participan dos.
        dataprop = por_corredor * pct * CORREDORES
    else:
        por_corredor = valor_clp * PCT_CORREDOR_ARRIENDO
        pct, tramo = PCT_ARRIENDO, TRAMO_ARRIENDO
        # Acá el contrato dice "de la comisión total", no "de cada corredor".
        dataprop = (por_corredor * CORREDORES) * pct

    return ComisionCanje(
        valor_clp=valor_clp.quantize(CENTAVO),
        valor_uf=valor_uf.quantize(CENTAVO),
        tramo=tramo,
        pct_dataprop=pct,
        comision_por_corredor=por_corredor.quantize(CENTAVO),
        comision_corredores=(por_corredor * CORREDORES).quantize(CENTAVO),
        comision_dataprop=dataprop.quantize(CENTAVO),
    )
