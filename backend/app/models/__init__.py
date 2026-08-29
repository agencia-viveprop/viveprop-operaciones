# Los modelos de SQLAlchemy se registran aquí a medida que se agregan
# para que Alembic los detecte via Base.metadata en autogenerate.
from app.models.usuario import Sesion, Usuario  # noqa: F401
from app.models.intento_login import IntentoLogin  # noqa: F401
from app.models.canje import Canje  # noqa: F401
from app.models.movimiento import Movimiento, TipoMovimiento  # noqa: F401
from app.models.uf import UFDiaria  # noqa: F401
from app.models.catalogo import Catalogo, Etapa  # noqa: F401
from app.models.negocio import (  # noqa: F401
    Negocio,
    NegocioHito,
    Propiedad,
)
from app.models.obligacion import (  # noqa: F401
    Obligacion,
    ObligacionAvance,
    TipoObligacion,
)
