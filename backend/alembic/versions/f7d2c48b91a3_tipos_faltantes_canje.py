"""tres tipos de movimiento de canje que faltaban, y reordenar el catalogo

Revision ID: f7d2c48b91a3
Revises: e5b73c19af42
Create Date: 2026-08-21

Al migrar el seguimiento operativo (sprint 21) aparecio que el catalogo sembrado
en B3 no cubre tres de las diez columnas del checklist del Excel:

- `Cliente calificado solicitante`
- `Propiedad disponible propietario`
- `Email registro solicitante` -- existia `EMAIL_REGISTRO_PROPIETARIO` pero no su
  par del solicitante, que es una omision evidente

Sin ellos la migracion perderia 100 pasos ya completados, asi que se agregan.

Se reordena todo el catalogo siguiendo el orden real del proceso, que es el de
las columnas de la hoja. El `orden` solo afecta como se listan, pero un
desplegable que no sigue el flujo de trabajo hace que la gente busque.
"""
from alembic import op
import sqlalchemy as sa

revision = "f7d2c48b91a3"
down_revision = "e5b73c19af42"
branch_labels = None
depends_on = None

# codigo, nombre, sla_horas, sla_es_habil, canal, responsable
NUEVOS = [
    ("CLIENTE_CALIFICADO", "Cliente calificado", 24, False, "Admin DataProp", "Operaciones"),
    ("PROPIEDAD_DISPONIBLE", "Propiedad disponible", 24, False, "Admin DataProp", "Operaciones"),
    ("EMAIL_REGISTRO_SOLICITANTE", "Email registro solicitante", 3, False, "Email", "Operaciones"),
]

# El orden del proceso, tal como lo recorren las columnas de la hoja.
ORDEN = [
    "GESTION_INICIAL",
    "CLIENTE_CALIFICADO",
    "PROPIEDAD_DISPONIBLE",
    "WA_CONFIRM_SOLICITANTE",
    "EMAIL_REGISTRO_SOLICITANTE",
    "WA_CONFIRM_PROPIETARIO",
    "EMAIL_REGISTRO_PROPIETARIO",
    "INSISTENCIA_PROPIETARIO",
    "MANDATO_FIRMADO",
    "VALIDACION_SOLICITANTE",
    "VALIDACION_PROPIETARIO",
    "ACUERDO_FIRMADO",
    "OFERTA_ENVIADA",
    "NEGOCIACION",
    "CIERRE",
    "CANCELACION",
    "COMENTARIO_GENERAL",
]

# El orden que tenian antes, para poder volver atras.
ORDEN_ANTERIOR = [
    "GESTION_INICIAL", "WA_CONFIRM_SOLICITANTE", "WA_CONFIRM_PROPIETARIO",
    "EMAIL_REGISTRO_PROPIETARIO", "INSISTENCIA_PROPIETARIO", "VALIDACION_SOLICITANTE",
    "VALIDACION_PROPIETARIO", "MANDATO_FIRMADO", "ACUERDO_FIRMADO", "OFERTA_ENVIADA",
    "NEGOCIACION", "CIERRE", "CANCELACION", "COMENTARIO_GENERAL",
]


def _renumerar(codigos: list[str]) -> None:
    for i, codigo in enumerate(codigos, start=1):
        op.execute(
            sa.text("UPDATE tipos_movimiento SET orden = :o WHERE codigo = :c").bindparams(
                o=i, c=codigo
            )
        )


def upgrade() -> None:
    tipos = sa.table(
        "tipos_movimiento",
        sa.column("codigo", sa.String),
        sa.column("entity_type", sa.Enum(name="entity_type")),
        sa.column("nombre", sa.String),
        sa.column("etapa_resultante", sa.String),
        sa.column("orden", sa.Integer),
        sa.column("sla_horas", sa.Numeric),
        sa.column("sla_es_habil", sa.Boolean),
        sa.column("canal", sa.String),
        sa.column("responsable_default", sa.String),
        sa.column("activo", sa.Boolean),
    )
    op.bulk_insert(
        tipos,
        [
            {
                "codigo": c,
                "entity_type": "canje",
                "nombre": n,
                "etapa_resultante": None,
                "orden": 99,
                "sla_horas": sla,
                "sla_es_habil": habil,
                "canal": canal,
                "responsable_default": resp,
                "activo": True,
            }
            for c, n, sla, habil, canal, resp in NUEVOS
        ],
    )
    _renumerar(ORDEN)


def downgrade() -> None:
    op.execute(
        "DELETE FROM tipos_movimiento WHERE codigo IN ("
        + ", ".join(f"'{c}'" for c, *_ in NUEVOS)
        + ")"
    )
    _renumerar(ORDEN_ANTERIOR)
