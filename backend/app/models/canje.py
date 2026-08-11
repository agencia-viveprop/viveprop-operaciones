import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.usuario import utcnow


class CanjeEstado(str, enum.Enum):
    ACTIVO = "ACTIVO"
    CANCELADO = "CANCELADO"


class CanjeEtapa(str, enum.Enum):
    SIN_ETAPA = "SIN_ETAPA"
    EN_REVISION = "EN_REVISION"
    PROCESO_DE_ACUERDO = "PROCESO_DE_ACUERDO"
    EN_OFERTA = "EN_OFERTA"
    EN_NEGOCIO = "EN_NEGOCIO"
    CERRADO = "CERRADO"


class OperacionTipo(str, enum.Enum):
    VENTA = "VENTA"
    ARRIENDO = "ARRIENDO"
    OTRO = "OTRO"


class MonedaTipo(str, enum.Enum):
    CLP = "CLP"
    UF = "UF"
    OTRA = "OTRA"


class Canje(Base):
    __tablename__ = "canjes"

    # Mismo ID_CANJE que trae la query de Dataprop -- no es autoincremental,
    # es la clave de matching de la futura importacion (Sprint B2).
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)

    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    estado: Mapped[CanjeEstado] = mapped_column(Enum(CanjeEstado, name="canje_estado"), nullable=False, default=CanjeEstado.ACTIVO)
    etapa: Mapped[CanjeEtapa] = mapped_column(Enum(CanjeEtapa, name="canje_etapa"), nullable=False, default=CanjeEtapa.SIN_ETAPA)

    corredor_solicitante_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    corredor_solicitante_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    corredor_propietario_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    corredor_propietario_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tipo_operacion: Mapped[OperacionTipo | None] = mapped_column(Enum(OperacionTipo, name="operacion_tipo"), nullable=True)
    tipo_inmueble: Mapped[str | None] = mapped_column(String(120), nullable=True)
    comuna: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)

    valor_prop: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    moneda_valor: Mapped[MonedaTipo | None] = mapped_column(Enum(MonedaTipo, name="moneda_tipo"), nullable=True)
    link_propiedad: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Campos que Dataprop no provee -- solo se completan a mano en la app.
    valor_negocio: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    valor_negocio_moneda: Mapped[MonedaTipo | None] = mapped_column(Enum(MonedaTipo, name="moneda_tipo"), nullable=True)
    comision_dbrokers: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    comision_dbrokers_moneda: Mapped[MonedaTipo | None] = mapped_column(Enum(MonedaTipo, name="moneda_tipo"), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    gestionado_en_app: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
