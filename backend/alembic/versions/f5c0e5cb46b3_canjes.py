"""canjes

Revision ID: f5c0e5cb46b3
Revises: 46ec5627fa9a
Create Date: 2026-08-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f5c0e5cb46b3"
down_revision = "46ec5627fa9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Los 4 tipos ENUM se crean automaticamente por SQLAlchemy al usarse
    # en las columnas de abajo (moneda_tipo se reutiliza en 3 columnas,
    # SQLAlchemy lo detecta y emite el CREATE TYPE una sola vez).
    canje_estado = postgresql.ENUM("ACTIVO", "CANCELADO", name="canje_estado")
    canje_etapa = postgresql.ENUM(
        "SIN_ETAPA", "EN_REVISION", "PROCESO_DE_ACUERDO", "EN_OFERTA", "EN_NEGOCIO", "CERRADO", name="canje_etapa"
    )
    operacion_tipo = postgresql.ENUM("VENTA", "ARRIENDO", "OTRO", name="operacion_tipo")
    moneda_tipo = postgresql.ENUM("CLP", "UF", "OTRA", name="moneda_tipo")

    op.create_table(
        "canjes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("fecha_solicitud", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_cierre", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", canje_estado, nullable=False, server_default="ACTIVO"),
        sa.Column("etapa", canje_etapa, nullable=False, server_default="SIN_ETAPA"),
        sa.Column("corredor_solicitante_nombre", sa.String(255), nullable=True),
        sa.Column("corredor_solicitante_email", sa.String(255), nullable=True),
        sa.Column("corredor_propietario_nombre", sa.String(255), nullable=True),
        sa.Column("corredor_propietario_email", sa.String(255), nullable=True),
        sa.Column("tipo_operacion", operacion_tipo, nullable=True),
        sa.Column("tipo_inmueble", sa.String(120), nullable=True),
        sa.Column("comuna", sa.String(120), nullable=True),
        sa.Column("direccion", sa.Text(), nullable=True),
        sa.Column("valor_prop", sa.Numeric(16, 2), nullable=True),
        sa.Column("moneda_valor", moneda_tipo, nullable=True),
        sa.Column("link_propiedad", sa.Text(), nullable=True),
        sa.Column("valor_negocio", sa.Numeric(16, 2), nullable=True),
        sa.Column("valor_negocio_moneda", moneda_tipo, nullable=True),
        sa.Column("comision_dbrokers", sa.Numeric(16, 2), nullable=True),
        sa.Column("comision_dbrokers_moneda", moneda_tipo, nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("gestionado_en_app", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_canjes_estado_etapa", "canjes", ["estado", "etapa"])
    op.create_index("idx_canjes_fecha", "canjes", ["fecha_solicitud"])


def downgrade() -> None:
    op.drop_index("idx_canjes_fecha", table_name="canjes")
    op.drop_index("idx_canjes_estado_etapa", table_name="canjes")
    op.drop_table("canjes")
    bind = op.get_bind()
    postgresql.ENUM(name="moneda_tipo").drop(bind, checkfirst=True)
    postgresql.ENUM(name="operacion_tipo").drop(bind, checkfirst=True)
    postgresql.ENUM(name="canje_etapa").drop(bind, checkfirst=True)
    postgresql.ENUM(name="canje_estado").drop(bind, checkfirst=True)
