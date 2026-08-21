"""etapa al negocio y tipos de movimiento de negocio

Revision ID: e5b73c19af42
Revises: d3a91f6c25b8
Create Date: 2026-08-21

Dos cosas, y la primera habilita la segunda.

**`etapa` pasa del hito al negocio.** `D-020` dejo dicho que el pipeline E1-E7 es
del negocio y que el hito es una liquidacion dentro de el, pero la columna habia
quedado en el hito porque asi estaba en el Excel. Verificado sobre los 18
negocios cargados: ningun negocio tiene hitos con etapas distintas, asi que el
movimiento es sin perdida. `estado` NO se mueve -- que la promesa cierre y la
escritura se caiga es un escenario real.

**Se siembran los tipos de movimiento de negocio**, con prefijo `NEG_` porque
`tipos_movimiento.codigo` es clave primaria global y ya existen `CIERRE`,
`CANCELACION` y `COMENTARIO_GENERAL` para canjes (D-014).
"""
from alembic import op
import sqlalchemy as sa

revision = "e5b73c19af42"
down_revision = "d3a91f6c25b8"
branch_labels = None
depends_on = None

# codigo, nombre, etapa_resultante, orden, responsable_default
TIPOS_NEGOCIO = [
    ("NEG_E1_CALIFICACION", "Calificación del cliente", "E1", 1, "Comercial"),
    ("NEG_E2_VISITA", "Visita y manifestación de interés", "E2", 2, "Comercial"),
    ("NEG_E3_PROMESA", "Negociación, reserva y promesa", "E3", 3, "Híbrido"),
    ("NEG_E4_DOCUMENTACION", "Documentación / EETT / Tasación", "E4", 4, "Operaciones"),
    ("NEG_E5_ESCRITURA", "Escritura / Contrato / firma final", "E5", 5, "Operaciones"),
    ("NEG_E6_ENTREGA", "Entrega y distribución de pagos", "E6", 6, "Operaciones"),
    ("NEG_E7_TERMINADO", "Terminado", "E7", 7, "Operaciones"),
    # Sin etapa resultante: no mueven el negocio en el pipeline.
    ("NEG_PERDIDA", "Negocio perdido", None, 8, "Comercial"),
    ("NEG_DESISTIMIENTO", "Cliente desistió", None, 9, "Comercial"),
    ("NEG_COMENTARIO", "Comentario general", None, 10, None),
]


def upgrade() -> None:
    op.add_column("negocios", sa.Column("etapa", sa.String(4), nullable=True))
    op.create_foreign_key(
        "fk_negocios_etapa", "negocios", "etapas", ["etapa"], ["codigo"]
    )
    # Se copia desde el hito mas antiguo de cada negocio. Verificado que todos
    # los hitos de un negocio comparten etapa, asi que cual se elija da igual.
    op.execute(
        """
        UPDATE negocios n
        SET etapa = (
            SELECT h.etapa FROM negocio_hitos h
            WHERE h.negocio_id = n.id AND h.etapa IS NOT NULL
            ORDER BY h.fecha_inicio
            LIMIT 1
        )
        """
    )
    op.drop_constraint("negocio_hitos_etapa_fkey", "negocio_hitos", type_="foreignkey")
    op.drop_column("negocio_hitos", "etapa")

    tipos = sa.table(
        "tipos_movimiento",
        sa.column("codigo", sa.String),
        sa.column("entity_type", sa.Enum(name="entity_type")),
        sa.column("nombre", sa.String),
        sa.column("etapa_resultante", sa.String),
        sa.column("orden", sa.Integer),
        sa.column("sla_es_habil", sa.Boolean),
        sa.column("responsable_default", sa.String),
        sa.column("activo", sa.Boolean),
    )
    op.bulk_insert(
        tipos,
        [
            {
                "codigo": c,
                "entity_type": "negocio",
                "nombre": n,
                "etapa_resultante": etapa,
                "orden": orden,
                "sla_es_habil": False,
                "responsable_default": resp,
                "activo": True,
            }
            for c, n, etapa, orden, resp in TIPOS_NEGOCIO
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM tipos_movimiento WHERE codigo IN ("
        + ", ".join(f"'{c}'" for c, *_ in TIPOS_NEGOCIO)
        + ")"
    )
    op.add_column("negocio_hitos", sa.Column("etapa", sa.String(4), nullable=True))
    op.create_foreign_key(
        "negocio_hitos_etapa_fkey", "negocio_hitos", "etapas", ["etapa"], ["codigo"]
    )
    op.execute(
        """
        UPDATE negocio_hitos h
        SET etapa = (SELECT n.etapa FROM negocios n WHERE n.id = h.negocio_id)
        """
    )
    op.drop_constraint("fk_negocios_etapa", "negocios", type_="foreignkey")
    op.drop_column("negocios", "etapa")
