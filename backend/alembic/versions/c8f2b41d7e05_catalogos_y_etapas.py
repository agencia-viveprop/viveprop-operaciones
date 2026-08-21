"""catalogos y etapas, con seed desde la hoja CONFIG

Revision ID: c8f2b41d7e05
Revises: a1c4e7d92b30
Create Date: 2026-08-21

El seed va en la migracion, siguiendo la convencion de b2dbf50bc5fc, que sembro
tipos_movimiento igual. Son listas de negocio que la app necesita para arrancar,
no datos de prueba.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "c8f2b41d7e05"
down_revision = "a1c4e7d92b30"
branch_labels = None
depends_on = None


# codigo, nombre, responsable, orden
ETAPAS = [
    ("E1", "Calificación del cliente", "COMERCIAL", 1),
    ("E2", "Visita y manifestación de interés", "COMERCIAL", 2),
    ("E3", "Negociación, reserva y promesa", "HIBRIDO", 3),
    ("E4", "Documentación / EETT / Tasación", "OPERACIONES", 4),
    ("E5", "Escritura / Contrato / firma final", "OPERACIONES", 5),
    ("E6", "Entrega y distribución de pagos", "OPERACIONES", 6),
    ("E7", "Terminado", "OPERACIONES", 7),
]

# tipo, codigo, nombre, orden, metadatos
CATALOGOS = [
    # Alianzas. El metadato guarda el modelo de negocio con el que opera cada
    # una -- en CONFIG la columna dice "Primario" y el modelo se llama
    # "Mercado Primario"; aqui se normaliza al codigo del enum.
    ("alianza", "ASSETPLAN", "Assetplan", 1, {"modelo": "SECUNDARIO_CONCENTRADORES"}),
    ("alianza", "INGEVEC", "Ingevec", 2, {"modelo": "MERCADO_PRIMARIO"}),
    ("alianza", "TOCTOC", "TocToc", 3, {"modelo": "MERCADO_PRIMARIO"}),
    ("alianza", "URMENETA", "Urmeneta", 4, {"modelo": "MERCADO_PRIMARIO"}),
    ("alianza", "MAESTRA", "Maestra", 5, {"modelo": "MERCADO_PRIMARIO"}),
    ("alianza", "EURO", "Euro", 6, {"modelo": "MERCADO_PRIMARIO"}),
    ("alianza", "NORTE_VERDE", "Norte Verde", 7, {"modelo": "MERCADO_PRIMARIO"}),
    ("alianza", "VIVEPROP", "Viveprop", 8, {"modelo": "SECUNDARIO_AGENCIA"}),
    # Estados de facturacion y pago. Son 11, en el orden de avance del ciclo:
    # los tres "No Aplica" primero, despues el ciclo real.
    ("estado_facturacion", "NO_APLICA_ETAPA", "No Aplica por Etapa", 1, None),
    ("estado_facturacion", "NO_APLICA_CAPTADOR", "No Aplica Captador", 2, None),
    ("estado_facturacion", "NO_APLICA_CAIDO", "No Aplica - Negocio Caído", 3, None),
    ("estado_facturacion", "INICIADO", "Iniciado", 4, None),
    ("estado_facturacion", "EN_PROCESO_CIERRE", "En proceso de cierre", 5, None),
    ("estado_facturacion", "PENDIENTE", "Pendiente", 6, None),
    ("estado_facturacion", "POR_LIQUIDAR", "Por Liquidar", 7, None),
    ("estado_facturacion", "POR_FACTURAR", "Por Facturar", 8, None),
    ("estado_facturacion", "FACTURADO", "Facturado", 9, None),
    ("estado_facturacion", "POR_PAGAR", "Por Pagar", 10, None),
    ("estado_facturacion", "PAGADO", "Pagado", 11, None),
    ("tipo_propiedad", "DEPARTAMENTO", "Departamento", 1, None),
    ("tipo_propiedad", "CASA", "Casa", 2, None),
    ("tipo_operacion", "VENTA", "Venta", 1, None),
    ("tipo_operacion", "ARRIENDO", "Arriendo", 2, None),
    ("estado_propiedad", "NUEVO", "Nuevo", 1, None),
    ("estado_propiedad", "USADO", "Usado", 2, None),
    # motivo_perdida arranca vacio a proposito (D-023): se puebla con lo que se
    # registre, no con una lista inventada.
]


def upgrade() -> None:
    catalogos = op.create_table(
        "catalogos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("metadatos", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tipo", "codigo", name="uq_catalogos_tipo_codigo"),
    )
    op.create_index("ix_catalogos_tipo", "catalogos", ["tipo"])

    etapas = op.create_table(
        "etapas",
        sa.Column("codigo", sa.String(4), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("responsable", sa.String(20), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("codigo"),
    )

    op.bulk_insert(
        etapas,
        [
            {"codigo": c, "nombre": n, "responsable": r, "orden": o, "activo": True}
            for c, n, r, o in ETAPAS
        ],
    )
    op.bulk_insert(
        catalogos,
        [
            {"tipo": t, "codigo": c, "nombre": n, "orden": o, "activo": True, "metadatos": m}
            for t, c, n, o, m in CATALOGOS
        ],
    )


def downgrade() -> None:
    op.drop_table("etapas")
    op.drop_index("ix_catalogos_tipo", table_name="catalogos")
    op.drop_table("catalogos")
