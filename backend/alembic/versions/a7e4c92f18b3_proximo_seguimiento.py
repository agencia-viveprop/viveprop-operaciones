"""Agrega movimientos.proximo_seguimiento

Revision ID: a7e4c92f18b3
Revises: f5a92c3d81e6
Create Date: 2026-08-25

**Para qué.** «Qué me toca hoy» ordenaba por horas sin gestión, que es un proxy:
mide cuánto hace que nadie toca un canje, no qué se prometió hacer. Con la fecha
de próximo seguimiento la pantalla pasa a responder la pregunta que su nombre
promete, y lo que hoy es una inferencia se vuelve un compromiso registrado.

**Va en `movimientos` y no en `canjes`.** El compromiso lo asume un movimiento
--"llamé y quedamos en que sigo el jueves"-- así que pertenece al registro de esa
gestión, no a la ficha. Puesto en `canjes` sería un campo que se sobreescribe sin
dejar rastro de quién lo movió ni desde cuándo; acá queda en la línea de tiempo,
al lado del movimiento que lo generó.

**El vigente es el del movimiento más reciente**, igual que la etapa (`D-052`).
Se deriva de la línea de tiempo en vez de acumularse, así que borrar un movimiento
devuelve el compromiso anterior sin ningún paso extra.

**Nullable, y sin valor por defecto en la base.** El default --dos días hábiles--
lo calcula el servicio, no la columna: depende de la fecha del movimiento y de
qué día de la semana cae, y eso no se expresa en un `server_default`. Las filas
que ya existen quedan en nulo, que es lo correcto: nadie prometió nada sobre ellas.

La tabla es polimórfica --sirve a canjes y a negocios-- así que la columna queda
disponible para los dos. Hoy solo la pantalla de canjes la usa.
"""
from alembic import op
import sqlalchemy as sa

revision = "a7e4c92f18b3"
down_revision = "f5a92c3d81e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "movimientos",
        sa.Column("proximo_seguimiento", sa.Date(), nullable=True),
    )
    # El índice es por la consulta de la bandeja: busca el movimiento más reciente
    # de cada canje y necesita su fecha de seguimiento. Sin él, con la tabla
    # creciendo un movimiento por gestión, esa consulta pasa a recorrerla entera.
    op.create_index(
        "idx_movimientos_proximo_seguimiento",
        "movimientos",
        ["entity_type", "proximo_seguimiento"],
    )


def downgrade() -> None:
    op.drop_index("idx_movimientos_proximo_seguimiento", table_name="movimientos")
    op.drop_column("movimientos", "proximo_seguimiento")
