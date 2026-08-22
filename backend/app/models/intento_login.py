from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.usuario import utcnow


class IntentoLogin(Base):
    """Un contador de fallos por clave, para frenar la fuerza bruta.

    La clave es genérica --`email:felipe@viveprop.com` o `ip:1.2.3.4`-- porque se
    cuentan dos cosas distintas con el mismo mecanismo: por email se protege la
    cuenta, por IP se protege el servidor.

    La fila se borra cuando alguien entra bien, y la limpieza periódica saca las
    que quedaron sin actividad. No es un registro de auditoría: es un contador con
    fecha de vencimiento.
    """

    __tablename__ = "intentos_login"

    clave: Mapped[str] = mapped_column(String(320), primary_key=True)
    fallidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Nulo mientras no se haya alcanzado el umbral.
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
