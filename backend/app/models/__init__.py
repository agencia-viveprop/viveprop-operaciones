# Los modelos de SQLAlchemy se registran aquí a medida que se agregan
# para que Alembic los detecte via Base.metadata en autogenerate.
from app.models.usuario import Sesion, Usuario  # noqa: F401
