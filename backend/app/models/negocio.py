import enum
import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.canje import MonedaTipo
from app.models.catalogo import EstadoNegocio, ModeloNegocio
from app.models.usuario import utcnow

# Los porcentajes se guardan con 14 decimales porque el historico trae valores
# despejados a mano como 0.0252001208200461. Truncarlos haria que las comisiones
# no cuadren al peso contra el Excel, que es el criterio del sprint 7.
PCT = Numeric(16, 14)
MONTO = Numeric(16, 2)


class Propiedad(Base):
    """La unidad fisica, separada del negocio (D0 seccion 2).

    Existe para hacer visibles los reintentos: hay 5 unidades trabajadas en mas
    de un negocio, y `Mario Kreutzberger 1520 u.316-A` tomo tres intentos hasta
    cerrar. En el Excel eso es invisible.

    La clave unica es una red minima, no una solucion: en los datos reales la
    misma unidad aparece escrita distinto ("Av. Fernandez Albano 492" contra
    "Fernandez Albano 492"). La deteccion de duplicados vive en el alta, que
    ofrece propiedades parecidas antes de crear una nueva.
    """

    __tablename__ = "propiedades"
    __table_args__ = (
        UniqueConstraint("direccion", "unidad", "comuna", name="uq_propiedades_direccion_unidad_comuna"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    direccion: Mapped[str] = mapped_column(Text, nullable=False)
    unidad: Mapped[str | None] = mapped_column(String(40), nullable=True)
    comuna: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo_propiedad_id: Mapped[int | None] = mapped_column(ForeignKey("catalogos.id"), nullable=True)
    estado_propiedad_id: Mapped[int | None] = mapped_column(ForeignKey("catalogos.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    negocios: Mapped[list["Negocio"]] = relationship(back_populates="propiedad")


def clave_de_orden(codigo: str | None) -> tuple[str, int]:
    """Cómo se ordena un código de negocio: por su prefijo y por su **número**.

    Ordenar `codigo` como texto pone `VVP-10` antes de `VVP-2`, porque compara
    caracter por caracter y el "1" es menor que el "2". En una lista de 18 negocios
    eso deja el orden alfabético que nadie espera: VVP-1, VVP-10, VVP-11 ... VVP-2.

    Se resuelve en Python y no en SQL a propósito. Extraer el número necesitaría
    `substring(... from '[0-9]+$')::int`, que es de Postgres, y dejaría el orden sin
    poder probarse contra la base en memoria -- el mismo motivo por el que el
    agrupamiento por mes del reporte mensual también se hace acá.

    Un código sin número al final va **antes** que los numerados de su prefijo, y no
    en un lugar arbitrario: `-1` es determinista y no colisiona con ningún número
    real.
    """
    if not codigo:
        return ("", -1)
    match = re.match(r"^(.*?)(\d+)$", codigo.strip())
    if match is None:
        return (codigo.strip().upper(), -1)
    return (match.group(1).upper(), int(match.group(2)))


class Negocio(Base):
    """El negocio: lo que no cambia entre sus hitos (D-020).

    Dos tablas y no autorreferencia, porque `D-002` se tomo para hacer el doble
    conteo imposible y un `padre_id` solo lo hace evitable. Aca sumar comisiones
    es siempre sumar `negocio_hitos`, sin filtros.

    `movimientos` apunta a esta tabla, no a los hitos: el pipeline E1-E7 es del
    negocio y el hito es una liquidacion dentro de el. Ese vinculo no tiene ni
    puede tener clave foranea porque `movimientos.entity_id` es polimorfico
    (canje o negocio); la validacion de que el negocio exista vive en la capa de
    servicio, como ya lo hace `crear_movimiento_canje`.
    """

    __tablename__ = "negocios"
    __table_args__ = (Index("ix_negocios_modelo_alianza", "modelo", "alianza_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # 'VVP-3'. No es la clave primaria porque movimientos.entity_id es bigint
    # y un PK de texto dejaria a negocios fuera de la linea de tiempo (D-013).
    codigo: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)

    propiedad_id: Mapped[int] = mapped_column(ForeignKey("propiedades.id"), nullable=False)
    modelo: Mapped[ModeloNegocio] = mapped_column(
        Enum(ModeloNegocio, name="modelo_negocio"), nullable=False
    )
    alianza_id: Mapped[int | None] = mapped_column(ForeignKey("catalogos.id"), nullable=True)
    tipo_operacion_id: Mapped[int | None] = mapped_column(ForeignKey("catalogos.id"), nullable=True)
    # El pipeline E1-E7 es del negocio, no del hito: un negocio esta en un punto
    # de su avance, y sus liquidaciones son eventos dentro de ese avance. Lo
    # mueve `crear_movimiento_negocio` via `etapa_resultante` del tipo.
    etapa: Mapped[str | None] = mapped_column(ForeignKey("etapas.codigo"), nullable=True)

    vendedor_arrendador: Mapped[str | None] = mapped_column(Text, nullable=True)
    comprador_arrendatario: Mapped[str | None] = mapped_column(Text, nullable=True)
    corredor_agente: Mapped[str | None] = mapped_column(Text, nullable=True)

    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    propiedad: Mapped["Propiedad"] = relationship(back_populates="negocios")
    hitos: Mapped[list["NegocioHito"]] = relationship(
        back_populates="negocio", cascade="all, delete-orphan", order_by="NegocioHito.fecha_inicio"
    )


class NegocioHito(Base):
    """La liquidacion: un negocio simple tiene uno, VVP-3 tiene dos.

    Cada hito se valoriza, se comisiona, se factura y se paga por separado:
    VVP-3 PROMESA cobra 2% y VVP-3 ESCRITURA 1% del mismo valor.

    Los 17 negocios simples son un negocio con un hito de `nombre` nulo. No hay
    caso especial ni rama en el codigo.
    """

    __tablename__ = "negocio_hitos"
    __table_args__ = (
        Index("ix_negocio_hitos_negocio", "negocio_id"),
        Index("ix_negocio_hitos_estado_cierre", "estado", "fecha_cierre"),
        Index("ix_negocio_hitos_fecha_cierre", "fecha_cierre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    negocio_id: Mapped[int] = mapped_column(
        ForeignKey("negocios.id", ondelete="CASCADE"), nullable=False
    )
    # 'PROMESA', 'ESCRITURA', o nulo cuando el negocio tiene un solo hito.
    nombre: Mapped[str | None] = mapped_column(String(60), nullable=True)

    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_cierre: Mapped[date | None] = mapped_column(Date, nullable=True)
    # `estado` si vive en el hito: que la promesa cierre y la escritura se caiga
    # es un escenario real, aunque los 18 negocios historicos no lo muestren.
    estado: Mapped[EstadoNegocio] = mapped_column(
        Enum(EstadoNegocio, name="estado_negocio"), nullable=False, default=EstadoNegocio.ACTIVO
    )

    # --- Valorizacion (D-017) ---
    valor_negocio: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    moneda: Mapped[MonedaTipo | None] = mapped_column(
        Enum(MonedaTipo, name="moneda_tipo", create_type=False), nullable=True
    )
    fecha_valorizacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    uf_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    valor_clp_calculado: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    # Cuando existe, manda: en Mercado Primario y Assetplan el valor en pesos lo
    # determinan liquidaciones externas que no siguen la regla de la UF.
    valor_clp_manual: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    motivo_valor_manual: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Tasas de comision (entrada) ---
    # Los dos primeros son "que porcentaje paga cada lado de la operacion", y
    # su destino depende del modelo (ver app/services/comisiones.py):
    #   Primario      -> el lado vendedor (la inmobiliaria) paga la comision.
    #   Concentradores-> el lado comprador paga la comision; lo del lado
    #                    vendedor lo cobra el concentrador y solo sirve para
    #                    calcular el rebate del 12% que comparte con ViveProp.
    #   Agencia       -> pagan los dos lados y la comision es la suma.
    # Se evito nombrarlos por su destino porque cambia entre modelos: llamarle
    # "pct_comision_concentrador" a la columna AD seria falso en Primario.
    pct_lado_vendedor: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    pct_lado_comprador: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    pct_rebate_concentrador: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    pct_broker_vendedor: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    pct_broker_comprador: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    pct_vp_vendedor: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    pct_vp_comprador: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    # 10% en la practica, no el 30-40% de REGLAS CALCULO. Editable (D-019).
    pct_equipo: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    pct_tercero: Mapped[Decimal | None] = mapped_column(PCT, nullable=True)
    nombre_tercero: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # --- Montos (calculados al guardar y persistidos, no al leer) ---
    comision_total: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    comision_broker: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    rebate_concentrador: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    comision_vp_bruta: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    comision_equipo: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    comision_tercero: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    comision_real_vp: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)

    # --- Cierre (D-023: opcional, catalogo mas texto libre) ---
    motivo_perdida_id: Mapped[int | None] = mapped_column(ForeignKey("catalogos.id"), nullable=True)
    motivo_perdida_detalle: Mapped[str | None] = mapped_column(Text, nullable=True)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    negocio: Mapped["Negocio"] = relationship(back_populates="hitos")
    obligaciones: Mapped[list["Obligacion"]] = relationship(
        back_populates="hito", cascade="all, delete-orphan"
    )

    @property
    def base_comision(self) -> Decimal | None:
        """La base sobre la que se calcula todo (D-017).

        El manual manda cuando existe. El motor de comisiones del sprint 7
        trabaja siempre sobre esto, nunca sobre la conversion por UF directa.
        """
        if self.valor_clp_manual is not None:
            return self.valor_clp_manual
        return self.valor_clp_calculado
