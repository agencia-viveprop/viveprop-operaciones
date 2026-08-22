"""Carga los negocios históricos y el seguimiento de canjes

Revision ID: b7c2f4a19d83
Revises: a4e81b6f30c9
Create Date: 2026-08-21

Los 18 negocios, sus 19 hitos y sus 114 obligaciones, más los 384 movimientos del
seguimiento migrado del Excel, se cargaron con scripts contra `dev` y nunca
llegaron a producción. Resultado: allá la pantalla de Negocios está vacía, su
dashboard en cero y el reporte semanal casi mudo -- nueve sprints de
funcionalidad sin nada que mostrar.

**Va como migración porque es la única vía que alcanza producción sola**, en el
deploy. Es el mismo mecanismo que ya llevó allá los catálogos, los tipos de
movimiento y la limpieza de canjes.

**Los datos están en `alembic/datos/historicos.json`**, no en el cuerpo de este
archivo: 550 filas inline lo volverían ilegible y mezclarían el paso de carga con
los datos que carga. El JSON lo genera
`app/scripts/exportar_historicos.py` desde `dev`.

**Los montos se cargan tal cual, sin recalcular** (`D-026`). Siete de estos
negocios están cerrados con plata ya facturada y `VVP-2` viene descuadrado del
origen; pasarlos por el motor cambiaría en silencio números que ya se cobraron.
Por eso el JSON trae las comisiones calculadas y esta migración no las toca.

**Las referencias a catálogos van por código, no por id.** Los ids son seriales
que asignó la migración de catálogos; corrió igual en las dos bases, así que
*deberían* coincidir. "Deberían" no alcanza cuando el resultado sería un negocio
atribuido a la alianza equivocada sin que nada falle.

**Es idempotente por código de negocio.** Un negocio que ya existe se saltea
entero, con sus hitos y obligaciones. Y los movimientos se saltean todos si ya
hay alguno migrado, para no duplicar una línea de tiempo.

**No borra ni actualiza nada.** Si producción ya tuviera un negocio con el mismo
código pero distinto contenido, esta migración lo respeta y sigue. Sobrescribir
datos de producción a ciegas es exactamente lo que no debe hacer una migración de
datos.
"""
import json
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "b7c2f4a19d83"
down_revision = "a4e81b6f30c9"
branch_labels = None
depends_on = None

DATOS = Path(__file__).resolve().parent.parent / "datos" / "historicos.json"

# Marca que identifica los movimientos del seguimiento migrado, para poder
# revertir solo esos y no los que se registren después desde la app.
MARCA_SEGUIMIENTO = "Migrado del Excel%"


# Cuantas filas por INSERT. Contra Neon cada statement es un viaje de red de
# ~180 ms; mandar 548 filas de a una tarda dos minutos y medio y deja el deploy
# expuesto a que la conexion se corte a mitad de camino. Agrupadas, son segundos.
# El `executemany` de SQLAlchemy sobre un `text()` no agrupa: manda una por una.
POR_LOTE = 100


