"""propiedades, negocios, negocio_hitos y negocio_obligaciones

Revision ID: d3a91f6c25b8
Revises: c8f2b41d7e05
Create Date: 2026-08-21

Especificacion en diseno_modelo_datos.md (D0), aprobada. Dos tablas para el
negocio y sus hitos (D-020) en vez de padre_id autorreferencial.

Nota sobre los enums: `modelo_negocio`, `estado_negocio` y `tipo_obligacion` se
crean aca. `moneda_tipo` ya existe desde la migracion de canjes, asi que se
referencia con create_type=False para no intentar crearlo de nuevo.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d3a91f6c25b8"
down_revision = "c8f2b41d7e05"
branch_labels = None
depends_on = None

PCT = sa.Numeric(16, 14)
MONTO = sa.Numeric(16, 2)

moneda_existente = postgresql.ENUM(
    "CLP", "UF", "OTRA", name="moneda_tipo", create_type=False
)


def upgrade() -> None:
    op.create_table(
        "propiedades",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("direccion", sa.Text(), nullable=False),
        sa.Column("unidad", sa.String(40), nullable=True),
        sa.Column("comuna", sa.String(120), nullable=False),
        sa.Column("tipo_propiedad_id", sa.Integer(), nullable=True),
        sa.Column("estado_propiedad_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tipo_propiedad_id"], ["catalogos.id"]),
        sa.ForeignKeyConstraint(["estado_propiedad_id"], ["catalogos.id"]),
        sa.UniqueConstraint("direccion", "unidad", "comuna", name="uq_propiedades_direccion_unidad_comuna"),
    )

    op.create_table(
        "negocios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("propiedad_id", sa.Integer(), nullable=False),
        sa.Column(
            "modelo",
            sa.Enum(
                "MERCADO_PRIMARIO", "SECUNDARIO_CONCENTRADORES", "SECUNDARIO_AGENCIA",
                name="modelo_negocio",
            ),
            nullable=False,
        ),
        sa.Column("alianza_id", sa.Integer(), nullable=True),
        sa.Column("tipo_operacion_id", sa.Integer(), nullable=True),
        sa.Column("vendedor_arrendador", sa.Text(), nullable=True),
        sa.Column("comprador_arrendatario", sa.Text(), nullable=True),
        sa.Column("corredor_agente", sa.Text(), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo", name="uq_negocios_codigo"),
        sa.ForeignKeyConstraint(["propiedad_id"], ["propiedades.id"]),
        sa.ForeignKeyConstraint(["alianza_id"], ["catalogos.id"]),
        sa.ForeignKeyConstraint(["tipo_operacion_id"], ["catalogos.id"]),
    )
    op.create_index("ix_negocios_modelo_alianza", "negocios", ["modelo", "alianza_id"])

    op.create_table(
        "negocio_hitos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("negocio_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(60), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_cierre", sa.Date(), nullable=True),
        sa.Column(
            "estado",
            sa.Enum("ACTIVO", "CERRADO", "PERDIDO", "DESISTIDO", name="estado_negocio"),
            nullable=False,
        ),
        sa.Column("etapa", sa.String(4), nullable=True),
        # Valorizacion (D-017)
        sa.Column("valor_negocio", MONTO, nullable=True),
        sa.Column("moneda", moneda_existente, nullable=True),
        sa.Column("fecha_valorizacion", sa.Date(), nullable=True),
        sa.Column("uf_snapshot", sa.Numeric(12, 2), nullable=True),
        sa.Column("valor_clp_calculado", MONTO, nullable=True),
        sa.Column("valor_clp_manual", MONTO, nullable=True),
        sa.Column("motivo_valor_manual", sa.Text(), nullable=True),
        # Tasas (D-018)
        sa.Column("pct_lado_vendedor", PCT, nullable=True),
        sa.Column("pct_lado_comprador", PCT, nullable=True),
        sa.Column("pct_rebate_concentrador", PCT, nullable=True),
        sa.Column("pct_broker_vendedor", PCT, nullable=True),
        sa.Column("pct_broker_comprador", PCT, nullable=True),
        sa.Column("pct_vp_vendedor", PCT, nullable=True),
        sa.Column("pct_vp_comprador", PCT, nullable=True),
        sa.Column("pct_equipo", PCT, nullable=True),
        sa.Column("pct_tercero", PCT, nullable=True),
        sa.Column("nombre_tercero", sa.String(255), nullable=True),
        # Montos calculados
        sa.Column("comision_total", MONTO, nullable=True),
        sa.Column("comision_broker", MONTO, nullable=True),
        sa.Column("rebate_concentrador", MONTO, nullable=True),
        sa.Column("comision_vp_bruta", MONTO, nullable=True),
        sa.Column("comision_equipo", MONTO, nullable=True),
        sa.Column("comision_tercero", MONTO, nullable=True),
        sa.Column("comision_real_vp", MONTO, nullable=True),
        # Cierre (D-023)
        sa.Column("motivo_perdida_id", sa.Integer(), nullable=True),
        sa.Column("motivo_perdida_detalle", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["negocio_id"], ["negocios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["etapa"], ["etapas.codigo"]),
        sa.ForeignKeyConstraint(["motivo_perdida_id"], ["catalogos.id"]),
    )
    op.create_index("ix_negocio_hitos_negocio", "negocio_hitos", ["negocio_id"])
    op.create_index("ix_negocio_hitos_estado_cierre", "negocio_hitos", ["estado", "fecha_cierre"])
    op.create_index("ix_negocio_hitos_fecha_cierre", "negocio_hitos", ["fecha_cierre"])

    op.create_table(
        "negocio_obligaciones",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hito_id", sa.Integer(), nullable=False),
        sa.Column(
            "tipo",
            sa.Enum(
                "PAGO_PARTNER_COMERCIAL", "FACT_CORREDOR_VP", "FACT_CAPTADOR_ALIANZA",
                "PAGO_EQUIPO_VP", "FACT_COMISION_TOTAL", "PAGO_COMISION_REAL_VP",
                name="tipo_obligacion",
            ),
            nullable=False,
        ),
        sa.Column("estado_id", sa.Integer(), nullable=True),
        sa.Column("monto", MONTO, nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["hito_id"], ["negocio_hitos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["estado_id"], ["catalogos.id"]),
        sa.UniqueConstraint("hito_id", "tipo", name="uq_negocio_obligaciones_hito_tipo"),
    )


def downgrade() -> None:
    op.drop_table("negocio_obligaciones")
    op.drop_index("ix_negocio_hitos_fecha_cierre", table_name="negocio_hitos")
    op.drop_index("ix_negocio_hitos_estado_cierre", table_name="negocio_hitos")
    op.drop_index("ix_negocio_hitos_negocio", table_name="negocio_hitos")
    op.drop_table("negocio_hitos")
    op.drop_index("ix_negocios_modelo_alianza", table_name="negocios")
    op.drop_table("negocios")
    op.drop_table("propiedades")
    # moneda_tipo NO se borra: es de canjes y sigue en uso.
    sa.Enum(name="tipo_obligacion").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estado_negocio").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="modelo_negocio").drop(op.get_bind(), checkfirst=True)
