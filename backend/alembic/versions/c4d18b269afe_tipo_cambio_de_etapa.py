"""Agrega el tipo CAMBIO_ETAPA, que registra los cambios hechos desde la ficha

Revision ID: c4d18b269afe
Revises: b8f3a71c904e
Create Date: 2026-08-25

**El hueco que cierra.** La etapa de un canje se puede cambiar por dos caminos:
registrando un movimiento en la bitácora, o editando la ficha. El primero quedaba
en la línea de tiempo y el segundo no. Medido en `dev`: se editó la ficha a «En
oferta» y la bitácora siguió mostrando que el último movimiento la había dejado en
«En negocio». Las dos pantallas decían cosas distintas y el cambio no tenía fecha
ni autor.

Eso es especialmente malo para lo que la bitácora existe --registrar historial y
poder armar después un reporte de línea de tiempo con gestiones y actividades--:
un cambio de etapa sin rastro no aparece en ninguno.

**Va como `activo = false`, y no es una contradicción.** El campo significa "se
ofrece en el selector", y este tipo no se elige: lo escribe el sistema cuando
alguien edita la ficha. Necesita existir en el catálogo porque `movimientos.
tipo_movimiento` tiene clave foránea contra él.

**El `orden` va alto** para que, si algún día se listan los inactivos, quede al
final: no es una gestión, es una nota de auditoría.
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d18b269afe"
down_revision = "b8f3a71c904e"
branch_labels = None
depends_on = None

CODIGO = "CAMBIO_ETAPA"


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            INSERT INTO tipos_movimiento
                (codigo, entity_type, nombre, etapa_resultante, orden,
                 sla_horas, sla_es_habil, canal, responsable_default, activo)
            VALUES (:codigo, 'canje', 'Cambio de etapa', NULL, 90,
                    NULL, false, NULL, NULL, false)
            ON CONFLICT (codigo) DO UPDATE
                SET nombre = EXCLUDED.nombre, activo = false
            """
        ),
        {"codigo": CODIGO},
    )


def downgrade() -> None:
    con = op.get_bind()
    # Solo se borra si nadie lo usó: si hay movimientos que lo referencian,
    # borrarlo rompería la clave foránea y con ella la línea de tiempo.
    usos = con.execute(
        sa.text("SELECT count(*) FROM movimientos WHERE tipo_movimiento = :c"),
        {"c": CODIGO},
    ).scalar()
    if usos:
        print(f"  {CODIGO} tiene {usos} movimientos: se deja en el catálogo")
    else:
        con.execute(
            sa.text("DELETE FROM tipos_movimiento WHERE codigo = :c"), {"c": CODIGO}
        )
