"""usuarios y sesiones

Revision ID: 46ec5627fa9a
Revises:
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "46ec5627fa9a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # El tipo ENUM se crea automaticamente por SQLAlchemy al usarse en la columna "rol" de abajo.
    user_role = postgresql.ENUM("gerencia", "operaciones", "admin", name="user_role")

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol", user_role, nullable=False, server_default="operaciones"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ultimo_login", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "sesiones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
    )
    op.create_index("ix_sesiones_usuario_id", "sesiones", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_sesiones_usuario_id", table_name="sesiones")
    op.drop_table("sesiones")
    op.drop_table("usuarios")
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)
