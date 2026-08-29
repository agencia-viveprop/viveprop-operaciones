"""Facturación y pago, parte por parte, para negocios y canjes.

**Una tabla para los dos dominios.** Una obligación cuelga de una *liquidación* de
negocio o de un *canje*, exactamente una de las dos, y la base lo exige con un
`CHECK`. Se usaron dos claves foráneas nulables en vez del `entity_type` +
`entity_id` de `movimientos`: acá el volumen es chico --114 filas hoy-- así que se
puede pagar el lujo de tener integridad referencial real de los dos lados, que es
lo que impide que quede una obligación apuntando a una liquidación borrada.

**El estado vigente se guarda y cada cambio deja un avance.** Es el mismo patrón
que el canje con su etapa: el estado actual está en la fila para poder consultarlo
sin recalcular, y la historia está en `obligacion_avances` para poder responder
*cuándo se facturó* y *quién lo registró*. El usuario lo pidió así: «un solo campo
de estado, pero que permita ir modificándolo y que quede registro de avance»
(`D-092`).

**La historia arranca cuando se empieza a usar.** Las 114 obligaciones que vinieron
del Excel traen su estado sin fecha ni monto --el archivo no los tenía-- así que no
tienen avances previos. El primero de cada una será el próximo cambio que alguien
registre.
"""
import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.usuario import utcnow

MONTO = Numeric(16, 2)


class TipoObligacion(str, enum.Enum):
    """Las partes que se facturan y se pagan, por dominio.

    Las seis primeras son las columnas de facturación y pago del Excel de
    negocios, verticalizadas. Las dos últimas son de canjes y salen de una regla
    distinta: **una factura por corredor**, porque en un canje Dataprop le cobra su
    comisión a cada uno de los dos corredores por separado.
    """

    # --- negocios
    PAGO_PARTNER_COMERCIAL = "PAGO_PARTNER_COMERCIAL"
    FACT_CORREDOR_VP = "FACT_CORREDOR_VP"
    FACT_CAPTADOR_ALIANZA = "FACT_CAPTADOR_ALIANZA"
    PAGO_EQUIPO_VP = "PAGO_EQUIPO_VP"
    FACT_COMISION_TOTAL = "FACT_COMISION_TOTAL"
    PAGO_COMISION_REAL_VP = "PAGO_COMISION_REAL_VP"
    # --- canjes
    FACT_CORREDOR_SOLICITANTE = "FACT_CORREDOR_SOLICITANTE"
    FACT_CORREDOR_PROPIETARIO = "FACT_CORREDOR_PROPIETARIO"


# Los rótulos que se muestran. Salen del Excel para que quien conocía la planilla
# reconozca la fila, y viven acá y no en la pantalla por la misma razón que los de
# etapa: escritos en el frontend se despegan del enum en cuanto el enum cambia.
OBLIGACION_LABELS = {
    TipoObligacion.FACT_COMISION_TOTAL: "Facturación comisión total",
    TipoObligacion.PAGO_PARTNER_COMERCIAL: "Pago partner comercial",
    TipoObligacion.FACT_CORREDOR_VP: "Facturación corredor ViveProp",
    TipoObligacion.FACT_CAPTADOR_ALIANZA: "Facturación captador alianza",
    TipoObligacion.PAGO_EQUIPO_VP: "Pago equipo ViveProp",
    TipoObligacion.PAGO_COMISION_REAL_VP: "Pago comisión real VP",
    TipoObligacion.FACT_CORREDOR_SOLICITANTE: "Facturación corredor solicitante",
    TipoObligacion.FACT_CORREDOR_PROPIETARIO: "Facturación corredor propietario",
}

