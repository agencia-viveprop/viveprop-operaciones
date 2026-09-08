"""Tabla de visitas: la solicitud de visita a una propiedad, importada desde la
consola de administración.

No tiene un ID propio en el archivo de origen, así que no hay clave única más
allá del `id` interno: cada carga inserta filas nuevas y los duplicados se
sacan a mano desde la app.

Revision ID: b4e91f2a7c33
Revises: d7f14a83c26b
"""
from alembic import op
import sqlalchemy as sa

revision = "b4e91f2a7c33"
down_revision = "d7f14a83c26b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visitas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("propiedad", sa.Text(), nullable=False),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("tipo", sa.String(length=120), nullable=True),
        sa.Column("mercado", sa.String(length=120), nullable=True),
        sa.Column("cliente", sa.String(length=255), nullable=True),
        sa.Column("rut", sa.String(length=40), nullable=True),
        sa.Column("objetivo_compra", sa.String(length=255), nullable=True),
        sa.Column("fecha_solicitada", sa.DateTime(timezone=True), nullable=True),
        sa.Column("etapa", sa.String(length=120), nullable=True),
        sa.Column("solicitada_el", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("visitas")
