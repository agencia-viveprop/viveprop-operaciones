import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.usuario import utcnow


class EntityType(str, enum.Enum):
    canje = "canje"
    negocio = "negocio"


class TipoMovimiento(Base):
    __tablename__ = "tipos_movimiento"

    codigo: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, name="entity_type"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    etapa_resultante: Mapped[str | None] = mapped_column(String(20), nullable=True)
    orden: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sla_horas: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    sla_es_habil: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    canal: Mapped[str | None] = mapped_column(String(30), nullable=True)
    responsable_default: Mapped[str | None] = mapped_column(String(60), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Movimiento(Base):
    __tablename__ = "movimientos"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, name="entity_type"), nullable=False)
    entity_id: Mapped[int] = mapped_column(nullable=False)
    tipo_movimiento: Mapped[str] = mapped_column(String(50), ForeignKey("tipos_movimiento.codigo"), nullable=False)
    etapa_resultante: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    autor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
