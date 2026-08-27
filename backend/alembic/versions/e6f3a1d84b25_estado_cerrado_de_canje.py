"""Agrega el estado CERRADO a los canjes

Revision ID: e6f3a1d84b25
Revises: d5e29c41f873
Create Date: 2026-08-27

**Qué falta hoy.** Un canje solo puede estar `ACTIVO` o `CANCELADO`, así que **no
hay forma de registrar que cerró**. Los 296 cancelados incluyen 31 que tienen la
etapa en «Cierre», y el usuario confirmó que esos se cayeron: llegaron hasta la
firma y no se concretaron. O sea que en cuatro años no se cerró ninguno, y el día
que se cierre el primero no hay dónde decirlo.

Eso tiene dos consecuencias que ya se veían en las pantallas:

- La métrica «Canjes cerrados» del reporte mensual da **0 en los 46 meses del
  histórico**, y no podía dar otra cosa: cuenta los que tienen etapa «Cierre` *y*
  fecha de cierre, y esa combinación no existe en ninguna fila.
- La vista directorio deducía los cerrados con la heurística «etapa Cierre y
  estado activo», que era lo mejor que se podía hacer sin un estado propio.

**Y ahora hace falta de verdad**, porque la comisión de Dataprop se cobra *por cada
operación cerrada*. El campo de comisión real pasa a ser el lugar donde se registra
lo que efectivamente se cobró al cerrar, y sin un estado que diga «cerró» ese campo
no tiene cuándo llenarse.

**Solo agrega el valor al tipo enumerado. No reclasifica ninguna fila.** Los 31 con
etapa «Cierre» siguen cancelados, porque eso es lo que son: el usuario lo confirmó
expresamente. Reetiquetarlos acá sería inventar 31 cierres que no ocurrieron.

`ALTER TYPE ... ADD VALUE` corre dentro de la transacción de Alembic sin problema
desde Postgres 12, siempre que el valor nuevo no se **use** en la misma
transacción. Acá solo se agrega.

El `downgrade` es un no-op declarado. Quitar un valor de un tipo enumerado en
Postgres obliga a recrear el tipo y reescribir la columna, y si alguna fila ya
quedó en `CERRADO` no hay a qué estado devolverla sin decidir por el usuario. Es la
misma decisión que en `b8f3a71c904e`.
"""
from alembic import op

revision = "e6f3a1d84b25"
down_revision = "d5e29c41f873"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE canje_estado ADD VALUE IF NOT EXISTS 'CERRADO'")


def downgrade() -> None:
    """No-op a propósito. Ver el docstring del módulo."""
