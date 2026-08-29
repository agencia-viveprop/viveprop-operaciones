"""obligaciones: la tabla de negocios pasa a servir tambien a canjes

Revision ID: d7f14a83c26b
Revises: c1e84f3a26d9
Create Date: 2026-08-29

`negocio_obligaciones` se renombra a `obligaciones` y pasa a colgar de una
liquidacion de negocio **o** de un canje, exactamente una de las dos, con un
CHECK que lo exige (`D-092`). Se renombra y no se crea una tabla nueva por dos
razones: las 114 filas historicas del Excel se conservan sin copiarlas, y una
sola tabla es lo que permite que la vista de cobranza consulte los dos mundos
con una consulta en vez de dos unidas a mano.

`hito_id` pasa a nulable --es la condicion para que un canje pueda ser el
dueño-- y el CHECK es lo que impide que quede nulo en los dos.

Se agrega `obligacion_avances`, la historia: cada cambio de estado guarda su
propio monto y fecha, porque al facturar se registran los de la factura y al
pagar los del pago, y con un solo par de campos el segundo registro pisaria al
primero.

Sobre el enum: `ALTER TYPE ... ADD VALUE` corre dentro de la transaccion de
Alembic siempre que el valor nuevo no se **use** en la misma transaccion. Aca
solo se agrega al tipo; las filas de canje las escribe la app despues.
"""
from alembic import op
import sqlalchemy as sa

revision = "d7f14a83c26b"
down_revision = "c1e84f3a26d9"
branch_labels = None
depends_on = None

MONTO = sa.Numeric(16, 2)

# Los dos tipos de canje: una factura por corredor, porque Dataprop le cobra su
# comision a cada uno de los dos por separado.
TIPOS_DE_CANJE = ("FACT_CORREDOR_SOLICITANTE", "FACT_CORREDOR_PROPIETARIO")

UN_DUENO = (
    "(hito_id IS NOT NULL AND canje_id IS NULL)"
    " OR (hito_id IS NULL AND canje_id IS NOT NULL)"
)


def upgrade() -> None:
    for tipo in TIPOS_DE_CANJE:
        op.execute(f"ALTER TYPE tipo_obligacion ADD VALUE IF NOT EXISTS '{tipo}'")

    op.rename_table("negocio_obligaciones", "obligaciones")
    # El rename de la tabla no toca los nombres de sus objetos dependientes, asi
    # que quedarian llamandose `negocio_obligaciones_*` para siempre. Se
    # renombran para que el nombre siga diciendo de que tabla es.
    op.execute("ALTER INDEX negocio_obligaciones_pkey RENAME TO obligaciones_pkey")
    op.execute(
        "ALTER SEQUENCE negocio_obligaciones_id_seq RENAME TO obligaciones_id_seq"
    )
    op.execute(
        "ALTER TABLE obligaciones RENAME CONSTRAINT"
        " uq_negocio_obligaciones_hito_tipo TO uq_obligaciones_hito_tipo"
    )

    op.alter_column("obligaciones", "hito_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("obligaciones", sa.Column("canje_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_obligaciones_canje", "obligaciones", "canjes", ["canje_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_obligaciones_canje_tipo", "obligaciones", ["canje_id", "tipo"]
    )
    op.create_check_constraint("ck_obligaciones_un_dueno", "obligaciones", UN_DUENO)

    op.create_table(
        "obligacion_avances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("obligacion_id", sa.Integer(), nullable=False),
        sa.Column("estado_id", sa.Integer(), nullable=True),
        sa.Column("monto", MONTO, nullable=True),
        sa.Column("fecha", sa.Date(), nullable=True),
        sa.Column("autor_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["obligacion_id"], ["obligaciones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["estado_id"], ["catalogos.id"]),
        # SET NULL y no CASCADE: borrar una cuenta no puede borrar la historia de
        # cobranza, igual que en movimientos.
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_obligacion_avances_obligacion", "obligacion_avances", ["obligacion_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_obligacion_avances_obligacion", table_name="obligacion_avances")
    op.drop_table("obligacion_avances")

    # Las obligaciones de canje se borran: en la tabla vieja no cabian, y volver
    # atras con `hito_id` nulo es imposible.
    op.execute("DELETE FROM obligaciones WHERE canje_id IS NOT NULL")
    op.drop_constraint("ck_obligaciones_un_dueno", "obligaciones", type_="check")
    op.drop_constraint("uq_obligaciones_canje_tipo", "obligaciones", type_="unique")
    op.drop_constraint("fk_obligaciones_canje", "obligaciones", type_="foreignkey")
    op.drop_column("obligaciones", "canje_id")
    op.alter_column(
        "obligaciones", "hito_id", existing_type=sa.Integer(), nullable=False
    )

    op.execute(
        "ALTER TABLE obligaciones RENAME CONSTRAINT"
        " uq_obligaciones_hito_tipo TO uq_negocio_obligaciones_hito_tipo"
    )
    op.execute("ALTER SEQUENCE obligaciones_id_seq RENAME TO negocio_obligaciones_id_seq")
    op.execute("ALTER INDEX obligaciones_pkey RENAME TO negocio_obligaciones_pkey")
    op.rename_table("obligaciones", "negocio_obligaciones")
    # Los dos valores del enum quedan: Postgres no sabe sacar valores de un tipo.
