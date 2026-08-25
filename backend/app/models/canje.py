import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.usuario import utcnow


class CanjeEstado(str, enum.Enum):
    ACTIVO = "ACTIVO"
    CANCELADO = "CANCELADO"


class CanjeEtapa(str, enum.Enum):
    # Un canje que entró y no avanzó. Se llamaba `SIN_ETAPA` --que describía la
    # ausencia de dato en el export de Dataprop, no un estado del negocio-- y la
    # migración `b8f3a71c904e` lo renombró.
    RECEPCION = "RECEPCION"
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
    # Los indices se declaran aca porque los creo la migracion `f5c0e5cb46b3` y
    # el modelo no los conocia: `autogenerate` los veia como sobrantes y proponia
    # borrarlos. Un `drop_index` sobre produccion degrada la bandeja en silencio.
    __table_args__ = (
        Index("idx_canjes_estado_etapa", "estado", "etapa"),
        Index("idx_canjes_fecha", "fecha_solicitud"),
    )

    # Mismo ID_CANJE que trae la query de Dataprop -- no es autoincremental,
    # es la clave de matching de la futura importacion (Sprint B2).
    # `BigInteger` explicito: la migracion creo `bigint` y sin declararlo aca el
    # modelo dice `Integer`. Ese desajuste hacia que `alembic revision
    # --autogenerate` emitiera un `modify_type` que angostaria la columna en
    # produccion.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    estado: Mapped[CanjeEstado] = mapped_column(Enum(CanjeEstado, name="canje_estado"), nullable=False, default=CanjeEstado.ACTIVO)
    etapa: Mapped[CanjeEtapa] = mapped_column(Enum(CanjeEtapa, name="canje_etapa"), nullable=False, default=CanjeEtapa.RECEPCION)

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
