"""Borra fecha_cierre en los hitos que no estan cerrados

Revision ID: d1f4a72b6e59
Revises: c9d3e8a41f57
Create Date: 2026-08-22

**El Excel duplica su única fecha en las dos columnas.** `Fecha_Inicio` y
`Fecha_Cierre` traen el mismo valor en **todas** las filas, incluidas las dos
marcadas "Activo" y las diez "Perdido". Verificado sobre la hoja: VVP-15, activo,
dice inicio 2026-01-06 y cierre 2026-01-06.

El cargador de los históricos fue fiel al origen, como corresponde (`D-026`), así
que copió esa duplicación. El resultado es que **12 hitos que nunca cerraron
tienen fecha de cierre**, y ahí ese campo no es un dato: es ruido con forma de
dato.

**Por qué se limpia y no se deja.** Un negocio abierto con fecha de cierre es una
contradicción que cualquier consulta futura puede leer mal: hoy los servicios
filtran por `estado` antes de mirar `fecha_cierre`, pero eso es una convención
que hay que recordar, y una columna que se contradice con el estado es una trampa
para quien escriba la próxima consulta. Y no se pierde información: el valor era
una copia de `fecha_inicio`, que sigue ahí.

**Solo toca las filas donde el estado dice que no cerró.** Los 7 cerrados quedan
intactos, con su fecha, que es la única real que el Excel tenía.
"""
from alembic import op
import sqlalchemy as sa

revision = "d1f4a72b6e59"
down_revision = "c9d3e8a41f57"
branch_labels = None
depends_on = None


def upgrade() -> None:
    resultado = op.get_bind().execute(
        sa.text("""
            UPDATE negocio_hitos
            SET fecha_cierre = NULL
            WHERE estado <> 'CERRADO' AND fecha_cierre IS NOT NULL
        """)
    )
    print(f"[fecha_cierre] limpiada en {resultado.rowcount} hitos no cerrados")


def downgrade() -> None:
    """No se puede revertir, y decirlo es mejor que fingirlo.

    El valor que había era una copia de `fecha_inicio`. Restituirlo sería volver a
    escribir el ruido, no recuperar un dato: si alguna vez hace falta, la copia se
    reconstruye desde `fecha_inicio`, que nunca se toca. Se deja explícito en vez
    de dejar un `pass` que parece un olvido.
    """
    pass