def _insertar_en_lotes(
    conexion,
    tabla: str,
    columnas: list[str],
    plantilla_fila: str,
    filas: list[dict],
) -> int:
    """Un INSERT con muchas tuplas en el VALUES, partido en lotes.

    `plantilla_fila` es una tupla del VALUES con `{i}` donde va el número de fila,
    por ejemplo `"(:hito_{i}, CAST(:tipo_{i} AS tipo_obligacion))"`. Los nombres
    de los parámetros se numeran por fila para que no se pisen entre sí dentro
    del mismo statement.
    """
    if not filas:
        return 0
    for inicio in range(0, len(filas), POR_LOTE):
        lote = filas[inicio:inicio + POR_LOTE]
        tuplas = ", ".join(plantilla_fila.format(i=i) for i in range(len(lote)))
        params = {
            f"{col}_{i}": fila[col]
            for i, fila in enumerate(lote)
            for col in columnas
        }
        conexion.execute(
            sa.text(f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES {tuplas}"),
            params,
        )
    return len(filas)


def _catalogos(conexion) -> dict[tuple[str, str], int]:
    """`(tipo, codigo) -> id`, para resolver las referencias del JSON."""
    return {
        (tipo, codigo): id_
        for id_, tipo, codigo in conexion.execute(
            sa.text("SELECT id, tipo, codigo FROM catalogos")
        )
    }


def upgrade() -> None:
    if not DATOS.exists():
        # Sin el archivo no hay nada que cargar. No es un error: una base nueva
        # levantada desde cero no tiene por qué traer los históricos.
        print(f"[datos historicos] no existe {DATOS}, no se carga nada")
        return

    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    conexion = op.get_bind()
    cat = _catalogos(conexion)

    def ref(tipo: str, codigo) -> int | None:
        if codigo is None:
            return None
        id_ = cat.get((tipo, codigo))
        if id_ is None:
            raise RuntimeError(
                f"El catalogo '{tipo}' no tiene el codigo '{codigo}'. "
                "La migracion de catalogos tiene que haber corrido antes."
            )
        return id_

    # ------------------------------------------------------- propiedades
    #
    # Se reusa la que ya exista con la misma direccion, unidad y comuna: hay una
    # restriccion unica sobre esas tres columnas, asi que insertar a ciegas
    # fallaria en la segunda corrida. Las existentes se traen todas de un viaje.
    propiedad_id: dict[tuple, int] = {
        (d, u, c): i
        for i, d, u, c in conexion.execute(
            sa.text("SELECT id, direccion, unidad, comuna FROM propiedades")
        )
    }
    for p in datos["propiedades"]:
        clave = (p["direccion"], p["unidad"], p["comuna"])
        if clave in propiedad_id:
            continue
        propiedad_id[clave] = conexion.execute(
            sa.text("""
                INSERT INTO propiedades (direccion, unidad, comuna,
                                         tipo_propiedad_id, estado_propiedad_id)
                VALUES (:d, :u, :c, :tp, :ep)
                RETURNING id
            """),
            {
                "d": p["direccion"], "u": p["unidad"], "c": p["comuna"],
                "tp": ref("tipo_propiedad", p["tipo_propiedad"]),
                "ep": ref("estado_propiedad", p["estado_propiedad"]),
            },
        ).scalar()

    # ---------------------------------------------------------- negocios
    ya_existen = set(
        conexion.execute(sa.text("SELECT codigo FROM negocios")).scalars()
    )
    negocio_id: dict[str, int] = {}
    salteados: list[str] = []
    for n in datos["negocios"]:
        if n["codigo"] in ya_existen:
            salteados.append(n["codigo"])
            continue
        negocio_id[n["codigo"]] = conexion.execute(
            sa.text("""
                INSERT INTO negocios (codigo, propiedad_id, modelo, alianza_id,
                                      tipo_operacion_id, etapa, vendedor_arrendador,
                                      comprador_arrendatario, corredor_agente,
                                      notas, observaciones)
                VALUES (:codigo, :prop, CAST(:modelo AS modelo_negocio), :alianza,
                        :operacion, :etapa, :vendedor, :comprador, :corredor,
                        :notas, :observaciones)
                RETURNING id
            """),
            {
                "codigo": n["codigo"],
                "prop": propiedad_id[(n["direccion"], n["unidad"], n["comuna"])],
                "modelo": n["modelo"],
                "alianza": ref("alianza", n["alianza"]),
                "operacion": ref("tipo_operacion", n["tipo_operacion"]),
                "etapa": n["etapa"],
                "vendedor": n["vendedor_arrendador"],
                "comprador": n["comprador_arrendatario"],
                "corredor": n["corredor_agente"],
                "notas": n["notas"],
                "observaciones": n["observaciones"],
            },
        ).scalar()

    # ------------------------------------------------------------ hitos
    hito_id: dict[tuple[str, str], int] = {}
    for h in datos["hitos"]:
        if h["negocio"] not in negocio_id:
            continue  # su negocio ya existia: no se toca nada suyo
        hito_id[(h["negocio"], h["nombre"] or "")] = conexion.execute(
            sa.text("""
                INSERT INTO negocio_hitos (
                    negocio_id, nombre, fecha_inicio, fecha_cierre, estado,
                    valor_negocio, moneda, fecha_valorizacion, uf_snapshot,
                    valor_clp_calculado, valor_clp_manual, motivo_valor_manual,
                    pct_lado_vendedor, pct_lado_comprador, pct_rebate_concentrador,
                    pct_broker_vendedor, pct_broker_comprador,
                    pct_vp_vendedor, pct_vp_comprador, pct_equipo, pct_tercero,
                    nombre_tercero, comision_total, comision_broker,
                    rebate_concentrador, comision_vp_bruta, comision_equipo,
                    comision_tercero, comision_real_vp,
                    motivo_perdida_id, motivo_perdida_detalle
                ) VALUES (
                    :negocio, :nombre, :inicio, :cierre, CAST(:estado AS estado_negocio),
                    :valor, CAST(:moneda AS moneda_tipo), :fecha_val, :uf,
                    :clp_calc, :clp_manual, :motivo_manual,
                    :p_lv, :p_lc, :p_rebate, :p_bv, :p_bc, :p_vv, :p_vc,
                    :p_equipo, :p_tercero, :nombre_tercero,
                    :c_total, :c_broker, :c_rebate, :c_bruta, :c_equipo,
                    :c_tercero, :c_real, :motivo_id, :motivo_detalle
                ) RETURNING id
            """),
            {
                "negocio": negocio_id[h["negocio"]],
                "nombre": h["nombre"],
                "inicio": h["fecha_inicio"], "cierre": h["fecha_cierre"],
                "estado": h["estado"],
                "valor": h["valor_negocio"], "moneda": h["moneda"],
                "fecha_val": h["fecha_valorizacion"], "uf": h["uf_snapshot"],
                "clp_calc": h["valor_clp_calculado"], "clp_manual": h["valor_clp_manual"],
                "motivo_manual": h["motivo_valor_manual"],
                "p_lv": h["pct_lado_vendedor"], "p_lc": h["pct_lado_comprador"],
                "p_rebate": h["pct_rebate_concentrador"],
                "p_bv": h["pct_broker_vendedor"], "p_bc": h["pct_broker_comprador"],
                "p_vv": h["pct_vp_vendedor"], "p_vc": h["pct_vp_comprador"],
                "p_equipo": h["pct_equipo"], "p_tercero": h["pct_tercero"],
                "nombre_tercero": h["nombre_tercero"],
                "c_total": h["comision_total"], "c_broker": h["comision_broker"],
                "c_rebate": h["rebate_concentrador"], "c_bruta": h["comision_vp_bruta"],
                "c_equipo": h["comision_equipo"], "c_tercero": h["comision_tercero"],
                "c_real": h["comision_real_vp"],
                "motivo_id": ref("motivo_perdida", h["motivo_perdida"]),
                "motivo_detalle": h["motivo_perdida_detalle"],
            },
        ).scalar()

    # ---------------------------------------------------- obligaciones
    filas_oblig = [
        {
            "hito_id": hito_id[(o["negocio"], o["hito"] or "")],
            "tipo": o["tipo"],
            "estado_id": ref("estado_facturacion", o["estado"]),
            "monto": o["monto"],
            "fecha": o["fecha"],
        }
        for o in datos["obligaciones"]
        if (o["negocio"], o["hito"] or "") in hito_id
    ]
    _insertar_en_lotes(
        conexion,
        "negocio_obligaciones",
        ["hito_id", "tipo", "estado_id", "monto", "fecha"],
        "(:hito_id_{i}, CAST(:tipo_{i} AS tipo_obligacion), :estado_id_{i}, "
        "CAST(:monto_{i} AS numeric), CAST(:fecha_{i} AS date))",
        filas_oblig,
    )

    # ------------------------------------- movimientos del seguimiento
    #
    # Todo o nada: si ya hay alguno migrado, la linea de tiempo ya se cargo y
    # volver a insertarlos la duplicaria.
    ya_hay = conexion.execute(
        sa.text("""
            SELECT count(*) FROM movimientos
            WHERE entity_type = 'canje' AND comentario LIKE :marca
        """),
        {"marca": MARCA_SEGUIMIENTO},
    ).scalar()

    # Los autores existen en produccion -- la rama dev salio de ahi -- pero si
    # alguno faltara, la clave foranea haria fallar el deploy entero por una
    # firma. Se resuelve a nulo en ese caso: el movimiento vale mas que su autor.
    usuarios = set(conexion.execute(sa.text("SELECT id FROM usuarios")).scalars())

    movimientos = 0
    if not ya_hay:
        for m in datos["movimientos_canje"]:
            # El canje tiene que existir: en produccion estan los mismos ids,
            # pero si alguno faltara, insertar dejaria un movimiento huerfano.
            existe = conexion.execute(
                sa.text("SELECT 1 FROM canjes WHERE id = :id"), {"id": m["entity_id"]}
            ).scalar()
            if not existe:
                continue
            conexion.execute(
                sa.text("""
                    INSERT INTO movimientos (entity_type, entity_id, tipo_movimiento,
                                             etapa_resultante, fecha, autor_id, comentario)
                    VALUES ('canje', :id, :tipo, :etapa, :fecha, :autor, :comentario)
                """),
                {
                    "id": m["entity_id"], "tipo": m["tipo_movimiento"],
                    "etapa": m["etapa_resultante"], "fecha": m["fecha"],
                    "autor": m["autor_id"] if m["autor_id"] in usuarios else None, "comentario": m["comentario"],
                },
            )
            movimientos += 1

    print(
        f"[datos historicos] {len(negocio_id)} negocios, {len(hito_id)} hitos, "
        f"{movimientos} movimientos. Salteados por ya existir: {len(salteados)}"
    )


def downgrade() -> None:
    """Borra lo que esta migracion cargo, y solo eso.

    Los negocios se identifican por los codigos del JSON; los movimientos, por la
    marca de su comentario. Las propiedades se borran solo si quedaron sin
    negocios apuntandoles: pudo haber otra cosa reusando la misma direccion.
    """
    if not DATOS.exists():
        return

    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    conexion = op.get_bind()
    codigos = [n["codigo"] for n in datos["negocios"]]

    conexion.execute(
        sa.text("""
            DELETE FROM movimientos
            WHERE entity_type = 'canje' AND comentario LIKE :marca
        """),
        {"marca": MARCA_SEGUIMIENTO},
    )
    # Las obligaciones caen por el ON DELETE CASCADE de los hitos.
    conexion.execute(
        sa.text("""
            DELETE FROM negocio_hitos
            WHERE negocio_id IN (SELECT id FROM negocios WHERE codigo = ANY(:codigos))
        """),
        {"codigos": codigos},
    )
    conexion.execute(
        sa.text("DELETE FROM negocios WHERE codigo = ANY(:codigos)"),
        {"codigos": codigos},
    )
    conexion.execute(
        sa.text("""
            DELETE FROM propiedades
            WHERE id NOT IN (SELECT propiedad_id FROM negocios)
        """)
    )
