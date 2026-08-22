"""Agrega usuarios.debe_cambiar_password

Revision ID: c9d3e8a41f57
Revises: b7c2f4a19d83
Create Date: 2026-08-21

El flag que sostiene el reset de contraseña: un admin resetea la clave de alguien,
esa persona entra con la temporal y **no puede hacer nada** hasta cambiarla.

Arranca en `false` para todos los que ya existen. Nadie tiene que cambiar nada
por el solo hecho de que aparezca la columna.
"""
from alembic import op
import sqlalchemy as sa

revision = "c9d3e8a41f57"
down_revision = "b7c2f4a19d83"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "debe_cambiar_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "debe_cambiar_password")
