import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Uuid, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RolUsuario(str, enum.Enum):
    gerencia = "gerencia"
    operaciones = "operaciones"
    admin = "admin"


# Orden de la jerarquía de permisos: gerencia < operaciones < admin
JERARQUIA_ROLES = {RolUsuario.gerencia: 0, RolUsuario.operaciones: 1, RolUsuario.admin: 2}


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, name="user_role"), nullable=False, default=RolUsuario.operaciones
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Lo pone un reset de clave y lo limpia el cambio. Mientras este en true, la
    # sesion existe pero no sirve para nada mas que cambiar la contrasena.
    debe_cambiar_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sesiones: Mapped[list["Sesion"]] = relationship(back_populates="usuario", cascade="all, delete-orphan")


class Sesion(Base):
    __tablename__ = "sesiones"

    # `sa.Uuid` en vez del `UUID` del dialecto de Postgres: en Postgres emite el
    # mismo tipo nativo, y en SQLite un CHAR(32) con la conversion incluida. Eso
    # es lo que permite crear esta tabla en los tests y probar la cadena de
    # autenticacion completa -- cookie, sesion y guarda de cambio forzado -- que
    # antes quedaba sin cubrir. No cambia el DDL en produccion.
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)

    usuario: Mapped["Usuario"] = relationship(back_populates="sesiones")
