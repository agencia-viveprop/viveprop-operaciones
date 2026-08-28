import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.usuario import utcnow


class CanjeEstado(str, enum.Enum):
    """En qué terminó el canje, o si sigue en curso.

    **`CERRADO` llegó tarde y por una necesidad concreta.** Durante todo el
    histórico solo existieron `ACTIVO` y `CANCELADO`, así que no había forma de
    registrar que un canje se concretó: los 31 que tienen la etapa en «Cierre»
    están cancelados --llegaron hasta la firma y se cayeron-- y por eso la métrica
    de canjes cerrados daba cero en los 46 meses y no podía dar otra cosa.

    Hace falta porque la comisión de Dataprop se cobra **por cada operación
    cerrada**, así que sin un estado que diga "cerró" no hay cuándo registrar lo
    que se cobró.

    **La etapa `CERRADO` y este estado son cosas distintas.** La etapa dice hasta
    dónde llegó el proceso; el estado, en qué terminó. Un canje puede llegar a la
    etapa de cierre y caerse igual, y eso es exactamente lo que pasó 31 veces.
    """

    ACTIVO = "ACTIVO"
    CERRADO = "CERRADO"
    CANCELADO = "CANCELADO"


class CanjeEtapa(str, enum.Enum):
    """Las cinco etapas del ciclo de un canje.

    **Hubo una sexta, `RECEPCION`, y ya no está** (`D-081`). Nació como
    `SIN_ETAPA` --describía que el export de Dataprop no traía etapa-- y la
    migración `b8f3a71c904e` la renombró razonando que «la etapa que corresponde a
    un canje que entró y no avanzó es Recepción». Eso fue el error: le puso nombre
    de etapa a una ausencia. Medido sobre producción, ningún canje pasaba tiempo
    en ella --los tramos daban 0 días-- y los 75 que la tenían estaban todos
    cancelados. Ahora un canje arranca en `EN_REVISION`, que es la primera etapa en
    la que alguien hace algo.

    El valor sigue existiendo en el tipo `canje_etapa` de Postgres, porque un enum
    no admite quitar valores. No hay ninguna fila que lo use.
    """

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


class CorredorCanje(str, enum.Enum):
    """Cuál de los dos corredores de un canje.

    Un canje siempre tiene dos: el que pide el intercambio y el que tiene la
    propiedad. Una gestión --una llamada, un WhatsApp-- se le hace a uno de los
    dos, y saber a cuál es lo que permite después separar quién no contesta.
    """

    SOLICITANTE = "SOLICITANTE"
    PROPIETARIO = "PROPIETARIO"


CORREDOR_LABELS = {
    CorredorCanje.SOLICITANTE: "Corredor solicitante",
    CorredorCanje.PROPIETARIO: "Corredor propietario",
}


# Los rótulos que se muestran. `CERRADO` se rotula «Cierre» --es el nombre de la
# etapa-- y se guarda como `CERRADO`: ese valor está escrito como texto en
# `movimientos.etapa_resultante`, así que renombrarlo pediría actualizar filas
# para ganar nada. Ver `b8f3a71c904e`.
ETAPA_LABELS = {
    CanjeEtapa.EN_REVISION: "En revisión",
    CanjeEtapa.PROCESO_DE_ACUERDO: "Proceso de acuerdo",
    CanjeEtapa.EN_OFERTA: "En oferta",
    CanjeEtapa.EN_NEGOCIO: "En negocio",
    CanjeEtapa.CERRADO: "Cierre",
}

# Lo mismo para la operación. "VENTA" es el valor guardado; "Venta" es lo que se
# lee. Vive acá y no en la pantalla porque el reporte lo manda ya redactado: un
# rótulo escrito en el frontend se despega del enum en cuanto el enum cambia.
OPERACION_LABELS = {
    OperacionTipo.VENTA: "Venta",
    OperacionTipo.ARRIENDO: "Arriendo",
    OperacionTipo.OTRO: "Otro",
}


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
    etapa: Mapped[CanjeEtapa] = mapped_column(Enum(CanjeEtapa, name="canje_etapa"), nullable=False, default=CanjeEtapa.EN_REVISION)

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
    # **La comisión real que Dataprop cobró al cerrar el canje**, no una
    # estimación. La estimada la calcula el motor a partir del valor de la
    # propiedad; ésta se negocia y se factura, así que es un dato que se registra.
    #
    # Vacía en las 303 filas: nunca se cerró un canje. Y la plata es de Dataprop,
    # no de ViveProp, que opera el programa a nombre de ella y no percibe nada.
    comision_dataprop: Mapped[float | None] = mapped_column(Numeric(16, 2), nullable=True)
    comision_dataprop_moneda: Mapped[MonedaTipo | None] = mapped_column(Enum(MonedaTipo, name="moneda_tipo"), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    gestionado_en_app: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
