"""Teléfonos de los dos corredores y código de propiedad, en canjes.

Dataprop agregó estas tres columnas a su export: TELEFONO_CORREDOR_SOLICITANTE,
TELEFONO_CORREDOR_PROPIETARIO y CODIGO_PROPIEDAD. El código de propiedad es el
de Dataprop, distinto del `id` del canje (que es el de la solicitud).

Revision ID: d4f7a2c8e6b1
Revises: c8a2e5f9b1d4
"""
from alembic import op
import sqlalchemy as sa

revision = "d4f7a2c8e6b1"
down_revision = "c8a2e5f9b1d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("canjes", sa.Column("corredor_solicitante_telefono", sa.String(length=50), nullable=True))
    op.add_column("canjes", sa.Column("corredor_propietario_telefono", sa.String(length=50), nullable=True))
    op.add_column("canjes", sa.Column("codigo_propiedad", sa.String(length=60), nullable=True))


def downgrade() -> None:
    op.drop_column("canjes", "codigo_propiedad")
    op.drop_column("canjes", "corredor_propietario_telefono")
    op.drop_column("canjes", "corredor_solicitante_telefono")
