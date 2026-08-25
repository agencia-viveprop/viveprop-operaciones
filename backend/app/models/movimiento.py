import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
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
    # Creado por la migracion `b2dbf50bc5fc`. Sin declararlo, `autogenerate`
    # propondria borrarlo, y es el indice que sostiene la linea de tiempo.
    __table_args__ = (
        Index("idx_movimientos_entity", "entity_type", "entity_id", "fecha"),
        # Creado por `a7e4c92f18b3`. Sostiene la consulta de la bandeja, que
        # busca el seguimiento pendiente de cada canje.
        Index("idx_movimientos_proximo_seguimiento", "entity_type", "proximo_seguimiento"),
    )

    # `BigInteger` con variante `Integer` para SQLite: en Postgres es `bigint`,
    # como lo creo la migracion, y en SQLite un `INTEGER PRIMARY KEY`, que es el
    # unico tipo que hace de alias de rowid y autoincrementa. Sin la variante los
    # tests fallan con "NOT NULL constraint failed" al insertar sin id.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True
    )
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType, name="entity_type"), nullable=False)
    # `bigint` en la base. Sin declararlo, `autogenerate` propondria angostarlo.
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo_movimiento: Mapped[str] = mapped_column(String(50), ForeignKey("tipos_movimiento.codigo"), nullable=False)
    etapa_resultante: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    autor_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("usuarios.id"), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Cuándo hay que volver a mirar esto. El compromiso lo asume el movimiento
    # --"llamé y quedamos en que sigo el jueves"-- así que vive acá y no en la
    # ficha del canje: puesto allá se sobreescribiría sin dejar rastro de quién lo
    # movió. El vigente es el del movimiento más reciente, igual que la etapa.
    proximo_seguimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Sobre cuál de los dos corredores se hizo la gestión. Solo aplica a canjes
    # --un negocio no tiene solicitante ni propietario-- y por eso va como texto
    # y no como tipo enumerado, igual que `etapa_resultante`: la tabla es
    # polimórfica y un valor de un dominio no debería imponerle un tipo a la
    # columna que comparten. Nulo en los 605 migrados: el Excel no lo traía.
    corredor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
