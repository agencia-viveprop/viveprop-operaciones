"""Tests del esquema de negocios (sprint 6, especificación en D0 y D-020).

El test que da sentido a todo el sprint es
`test_sumar_hitos_no_duplica_el_negocio`: `D-002` se tomó para hacer el doble
conteo imposible, y esa es la propiedad que aquí se verifica sobre la estructura
real, con los números de VVP-3.
"""
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models.canje import MonedaTipo
from app.models.catalogo import EstadoNegocio, ModeloNegocio
from app.models.negocio import (
    Negocio,
    NegocioHito,
    Propiedad,
)
from app.models.obligacion import Obligacion, TipoObligacion


@pytest.fixture
def propiedad(db):
    p = Propiedad(
        direccion="Ladislao Errázuriz 2037", unidad="503", comuna="Providencia"
    )
    db.add(p)
    db.commit()
    return p


@pytest.fixture
def vvp3(db, propiedad):
    """VVP-3 tal como está en el Excel: un negocio, dos hitos.

    Mismo valor (6.088,44 UF) pero 2% en la promesa y 1% en la escritura. Es el
    único caso real con hitos y el que justifica `D-020`.
    """
    negocio = Negocio(
        codigo="VVP-3",
        propiedad=propiedad,
        modelo=ModeloNegocio.MERCADO_PRIMARIO,
        vendedor_arrendador="Inmobiliaria y Constructora DP",
        comprador_arrendatario="Saravia Hermanos",
    )
    negocio.hitos = [
        NegocioHito(
            nombre="PROMESA",
            fecha_inicio=date(2025, 12, 16),
            fecha_cierre=date(2025, 12, 16),
            estado=EstadoNegocio.CERRADO,
            valor_negocio=Decimal("6088.44"),
            moneda=MonedaTipo.UF,
            uf_snapshot=Decimal("39707.30"),
            valor_clp_calculado=Decimal("241755513.61"),
            pct_lado_vendedor=Decimal("0.02"),
            comision_total=Decimal("4835110.00"),
            comision_real_vp=Decimal("2110525.63"),
        ),
        NegocioHito(
            nombre="ESCRITURA",
            fecha_inicio=date(2026, 3, 9),
            fecha_cierre=date(2026, 3, 9),
            estado=EstadoNegocio.CERRADO,
            valor_negocio=Decimal("6088.44"),
            moneda=MonedaTipo.UF,
            uf_snapshot=Decimal("39790.63"),
            valor_clp_calculado=Decimal("242262863.32"),
            pct_lado_vendedor=Decimal("0.01"),
            comision_total=Decimal("2422629.00"),
            comision_real_vp=Decimal("1057477.00"),
        ),
    ]
    db.add(negocio)
    db.commit()
    return negocio


def test_sumar_hitos_no_duplica_el_negocio(db, vvp3):
    """El propósito de D-020: sumar comisiones es sumar hitos, sin filtros.

    Con `padre_id` autorreferencial habría una tercera fila (el padre) que hay
    que recordar excluir. Acá no existe, así que no hay nada que olvidar.
    """
    total = db.scalar(select(func.sum(NegocioHito.comision_total)))
    assert total == Decimal("7257739.00")  # 4.835.110 + 2.422.629

    filas = db.scalar(select(func.count()).select_from(NegocioHito))
    assert filas == 2, "solo los hitos son filas; el negocio no aporta un monto"


def test_los_hitos_llegan_en_orden_cronologico(db, vvp3):
    assert [h.nombre for h in vvp3.hitos] == ["PROMESA", "ESCRITURA"]


def test_un_negocio_simple_es_un_negocio_con_un_hito(db, propiedad):
    """Los 17 negocios sin hitos no son un caso especial."""
    n = Negocio(codigo="VVP-4", propiedad=propiedad, modelo=ModeloNegocio.SECUNDARIO_CONCENTRADORES)
    n.hitos = [NegocioHito(fecha_inicio=date(2026, 1, 2), estado=EstadoNegocio.PERDIDO)]
    db.add(n)
    db.commit()

    assert len(n.hitos) == 1
    assert n.hitos[0].nombre is None


