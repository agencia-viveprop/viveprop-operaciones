from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.usuario import utcnow


class UFDiaria(Base):
    """Serie diaria de la Unidad de Fomento.

    `fecha` es la clave primaria: hay exactamente un valor por dia y la serie no
    tiene huecos (verificado sobre los 17.937 dias del archivo original). Eso
    permite que la carga sea un upsert por fecha, y que subir meses solapados no
    duplique nada.

    La serie se carga a mano una vez al mes (ver D-007): la UF se publica del
    dia 10 al 9 del mes siguiente, asi que siempre hay ~30 dias de colchon.
    """

    __tablename__ = "uf_diaria"

    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    valor: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
