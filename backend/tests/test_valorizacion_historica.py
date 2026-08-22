"""Que guardar un hito histórico no le mueva la plata.

**El agujero que este archivo tapa.** El motor de comisiones tiene sus 19 casos de
regresión en `test_comisiones.py`, pero ahí la base entra a mano: se le pasa la
columna AC del Excel y se comprueba el reparto. Nunca se probó el paso *anterior*
--`resolver_valorizacion`, que convierte UF a pesos-- y ahí estaba el defecto.

Los 19 hitos se cargaron desde la planilla con `fecha_valorizacion` en nulo en trece
de ellos, así que la primera vez que alguien los guardaba se revalorizaban con la UF
del día de inicio, sobreescribiendo la `uf_snapshot` que traía el Excel. Medido en
`dev`: cerrar `VVP-17` desde la app le bajó la comisión real de 774.691,95 a
759.166,55 sin tocar una sola tasa. La migración `f5a92c3d81e6` lo arregló dejando
cada fila consistente consigo misma; esto es lo que impide que vuelva a pasar.

**La comprobación es de dos lados**, porque un test que solo compare el JSON contra
sí mismo no prueba nada:

1. Los montos del JSON son los del Excel --se contrastan contra `HISTORICOS`, el
   fixture generado de la planilla, que es la fuente de verdad del sprint 7.
2. Pasando las *entradas* del JSON por `refrescar_hito`, con la UF de verdad y no
   con la que cada fila afirma, salen esos mismos montos.

Juntas dicen lo único que importa: guardar un negocio histórico lo deja igual.

`VVP-2` es la única excepción y está nombrada. Esa fila usó dos bases a la vez --el
total sobre 81.505.175 y el broker y la VP bruta sobre los 104.100.248,32 de la UF--
así que ninguna base única la reproduce; `test_comisiones.py` ya la tiene como
`xfail` estricto por lo mismo. Acá se afirma *cuánto* se movería, para que el día que
se decida qué base es la correcta el número esté a la vista.
"""
import json
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import pytest

from app.models.canje import MonedaTipo
from app.models.catalogo import EstadoNegocio
from app.models.negocio import NegocioHito
from app.models.uf import UFDiaria
from app.services.negocios import refrescar_hito

from tests.datos_historicos import HISTORICOS

DATOS = Path(__file__).resolve().parents[1] / "alembic" / "datos" / "historicos.json"

# La fila que se contradice consigo misma. Ver el docstring.
IRRECONCILIABLE = "VVP-2"

MONTOS = (
    "comision_total", "comision_broker", "rebate_concentrador", "comision_vp_bruta",
    "comision_equipo", "comision_tercero", "comision_real_vp",
)

TASAS = (
    "pct_lado_vendedor", "pct_lado_comprador", "pct_rebate_concentrador",
    "pct_broker_vendedor", "pct_broker_comprador", "pct_vp_vendedor",
    "pct_vp_comprador", "pct_equipo", "pct_tercero",
)

# La UF de verdad para las 16 fechas que estos 19 hitos necesitan. Van acá y no
# derivadas del `uf_snapshot` de cada fila, porque derivarlas volvería el test
# circular: se le estaría dando por buena justamente la UF que hay que comprobar,
# y el defecto original --una fila que afirma una UF que su propia fecha no
# produce-- pasaría inadvertido.
#
# Los valores son los de `uf_diaria`, que se verificó contra el SII en el sprint
# 15: 617 fechas, cero diferencias.
#
# Incluye también la UF de las seis fechas de inicio que no son la de valorización.
# No hacen falta para que el test pase; hacen falta para que **falle bien**: si
# alguien vuelve a dejar `fecha_valorizacion` en nulo, sin ellas el test moriría con
# "no hay UF de esa fecha" en vez de decir cuánta plata se movió.
UF_SERIE = {
    date(2025, 8, 12): D("39167.40"),
    date(2025, 10, 7): D("39485.65"),
    date(2025, 12, 10): D("39647.42"),
    date(2025, 12, 16): D("39670.41"),
    date(2026, 1, 2): D("39735.63"),
    date(2026, 1, 6): D("39751.00"),
    date(2026, 1, 3): D("39739.47"),
    date(2026, 1, 8): D("39758.68"),
    date(2026, 1, 10): D("39759.95"),
    date(2026, 1, 14): D("39749.68"),
    date(2026, 1, 23): D("39726.59"),
    date(2026, 1, 28): D("39713.76"),
    date(2026, 2, 1): D("39703.50"),
    date(2026, 2, 28): D("39790.63"),
    date(2026, 3, 5): D("39819.01"),
    date(2026, 3, 9): D("39841.72"),
    date(2026, 3, 29): D("39841.72"),
    date(2026, 4, 12): D("39881.38"),
    date(2026, 4, 24): D("40040.43"),
    date(2026, 6, 1): D("40627.62"),
    date(2026, 6, 15): D("40779.55"),
    date(2026, 8, 20): D("40859.28"),
}


def _dec(valor) -> D | None:
    return None if valor is None else D(str(valor))


def _fecha(valor) -> date | None:
    return None if valor is None else date.fromisoformat(valor)


def _etiqueta(fila: dict) -> str:
    """El mismo formato que usa `HISTORICOS.codigo`: 'VVP-3 PROMESA'."""
    return f"{fila['negocio']} {fila['nombre'] or ''}".strip()


def _cargar() -> list[dict]:
    return json.loads(DATOS.read_text(encoding="utf-8"))["hitos"]


