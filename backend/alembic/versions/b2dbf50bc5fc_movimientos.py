"""movimientos y catalogo de tipos_movimiento (seed Canjes)

Revision ID: b2dbf50bc5fc
Revises: f5c0e5cb46b3
Create Date: 2026-08-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b2dbf50bc5fc"
down_revision = "f5c0e5cb46b3"
branch_labels = None
depends_on = None

# codigo, nombre, etapa_resultante, orden, sla_horas, sla_es_habil, canal, responsable_default
CATALOGO_CANJES = [
    ("GESTION_INICIAL", "Gestión inicial", "EN_REVISION", 1, 24, False, "Admin DataProp", "Operaciones"),
    ("WA_CONFIRM_SOLICITANTE", "WA confirmación solicitante", None, 2, 2, True, "WhatsApp", "Operaciones"),
    ("WA_CONFIRM_PROPIETARIO", "WA confirmación propietario", None, 3, 2, True, "WhatsApp", "Operaciones"),
    ("EMAIL_REGISTRO_PROPIETARIO", "Email registro propietario", None, 4, 3, False, "Email", "Operaciones"),
    ("INSISTENCIA_PROPIETARIO", "Insistencia propietario", None, 5, 24, True, "WA / Llamada / Email", "Operaciones"),
    ("VALIDACION_SOLICITANTE", "Validación solicitante", None, 6, 24, False, "Teléfono", "Operaciones"),
    ("VALIDACION_PROPIETARIO", "Validación propietario", None, 7, 24, False, "Teléfono", "Operaciones"),
    ("MANDATO_FIRMADO", "Mandato firmado", None, 8, None, False, "Plataforma", "Operaciones"),
    ("ACUERDO_FIRMADO", "Acuerdo de canje firmado", "PROCESO_DE_ACUERDO", 9, 24, False, "Plataforma", "Corredores + Operaciones"),
    ("OFERTA_ENVIADA", "Oferta enviada", "EN_OFERTA", 10, None, False, "Plataforma", "Operaciones"),
    ("NEGOCIACION", "Negociación", "EN_NEGOCIO", 11, None, False, "Plataforma", "Operaciones"),
    ("CIERRE", "Cierre", "CERRADO", 12, 24, False, "Admin DataProp", "Operaciones"),
    ("CANCELACION", "Cancelación", None, 13, None, False, None, None),
    ("COMENTARIO_GENERAL", "Comentario general", None, 14, None, False, None, None),
]


def upgrade() -> None:
    entity_type = postgresql.ENUM("canje", "negocio", name="entity_type")

    op.create_table(
        "tipos_movimiento",
        sa.Column("codigo", sa.String(50), primary_key=True),
        sa.Column("entity_type", entity_type, nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("etapa_resultante", sa.String(20), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=True),
        sa.Column("sla_horas", sa.Numeric(6, 2), nullable=True),
        sa.Column("sla_es_habil", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("canal", sa.String(30), nullable=True),
        sa.Column("responsable_default", sa.String(60), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "movimientos",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("entity_type", entity_type, nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("tipo_movimiento", sa.String(50), sa.ForeignKey("tipos_movimiento.codigo"), nullable=False),
        sa.Column("etapa_resultante", sa.String(20), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("autor_id", sa.BigInteger(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_movimientos_entity", "movimientos", ["entity_type", "entity_id", "fecha"])

    tabla = sa.table(
        "tipos_movimiento",
        sa.column("codigo", sa.String),
        sa.column("entity_type", sa.String),
        sa.column("nombre", sa.String),
        sa.column("etapa_resultante", sa.String),
        sa.column("orden", sa.Integer),
        sa.column("sla_horas", sa.Numeric),
        sa.column("sla_es_habil", sa.Boolean),
        sa.column("canal", sa.String),
        sa.column("responsable_default", sa.String),
    )
    op.bulk_insert(
        tabla,
        [
            {
                "codigo": c[0], "entity_type": "canje", "nombre": c[1], "etapa_resultante": c[2],
                "orden": c[3], "sla_horas": c[4], "sla_es_habil": c[5], "canal": c[6], "responsable_default": c[7],
            }
            for c in CATALOGO_CANJES
        ],
    )


def downgrade() -> None:
    op.drop_index("idx_movimientos_entity", table_name="movimientos")
    op.drop_table("movimientos")
    op.drop_table("tipos_movimiento")
    postgresql.ENUM(name="entity_type").drop(op.get_bind(), checkfirst=True)
