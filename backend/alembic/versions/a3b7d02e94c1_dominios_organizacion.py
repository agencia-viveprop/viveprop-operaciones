"""Dominios de la organización administrables, y el rastro del acceso externo.

Dos cosas, que son la misma decisión (`D-078`):

1. Las dos columnas que registran **quién autorizó** un correo de fuera de la
   organización y **cuándo**. Nulas en los usuarios que ya existen, que es
   correcto: todos tienen correo `@viveprop.com`, así que nadie tuvo que
   autorizarlos.
2. Los dos dominios iniciales en la tabla de catálogos. Antes la lista vivía en
   la variable de entorno `DOMINIOS_EMAIL`, que ya no existe: con la lista en la
   base, un admin la administra desde la app sin entrar a Render.

La siembra usa `ON CONFLICT DO NOTHING` para que correrla dos veces --o sobre una
base donde alguien ya agregó los dominios a mano-- no falle.

Revision ID: a3b7d02e94c1
Revises: f7a2c95e13d8
"""
from alembic import op
import sqlalchemy as sa

revision = "a3b7d02e94c1"
down_revision = "f7a2c95e13d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("externo_autorizado_por_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "usuarios",
        sa.Column("externo_autorizado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_usuarios_externo_autorizado_por",
        "usuarios",
        "usuarios",
        ["externo_autorizado_por_id"],
        ["id"],
        # Si se borra la cuenta del admin que autorizó, el usuario externo no
        # puede desaparecer con ella.
        ondelete="SET NULL",
    )

    op.execute(
        """
        INSERT INTO catalogos (tipo, codigo, nombre, orden, activo)
        VALUES
            ('dominio_organizacion', 'viveprop.com', 'ViveProp', 1, true),
            ('dominio_organizacion', 'dataprop.cl', 'Dataprop', 2, true)
        ON CONFLICT (tipo, codigo) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM catalogos WHERE tipo = 'dominio_organizacion'")
    op.drop_constraint("fk_usuarios_externo_autorizado_por", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "externo_autorizado_en")
    op.drop_column("usuarios", "externo_autorizado_por_id")
