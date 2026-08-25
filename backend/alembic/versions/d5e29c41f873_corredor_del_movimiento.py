"""Agrega movimientos.corredor: sobre quién se hizo la gestión

Revision ID: d5e29c41f873
Revises: c4d18b269afe
Create Date: 2026-08-25

**Qué falta hoy.** La bitácora dice **qué se hizo** (el tipo), **dónde quedó el
canje** (la etapa) y **cuándo** (la fecha), pero no sobre quién. Un canje tiene dos
corredores --el solicitante y el propietario-- y una llamada o un WhatsApp se le
hace a uno de los dos. Sin ese dato, "Seguimiento - Llamado · 3 veces" no dice si
se insistió tres veces al mismo o una vez a cada uno, y un reporte de gestión no
puede separar quién no contesta.

**Va como `String(20)` y no como un tipo enumerado de Postgres**, siguiendo lo que
ya hace `etapa_resultante` en esta misma tabla. El motivo es el mismo: `movimientos`
es polimórfica --sirve a canjes y a negocios-- y un valor que solo tiene sentido en
uno de los dos dominios no debería imponerle un tipo a la columna que comparten. La
validación la hace Pydantic en la API, que es donde el dominio se conoce.

**Nullable, y sin relleno de las filas que ya están.** Los 605 movimientos migrados
no traen esa información: el Excel no la tenía. Dejarlos en nulo dice la verdad
--"no se sabe"-- y adivinar un corredor para completar la columna habría sido
inventar historial.

**Optativo también de acá en adelante.** El pedido fue "la opción de registrar", y
hay gestiones que no son sobre un corredor: una cancelación, un comentario
general. Forzar la elección obligaría a poner un dato falso en esos casos.
"""
from alembic import op
import sqlalchemy as sa

revision = "d5e29c41f873"
down_revision = "c4d18b269afe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("movimientos", sa.Column("corredor", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("movimientos", "corredor")
