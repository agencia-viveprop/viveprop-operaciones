from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.usuario import utcnow


class Visita(Base):
    """Una solicitud de visita a una propiedad, tal como sale de la consola.

    No tiene un ID propio en el archivo de origen --a diferencia de los canjes,
    que traen `ID_CANJE`-- así que cada carga inserta todas las filas como
    registros nuevos, sin buscar existentes. Si el mismo archivo se sube dos
    veces, las filas quedan duplicadas y se sacan a mano, una por una.
    """

    __tablename__ = "visitas"

    id: Mapped[int] = mapped_column(primary_key=True)
    propiedad: Mapped[str] = mapped_column(Text, nullable=False)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    mercado: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cliente: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Se guarda tal cual viene del Excel, sin validar formato: el origen trae
    # RUTs incompletos ("1111") y no es objetivo de este módulo corregirlos.
    rut: Mapped[str | None] = mapped_column(String(40), nullable=True)
    objetivo_compra: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fecha_solicitada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    etapa: Mapped[str | None] = mapped_column(String(120), nullable=True)
    corredor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    solicitada_el: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