# **En el orden en que ocurren**, que es el orden en que se leen en la pantalla.
# La comisión total va primera porque es el todo del que salen las demás.
TIPOS_DE_NEGOCIO = (
    TipoObligacion.FACT_COMISION_TOTAL,
    TipoObligacion.PAGO_PARTNER_COMERCIAL,
    TipoObligacion.FACT_CORREDOR_VP,
    TipoObligacion.FACT_CAPTADOR_ALIANZA,
    TipoObligacion.PAGO_EQUIPO_VP,
    TipoObligacion.PAGO_COMISION_REAL_VP,
)
TIPOS_DE_CANJE = (
    TipoObligacion.FACT_CORREDOR_SOLICITANTE,
    TipoObligacion.FACT_CORREDOR_PROPIETARIO,
)


class Obligacion(Base):
    """Una parte que hay que facturar o pagar, con su estado vigente.

    El estado se guarda explícito y no se deriva del estado del negocio, aunque en
    el histórico los 10 perdidos tengan «No Aplica - Negocio Caído» en las seis
    columnas: un negocio puede caerse **después** de que algo ya se facturó, y ahí
    la derivación mentiría.
    """

    __tablename__ = "obligaciones"
    __table_args__ = (
        # Exactamente uno de los dos dueños. Sin esto, una obligación podría
        # quedar colgando de nada o de los dos a la vez, y los dos casos dan
        # cifras mal en la vista de cobranza.
        CheckConstraint(
            "(hito_id IS NOT NULL AND canje_id IS NULL)"
            " OR (hito_id IS NULL AND canje_id IS NOT NULL)",
            name="ck_obligaciones_un_dueno",
        ),
        UniqueConstraint("hito_id", "tipo", name="uq_obligaciones_hito_tipo"),
        UniqueConstraint("canje_id", "tipo", name="uq_obligaciones_canje_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    hito_id: Mapped[int | None] = mapped_column(
        ForeignKey("negocio_hitos.id", ondelete="CASCADE"), nullable=True
    )
    # `BigInteger` porque el id del canje es el ID_CANJE de Dataprop y es bigint.
    canje_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("canjes.id", ondelete="CASCADE"), nullable=True
    )
    tipo: Mapped[TipoObligacion] = mapped_column(
        Enum(TipoObligacion, name="tipo_obligacion"), nullable=False
    )
    estado_id: Mapped[int | None] = mapped_column(ForeignKey("catalogos.id"), nullable=True)
    # El monto **registrado**, que puede diferir del que calcula el motor: se
    # factura lo que se factura, y un ajuste por acuerdo es un hecho y no un error.
    # La pantalla muestra los dos para que la diferencia se vea.
    monto: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    fecha: Mapped[date | None] = mapped_column(Date, nullable=True)

    hito: Mapped["object"] = relationship("NegocioHito", back_populates="obligaciones")
    canje: Mapped["object"] = relationship("Canje")
    avances: Mapped[list["ObligacionAvance"]] = relationship(
        back_populates="obligacion",
        cascade="all, delete-orphan",
        order_by="ObligacionAvance.id",
    )


class ObligacionAvance(Base):
    """Cada cambio de estado, con lo que se registró en ese momento.

    Guarda **monto y fecha propios** y no solo el estado: al facturar se registra
    el monto y la fecha de la factura, y al pagar los del pago. Si el avance
    guardara solo el estado, el segundo registro pisaría los datos del primero y
    «cuánto se facturó» se perdería.
    """

    __tablename__ = "obligacion_avances"

    id: Mapped[int] = mapped_column(primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(
        ForeignKey("obligaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estado_id: Mapped[int | None] = mapped_column(ForeignKey("catalogos.id"), nullable=True)
    monto: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    fecha: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Quién lo registró. `SET NULL` para que borrar una cuenta no borre la
    # historia de cobranza.
    autor_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    # Cuándo se registró, que no es lo mismo que la fecha de la factura o del pago:
    # es la distinción que ya existe entre `fecha` y `creado_en` en movimientos.
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    obligacion: Mapped["Obligacion"] = relationship(back_populates="avances")
