"""Etapa y tipo de movimiento como dos campos, y el catálogo de tipos que se usa

Revision ID: b8f3a71c904e
Revises: a7e4c92f18b3
Create Date: 2026-08-25

**Qué cambia.** Registrar una gestión de canje pedía un solo dato --el tipo de
movimiento-- y la etapa salía implícita de él: `ACUERDO_FIRMADO` movía el canje a
«Proceso de acuerdo» y `CLIENTE_CALIFICADO` no lo movía a ninguna parte. Eso ataba
dos cosas que no son la misma: **qué se hizo** y **dónde quedó el canje**. Con una
sola llamada de seguimiento no había forma de decir que el canje avanzó, ni de
avanzarlo sin inventar un tipo de movimiento que lo hiciera.

Ahora son dos campos que se eligen aparte y conviven en el mismo registro.

**Tres cosas hace esta migración.**

**Uno: `SIN_ETAPA` pasa a llamarse `RECEPCION`.** No es cosmético: el valor
significaba "Dataprop no mandó etapa", y la etapa que corresponde a un canje que
entró y no avanzó es «Recepción». Se hace con `ALTER TYPE ... RENAME VALUE`, que es
atómico y no toca ninguna fila. Se verificó que ningún `tipos_movimiento.
etapa_resultante` ni `movimientos.etapa_resultante` guarda ese texto, así que no
hay strings que queden colgando.

`CERRADO` **no** se renombra a `CIERRE`, y es deliberado: ahí el cambio sería
puramente de rótulo --es la misma etapa-- y ese valor sí está guardado como texto
en `movimientos.etapa_resultante`. Renombrarlo obligaría a actualizar esas filas
para ganar nada. Se muestra como «Cierre» en la pantalla y se guarda como
`CERRADO`.

**Dos: los cuatro tipos que se van a usar.** `GESTION_INICIAL` ya existía y se le
saca su `etapa_resultante` --ahora la etapa la elige quien registra, no la impone
el tipo--; los otros tres son nuevos.

**Tres: los trece tipos que quedan fuera pasan a `activo = false`.** No se borran
ni por un momento: 605 movimientos los referencian y son la línea de tiempo de los
297 canjes. Inactivo quiere decir "no se ofrece más", no "no existió". `CANCELACION`
se queda activa aunque no esté en la lista nueva: es la única forma de dejar
registrado en la línea de tiempo cuándo y por qué se canceló un canje --editar el
estado a mano lo cambia sin dejar rastro--.
"""
from alembic import op
import sqlalchemy as sa

revision = "b8f3a71c904e"
down_revision = "a7e4c92f18b3"
branch_labels = None
depends_on = None

# Los que se ofrecen de acá en adelante. `etapa_resultante` va en nulo en todos:
# la etapa es un campo aparte y no una consecuencia del tipo.
TIPOS_NUEVOS = [
    ("SEG_LLAMADO", "Seguimiento - Llamado", 2),
    ("SEG_WHATSAPP", "Seguimiento - Whatsapp", 3),
    ("RESPUESTA_CORREDOR", "Respuesta Corredor", 4),
]

# Se ofrecen: los cuatro de la lista más la cancelación.
ACTIVOS = ("GESTION_INICIAL", "SEG_LLAMADO", "SEG_WHATSAPP", "RESPUESTA_CORREDOR", "CANCELACION")


def upgrade() -> None:
    con = op.get_bind()

    # --- 1. La etapa de entrada se llama Recepción -------------------------
    colgando = con.execute(
        sa.text(
            "SELECT count(*) FROM tipos_movimiento WHERE etapa_resultante = 'SIN_ETAPA'"
            " UNION ALL "
            "SELECT count(*) FROM movimientos WHERE etapa_resultante = 'SIN_ETAPA'"
        )
    ).scalars().all()
    if any(colgando):
        raise RuntimeError(
            f"Hay etapa_resultante = 'SIN_ETAPA' guardada como texto ({colgando}). "
            "Renombrar el valor del enum dejaría esas filas apuntando a una etapa "
            "que ya no existe: hay que actualizarlas primero."
        )
    op.execute("ALTER TYPE canje_etapa RENAME VALUE 'SIN_ETAPA' TO 'RECEPCION'")

    # --- 2. Los tipos que se van a usar -----------------------------------
    # La etapa la elige quien registra: el tipo deja de imponerla.
    con.execute(
        sa.text(
            "UPDATE tipos_movimiento SET etapa_resultante = NULL, orden = 1, activo = true "
            "WHERE codigo = 'GESTION_INICIAL'"
        )
    )
    for codigo, nombre, orden in TIPOS_NUEVOS:
        con.execute(
            sa.text(
                """
                INSERT INTO tipos_movimiento
                    (codigo, entity_type, nombre, etapa_resultante, orden,
                     sla_horas, sla_es_habil, canal, responsable_default, activo)
                VALUES (:codigo, 'canje', :nombre, NULL, :orden, NULL, false, NULL, NULL, true)
                ON CONFLICT (codigo) DO UPDATE
                    SET nombre = EXCLUDED.nombre,
                        etapa_resultante = NULL,
                        orden = EXCLUDED.orden,
                        activo = true
                """
            ),
            {"codigo": codigo, "nombre": nombre, "orden": orden},
        )

    # La cancelación se queda al final del selector: no es una gestión más.
    con.execute(
        sa.text(
            "UPDATE tipos_movimiento SET orden = 9, activo = true WHERE codigo = 'CANCELACION'"
        )
    )

    # --- 3. El resto sale del selector y se queda en el historial ---------
    activos = ", ".join(f"'{c}'" for c in ACTIVOS)
    resultado = con.execute(
        sa.text(
            f"UPDATE tipos_movimiento SET activo = false "
            f"WHERE entity_type = 'canje' AND codigo NOT IN ({activos}) "
            f"RETURNING codigo"
        )
    ).scalars().all()
    print(f"  {len(resultado)} tipos de canje quedaron inactivos: {', '.join(sorted(resultado))}")
    print(f"  se ofrecen: {', '.join(ACTIVOS)}")


def downgrade() -> None:
    con = op.get_bind()
    op.execute("ALTER TYPE canje_etapa RENAME VALUE 'RECEPCION' TO 'SIN_ETAPA'")
    con.execute(
        sa.text("UPDATE tipos_movimiento SET activo = true WHERE entity_type = 'canje'")
    )
    con.execute(
        sa.text(
            "UPDATE tipos_movimiento SET etapa_resultante = 'EN_REVISION' "
            "WHERE codigo = 'GESTION_INICIAL'"
        )
    )
    # Los tres nuevos se borran solo si nadie los usó: si hay movimientos que los
    # referencian, borrarlos rompería la clave foránea y la línea de tiempo.
    for codigo, _, _ in TIPOS_NUEVOS:
        usos = con.execute(
            sa.text("SELECT count(*) FROM movimientos WHERE tipo_movimiento = :c"),
            {"c": codigo},
        ).scalar()
        if usos:
            print(f"  {codigo} tiene {usos} movimientos: se deja, solo se desactiva")
            con.execute(
                sa.text("UPDATE tipos_movimiento SET activo = false WHERE codigo = :c"),
                {"c": codigo},
            )
        else:
            con.execute(
                sa.text("DELETE FROM tipos_movimiento WHERE codigo = :c"), {"c": codigo}
            )
