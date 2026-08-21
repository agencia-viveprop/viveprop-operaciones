"""Deja activos solo los canjes vigentes al 2026-08-21

Revision ID: a4e81b6f30c9
Revises: f7d2c48b91a3
Create Date: 2026-08-21

En Dataprop quedaban seis solicitudes vivas y la base arrastraba 225 activas, asi
que la app mostraba como pendiente trabajo que no existe: la bandeja abria con
194 filas y ninguna era real.

**Va como migracion y no como script a proposito.** Es la unica via que alcanza
produccion sola, en el deploy, sin depender de que alguien corra algo con la
credencial de la base a mano. Es el mismo mecanismo que ya lleva los catalogos y
los tipos de movimiento.

**Cancela todo lo que no este en la lista, incluidos los que tienen etapa
CERRADO.** Se advirtio que eso pierde la distincion entre "se cayo" y "se
concluyo" -- en `dev` eran 31 casos -- y la decision fue cancelarlos igual. La
etapa **no se toca**, asi que esa informacion sigue guardada y el `downgrade`
puede devolver el estado exacto.

**Es idempotente.** Solo mira los que estan ACTIVO, asi que aplicarla dos veces
no hace nada la segunda. Y se adapta a cada base: en `dev` cancela 221, en
produccion menos, porque alla hay seis cancelaciones mas que la rama no tiene.

**Deja rastro.** Cada cancelacion inserta un movimiento CANCELACION con un
comentario que dice que fue esta limpieza. Sin eso, quien abra el canje #150 en
seis meses ve CANCELADO sin ninguna explicacion. El `downgrade` usa justamente
esos movimientos para saber a quien revertir.

**`autor_id` va nulo**: no lo hizo una persona, lo hizo una migracion, y firmar
con la cuenta del admin seria decir algo que no paso.
"""
from alembic import op
import sqlalchemy as sa

revision = "a4e81b6f30c9"
down_revision = "f7d2c48b91a3"
branch_labels = None
depends_on = None

# Las solicitudes vivas en Dataprop al 2026-08-21. #364 y #367 son posteriores al
# ultimo export, asi que puede que no existan en la base todavia; no importa,
# la condicion es por exclusion.
VIGENTES = (334, 344, 359, 360, 364, 367)

TIPO = "CANCELACION"
MARCA = "Cancelado en la limpieza del 2026-08-21"
COMENTARIO = (
    f"{MARCA}: no estaba entre las solicitudes vigentes en Dataprop."
)


def upgrade() -> None:
    vigentes = ", ".join(str(v) for v in VIGENTES)

    # El movimiento primero: se necesita saber a quien se cancelo, y despues del
    # UPDATE ya no habria forma de distinguirlos de los cancelados de antes.
    op.execute(sa.text(f"""
        INSERT INTO movimientos (entity_type, entity_id, tipo_movimiento,
                                 etapa_resultante, fecha, autor_id, comentario)
        SELECT 'canje', c.id, '{TIPO}', NULL, now(), NULL, :comentario
        FROM canjes c
        WHERE c.estado = 'ACTIVO' AND c.id NOT IN ({vigentes})
    """).bindparams(comentario=COMENTARIO))

    op.execute(sa.text(f"""
        UPDATE canjes
        SET estado = 'CANCELADO',
            -- Lo mismo que hace la app al cancelar: sin esto, una importacion
            -- posterior de Dataprop volveria a pisar los datos del canje.
            gestionado_en_app = true
        WHERE estado = 'ACTIVO' AND id NOT IN ({vigentes})
    """))


def downgrade() -> None:
    """Devuelve a ACTIVO exactamente los que esta migracion cancelo.

    Se identifican por su movimiento, no por la lista de vigentes: si alguien
    cancelo otros canjes despues, revertir por exclusion se los llevaria puestos.
    """
    op.execute(sa.text("""
        UPDATE canjes SET estado = 'ACTIVO'
        WHERE id IN (
            SELECT entity_id FROM movimientos
            WHERE entity_type = 'canje'
              AND tipo_movimiento = :tipo
              AND comentario LIKE :marca
        )
    """).bindparams(tipo=TIPO, marca=f"{MARCA}%"))

    op.execute(sa.text("""
        DELETE FROM movimientos
        WHERE entity_type = 'canje'
          AND tipo_movimiento = :tipo
          AND comentario LIKE :marca
    """).bindparams(tipo=TIPO, marca=f"{MARCA}%"))
