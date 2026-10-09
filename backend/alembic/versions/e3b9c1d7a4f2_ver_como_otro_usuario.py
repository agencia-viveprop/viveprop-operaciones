"""Un admin puede ver la app como otro usuario (`D-120`).

`sesiones.viendo_como_id` guarda a quién está viendo el admin desde su propia
sesión, y `vistas_como` deja el registro de cada vista: qué admin, a quién,
cuándo empezó y cuándo terminó.

Revision ID: e3b9c1d7a4f2
Revises: d4f7a2c8e6b1
"""
from alembic import op
import sqlalchemy as sa

revision = "e3b9c1d7a4f2"
down_revision = "d4f7a2c8e6b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sesiones", sa.Column("viendo_como_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sesiones_viendo_como_id",
        "sesiones",
        "usuarios",
        ["viendo_como_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_table(
        "vistas_como",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sesion_id", sa.Uuid(), nullable=True),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("vistas_como")
    op.drop_constraint("fk_sesiones_viendo_como_id", "sesiones", type_="foreignkey")
    op.drop_column("sesiones", "viendo_como_id")
