"""Columna corredor en visitas.

El archivo de la consola trae una columna con el corredor a cargo de la
solicitud, entre "Etapa" y "Solicitada el". Texto libre, igual que el resto de
las columnas del archivo: no hay un catálogo de corredores para esta tabla.

Revision ID: c8a2e5f9b1d4
Revises: b4e91f2a7c33
"""
from alembic import op
import sqlalchemy as sa

revision = "c8a2e5f9b1d4"
down_revision = "b4e91f2a7c33"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("visitas", sa.Column("corredor", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("visitas", "corredor")
