import enum

from sqlalchemy import JSON, Boolean, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TipoCatalogo(str, enum.Enum):
    """Los tipos de lista que viven en la tabla generica (D-021).

    Se guarda como varchar y no como enum de Postgres a proposito: agregar un
    catalogo nuevo no deberia requerir una migracion. Este enum existe para
    validar en la capa de servicio y para tipar el endpoint.
    """

    ALIANZA = "alianza"
    ESTADO_FACTURACION = "estado_facturacion"
    TIPO_PROPIEDAD = "tipo_propiedad"
    TIPO_OPERACION = "tipo_operacion"
    ESTADO_PROPIEDAD = "estado_propiedad"
    MOTIVO_PERDIDA = "motivo_perdida"
    # Los dominios de correo de la organización. Vive acá y no en una tabla
    # propia porque es exactamente lo que esta tabla resuelve --una lista corta,
    # editable, con `activo` y `orden`-- y así no cuesta una migración de esquema.
    #
    # A diferencia de los otros, **no sale en `GET /api/catalogos`**: lo sirve el
    # router de admin. No es secreto, pero tampoco le sirve a las pantallas que
    # consumen el catálogo general, y esa respuesta la lee cualquier usuario.
    DOMINIO_ORGANIZACION = "dominio_organizacion"


class ModeloNegocio(str, enum.Enum):
    """Enum, no catalogo (D-021).

    Cada modelo tiene una formula de comision distinta escrita en codigo: la de
    Concentradores (D-018) no se parece a la de Primario. Si esto fuera un
    catalogo editable, agregar un cuarto modelo desde un mantenedor dejaria al
    motor sin saber calcularlo, fallando en silencio. Siendo enum, agregar un
    modelo es un cambio de codigo con su test.

    El tipo de Postgres se crea en el sprint 6, junto con la tabla que lo usa.
    """

    MERCADO_PRIMARIO = "MERCADO_PRIMARIO"
    SECUNDARIO_CONCENTRADORES = "SECUNDARIO_CONCENTRADORES"
    SECUNDARIO_AGENCIA = "SECUNDARIO_AGENCIA"


class EstadoNegocio(str, enum.Enum):
    """Enum por el mismo criterio que ModeloNegocio: gobierna logica.

    De estos tres estados dependen los tres buckets de la reporteria (D-006):
    ganado, pipeline y comision potencial no concretada. `DESISTIDO` esta en
    CONFIG pero no aparece en ninguna de las 19 filas historicas.
    """

    ACTIVO = "ACTIVO"
    CERRADO = "CERRADO"
    PERDIDO = "PERDIDO"
    DESISTIDO = "DESISTIDO"


class ResponsableEtapa(str, enum.Enum):
    COMERCIAL = "COMERCIAL"
    HIBRIDO = "HIBRIDO"
    OPERACIONES = "OPERACIONES"


class Catalogo(Base):
    """Listas planas editables, en una sola tabla (D-021).

    Costo aceptado: sin claves foraneas por tipo, nada a nivel de base impide
    que un negocio apunte a un catalogo del tipo equivocado. La validacion vive
    en la capa de servicio.
    """

    __tablename__ = "catalogos"
    __table_args__ = (UniqueConstraint("tipo", "codigo", name="uq_catalogos_tipo_codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(40), nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    orden: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # JSONB en Postgres, JSON en SQLite: la variante permite crear la tabla en
    # la base de test sin renunciar al tipo nativo en produccion.
    metadatos: Mapped[dict | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=True
    )


class Etapa(Base):
    """Tabla propia y no catalogo generico (D-021).

    Tiene estructura real -- codigo, nombre, responsable, orden -- y la consulta
    el motor de pipeline del sprint 11, no solo un desplegable.
    """

    __tablename__ = "etapas"

    codigo: Mapped[str] = mapped_column(String(4), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    responsable: Mapped[ResponsableEtapa] = mapped_column(
        String(20), nullable=False
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
