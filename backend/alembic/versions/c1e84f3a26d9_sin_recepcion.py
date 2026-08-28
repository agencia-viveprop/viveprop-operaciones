"""«Recepción» deja de ser una etapa: lo que estaba ahí pasa a «En revisión».

Revierte el criterio de `b8f3a71c904e`, que había renombrado `SIN_ETAPA` a
`RECEPCION` razonando que «la etapa que corresponde a un canje que entró y no
avanzó es Recepción». Ese fue el error: le puso nombre de etapa a una ausencia de
dato en el export de Dataprop.

Lo que se midió sobre producción antes de decidir (`D-081`):

- La etapa quedaba registrada en 32 de 631 movimientos de canje, y los tramos
  cerrados de «Recepción» daban **0 días**: nadie pasa tiempo ahí.
- Los **75 canjes** que la tenían estaban **todos cancelados**. Ninguno activo.
- Ningún `tipos_movimiento` la asigna: los dos movimientos que la traen se
  registraron eligiéndola a mano en el selector, que este cambio saca.

**Lo que se pierde, y es la razón por la que está escrito acá:** después de esto
los 75 no se distinguen de los que Dataprop sí marcó «En revisión». Una migración
no puede reconstruir cuáles eran cuáles; la vuelta atrás es el historial de Neon.

El valor `RECEPCION` **se queda en el tipo `canje_etapa`**: Postgres no admite
quitar un valor de un enum, y recrear el tipo para borrar un valor que ninguna
fila usa sería mucho riesgo por nada. Queda huérfano e invisible.

Revision ID: c1e84f3a26d9
Revises: a3b7d02e94c1
"""
from alembic import op

revision = "c1e84f3a26d9"
down_revision = "a3b7d02e94c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE canjes SET etapa = 'EN_REVISION' WHERE etapa = 'RECEPCION'")
    # También en el historial: la insignia de esos movimientos mostraría un código
    # que la pantalla ya no ofrece. `etapa_resultante` es texto --la tabla es
    # polimórfica-- así que acá se compara con un string y no con el enum.
    op.execute(
        """
        UPDATE movimientos SET etapa_resultante = 'EN_REVISION'
        WHERE entity_type = 'canje' AND etapa_resultante = 'RECEPCION'
        """
    )
    # Y en la configuración de tipos, por si algún día se agrega uno que la use.
    op.execute(
        """
        UPDATE tipos_movimiento SET etapa_resultante = 'EN_REVISION'
        WHERE entity_type = 'canje' AND etapa_resultante = 'RECEPCION'
        """
    )


def downgrade() -> None:
    """No se puede deshacer, y decirlo es más honesto que fingirlo.

    Devolver todo a `RECEPCION` sería peor que no hacer nada: mandaría ahí también
    a los canjes que Dataprop sí había marcado «En revisión». El camino de vuelta
    es restaurar desde el historial de Neon.
    """
    pass