def test_el_codigo_del_negocio_es_unico(db, propiedad):
    db.add(Negocio(codigo="VVP-9", propiedad=propiedad, modelo=ModeloNegocio.MERCADO_PRIMARIO))
    db.commit()

    db.add(Negocio(codigo="VVP-9", propiedad=propiedad, modelo=ModeloNegocio.MERCADO_PRIMARIO))
    with pytest.raises(IntegrityError):
        db.commit()


def test_la_propiedad_no_se_duplica(db, propiedad):
    db.add(Propiedad(direccion="Ladislao Errázuriz 2037", unidad="503", comuna="Providencia"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_una_propiedad_puede_tener_varios_negocios(db, propiedad):
    """El patrón de reintento: la misma unidad se vuelve a trabajar."""
    for codigo, estado in (("VVP-4", EstadoNegocio.PERDIDO),
                           ("VVP-13", EstadoNegocio.PERDIDO),
                           ("VVP-16", EstadoNegocio.CERRADO)):
        n = Negocio(codigo=codigo, propiedad=propiedad,
                    modelo=ModeloNegocio.SECUNDARIO_CONCENTRADORES)
        n.hitos = [NegocioHito(fecha_inicio=date(2026, 1, 2), estado=estado)]
        db.add(n)
    db.commit()

    db.refresh(propiedad)
    assert len(propiedad.negocios) == 3
    assert sum(1 for n in propiedad.negocios if n.hitos[0].estado == EstadoNegocio.CERRADO) == 1


def test_una_obligacion_por_tipo_y_por_hito(db, vvp3):
    hito = vvp3.hitos[0]
    db.add(Obligacion(hito_id=hito.id, tipo=TipoObligacion.FACT_COMISION_TOTAL))
    db.commit()

    db.add(Obligacion(hito_id=hito.id, tipo=TipoObligacion.FACT_COMISION_TOTAL))
    with pytest.raises(IntegrityError):
        db.commit()


def test_las_obligaciones_cuelgan_del_hito_no_del_negocio(db, vvp3):
    """Cada liquidación se factura y se paga por separado."""
    for hito in vvp3.hitos:
        db.add(Obligacion(hito_id=hito.id, tipo=TipoObligacion.FACT_COMISION_TOTAL))
    db.commit()

    assert db.scalar(select(func.count()).select_from(Obligacion)) == 2


def test_borrar_el_negocio_se_lleva_hitos_y_obligaciones(db, vvp3):
    db.add(Obligacion(hito_id=vvp3.hitos[0].id, tipo=TipoObligacion.PAGO_EQUIPO_VP))
    db.commit()

    db.delete(vvp3)
    db.commit()

    assert db.scalar(select(func.count()).select_from(NegocioHito)) == 0
    assert db.scalar(select(func.count()).select_from(Obligacion)) == 0


def test_un_hito_no_puede_colgar_de_un_negocio_inexistente(db):
    db.add(NegocioHito(negocio_id=9999, fecha_inicio=date(2026, 1, 1),
                       estado=EstadoNegocio.ACTIVO))
    with pytest.raises(IntegrityError):
        db.commit()


class TestBaseComision:
    """La base sobre la que calcula el motor del sprint 7 (D-017)."""

    def _hito(self, **kwargs):
        return NegocioHito(fecha_inicio=date(2026, 1, 1), estado=EstadoNegocio.ACTIVO, **kwargs)

    def test_usa_el_calculado_cuando_no_hay_manual(self):
        h = self._hito(valor_clp_calculado=Decimal("42914480.40"))
        assert h.base_comision == Decimal("42914480.40")

    def test_el_manual_le_gana_al_calculado(self):
        """El caso VVP-2: la liquidación real fue 21,7% menor que la regla."""
        h = self._hito(
            valor_clp_calculado=Decimal("104100248.32"),
            valor_clp_manual=Decimal("81505175.00"),
            motivo_valor_manual="Ajustes por costo credito pie ultima hora",
        )
        assert h.base_comision == Decimal("81505175.00")

    def test_sin_valorizacion_no_hay_base(self):
        assert self._hito().base_comision is None
