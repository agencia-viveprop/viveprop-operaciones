"""Renombra comision_dbrokers a comision_dataprop

Revision ID: f7a2c95e13d8
Revises: e6f3a1d84b25
Create Date: 2026-08-27

**Por qué.** La columna se llamaba `comision_dbrokers` y el formulario decía
«Comisión DBrokers», y eso ocultaba de quién es esa plata. Quedó aclarado que
**ViveProp no participa en los canjes ni percibe nada de ellos**: opera el Centro
de Canje a nombre de Dataprop, así que la comisión es de Dataprop. Un nombre que no
dice de quién es la plata es el tipo de cosa que en seis meses hace que alguien la
sume con los ingresos de ViveProp.

**Y cambia lo que significa.** Antes era un monto que alguien escribía sin una regla
detrás. Ahora la comisión estimada la calcula el motor a partir del valor de la
propiedad, y este campo pasa a ser **la comisión real que se cobró cuando el canje
cerró**: un hecho que se negocia y se factura, no algo que se derive. Está vacío en
las 303 filas, porque nunca se cerró un canje.

Es un rename, no una columna nueva: los datos que hubiera se conservan. El
importador de Dataprop no toca este campo --se llena a mano-- así que no hay nada
más que ajustar del lado de la carga.
"""
from alembic import op

revision = "f7a2c95e13d8"
down_revision = "e6f3a1d84b25"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("canjes", "comision_dbrokers", new_column_name="comision_dataprop")
    op.alter_column(
        "canjes", "comision_dbrokers_moneda", new_column_name="comision_dataprop_moneda"
    )


def downgrade() -> None:
    op.alter_column("canjes", "comision_dataprop", new_column_name="comision_dbrokers")
    op.alter_column(
        "canjes", "comision_dataprop_moneda", new_column_name="comision_dbrokers_moneda"
    )