def _sembrar_uf(db) -> None:
    db.add_all([UFDiaria(fecha=f, valor=v) for f, v in UF_SERIE.items()])
    db.commit()


HITOS = _cargar()
IDS = [_etiqueta(h) for h in HITOS]


def test_el_fixture_cubre_las_19_filas():
    assert len(HITOS) == 19
    assert len(set(IDS)) == 19, "hay dos hitos con la misma etiqueta"
    assert {c.codigo for c in HISTORICOS} == set(IDS), (
        "el JSON de la migración y el fixture del Excel dejaron de hablar de los "
        "mismos negocios"
    )


@pytest.mark.parametrize("fila", HITOS, ids=IDS)
def test_los_montos_del_json_son_los_del_excel(fila):
    """Primer lado: lo que la migración carga es lo que decía la planilla.

    `comision_total` va con tolerancia de un peso porque el Excel la guardaba
    redondeada y las demás columnas con todos sus decimales. Las que importan --la
    comisión real y su reparto-- se exigen al centavo.
    """
    caso = next(c for c in HISTORICOS if c.codigo == _etiqueta(fila))

    for campo in MONTOS:
        esperado = caso.esperado[campo]
        obtenido = _dec(fila[campo])
        tolerancia = D("1") if campo == "comision_total" else D("0.01")
        assert abs(obtenido - esperado) <= tolerancia, (
            f"{caso.codigo}: {campo} cargado {obtenido}, el Excel decía {esperado}"
        )


@pytest.mark.parametrize("fila", HITOS, ids=IDS)
def test_recalcular_no_mueve_la_plata(db, fila):
    """Segundo lado, y el que atrapa el defecto: guardar no cambia nada.

    Se arma el hito con las entradas del JSON --valor, moneda, las dos fechas, la
    base a mano y las nueve tasas-- y se le pasa el motor completo. Los nueve
    montos guardados tienen que salir idénticos.
    """
    etiqueta = _etiqueta(fila)
    caso = next(c for c in HISTORICOS if c.codigo == etiqueta)

    _sembrar_uf(db)

    hito = NegocioHito(
        negocio_id=1,
        nombre=fila["nombre"],
        fecha_inicio=_fecha(fila["fecha_inicio"]),
        fecha_cierre=_fecha(fila["fecha_cierre"]),
        estado=EstadoNegocio(fila["estado"]),
        valor_negocio=_dec(fila["valor_negocio"]),
        moneda=MonedaTipo(fila["moneda"]),
        fecha_valorizacion=_fecha(fila["fecha_valorizacion"]),
        valor_clp_manual=_dec(fila["valor_clp_manual"]),
        **{t: _dec(fila[t]) for t in TASAS},
    )

    refrescar_hito(db, hito, caso.modelo)

    assert hito.uf_snapshot == _dec(fila["uf_snapshot"]), (
        f"{etiqueta}: la UF congelada cambió. La fila afirma una UF que su propia "
        f"fecha de valorización no produce."
    )
    assert hito.valor_clp_calculado == _dec(fila["valor_clp_calculado"])

    if etiqueta == IRRECONCILIABLE:
        pytest.skip("se verifica aparte, en test_vvp2_se_movería_y_cuánto")

    for campo in MONTOS:
        assert getattr(hito, campo) == _dec(fila[campo]), (
            f"{etiqueta}: guardar el hito cambió {campo} de {fila[campo]} a "
            f"{getattr(hito, campo)}. Eso es plata moviéndose sola."
        )


def test_vvp2_se_moveria_y_cuanto(db):
    """La excepción, con su número a la vista en vez de escondida en un skip.

    `VVP-2` calculó el total sobre 81.505.175 y el reparto sobre los 104.100.248,32
    de la UF. Como `base_comision` es una sola, el motor no puede llegar a las dos
    cifras: reproduce el reparto --que es la plata que se cobró-- y sube el total
    hasta lo que esa base implica. La diferencia es el descuadre de 903.803 que
    viene del origen (`D-017`) y que la ficha del negocio muestra.

    Si algún día se resuelve con la contraparte, este test falla y hay que venir a
    borrarlo. Es la idea.
    """
    fila = next(h for h in HITOS if _etiqueta(h) == IRRECONCILIABLE)
    caso = next(c for c in HISTORICOS if c.codigo == IRRECONCILIABLE)

    _sembrar_uf(db)

    hito = NegocioHito(
        negocio_id=1,
        fecha_inicio=_fecha(fila["fecha_inicio"]),
        fecha_cierre=_fecha(fila["fecha_cierre"]),
        estado=EstadoNegocio(fila["estado"]),
        valor_negocio=_dec(fila["valor_negocio"]),
        moneda=MonedaTipo(fila["moneda"]),
        fecha_valorizacion=_fecha(fila["fecha_valorizacion"]),
        valor_clp_manual=_dec(fila["valor_clp_manual"]),
        **{t: _dec(fila[t]) for t in TASAS},
    )
    refrescar_hito(db, hito, caso.modelo)

    # El reparto sí se reproduce: eso es lo que se cobró.
    assert hito.comision_broker == _dec(fila["comision_broker"])
    assert hito.comision_vp_bruta == _dec(fila["comision_vp_bruta"])
    assert hito.comision_real_vp == _dec(fila["comision_real_vp"])

    # El total no, y por exactamente el descuadre del origen.
    guardado = _dec(fila["comision_total"])
    assert hito.comision_total != guardado
    descuadre = hito.comision_total - guardado
    assert descuadre == D("903802.93"), (
        f"el descuadre de VVP-2 cambió: era 903.802,93 y ahora es {descuadre}"
    )
