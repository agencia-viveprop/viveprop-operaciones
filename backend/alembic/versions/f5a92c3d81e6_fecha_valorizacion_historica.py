"""Deja los hitos históricos reproducibles por el motor

Revision ID: f5a92c3d81e6
Revises: e3b8c15d7a42
Create Date: 2026-08-22

**Editar un negocio histórico le cambiaba la plata en silencio.** Está medido: al
cerrar `VVP-17` desde la app su comisión real pasó de 774.691,95 a 759.166,55 sin
que se tocara ninguna tasa. Y `VVP-2` era peor: guardarlo le habría *subido* la
comisión total de 3.260.207 a 4.164.010, novecientos mil pesos de la nada.

La causa no es el motor de comisiones --sus 19 casos de regresión pasan-- sino el
paso anterior, la valorización, que nunca tuvo prueba propia. `D-026` cargó los
montos tal cual para no pasarlos por el motor; pero la API sí los pasa en cada
guardado, y la pantalla de edición de liquidaciones lo pone a un clic. Esta
migración cierra ese hueco: deja cada fila **consistente consigo misma**, de modo
que recalcularla dé exactamente lo mismo que ya está guardado.

**Uno: la fecha de valorización.** `resolver_valorizacion` toma la UF de
`fecha_valorizacion`, y si está vacía la de `fecha_inicio`. Trece de los 19 hitos
vinieron con esa fecha en nulo, así que se revalorizaban con la UF del día de
inicio y sobreescribían la `uf_snapshot` que traía el Excel. En once daba lo mismo
--la planilla usó justamente esa UF-- y en dos no: `VVP-15` y `VVP-17`, los dos
abiertos, que estaban valorizados con la UF del 20-08-2026.

Eso dice algo que hay que decidir aparte: **la planilla valorizaba los negocios
abiertos con la UF del día en que se exportaba**, o sea que el pipeline se
revalorizaba solo cada vez. Acá quedan fijos al 20-08-2026, que preserva el monto
que había pero lo congela. Falta definir con qué UF se valoriza un negocio abierto.

Los otros seis --`VVP-1`, `VVP-2`, `VVP-3 ESCRITURA`, `VVP-16`, `VVP-18` y
`VVP-19`-- **sí traían fecha en la planilla** y se reponen tal cual, sin
interpretarlas. (Una primera versión de esta migración las borró al bajar, por
confundirlas con las que ella misma escribe; ver `downgrade`.)

**Dos: las bases que no salen de la UF.** `VVP-3 PROMESA` y `VVP-16` traen un valor
en pesos que ninguna UF de la serie produce: la de la promesa (39.707,30) difiere en
1,23 de la más cercana, y la de `VVP-16` equivale a 40.976,47 cuando la propia
planilla anotaba 40.779,55. Los dos van con `valor_clp_manual`, que es exactamente
el campo para un valor en pesos que se afirma en vez de derivarse, y la ficha lo
muestra con su aviso en vez de esconderlo.

**Tres: el total redondeado.** La planilla guardaba `comision_total` al peso y las
demás columnas con todos sus decimales, así que las 19 filas diferían del motor en
menos de un peso. Se reescribe con el producto exacto --leyendo el lado que le toca
a cada modelo, que no es la suma de los dos-- porque si no cualquier guardado
futuro movería centavos y una auditoría no sabría distinguir eso de un problema
real.

**`VVP-2` queda intacto salvo su fecha, y a propósito.** Esa fila usó dos bases
distintas: el total lo calculó sobre 81.505.175 y el broker y la VP bruta sobre los
104.100.248,32 de la UF. Por eso no cuadra --es el descuadre de 903.803 que la
ficha muestra-- y por eso ninguna base única la reproduce: `test_comisiones.py` ya
la tiene como `xfail(strict=True)`. Ponerle `valor_clp_manual` le bajaría la
comisión real de 1.386.604 a 1.085.640, y dejarla derivar de la UF se la subiría a
4.164.010. Las dos son inventar plata. Se le fija la fecha de valorización, que
estabiliza su UF sin mover ningún monto, y el resto espera la decisión de negocio.

**Ninguna de las otras seis comisiones se recalcula.** Se copian del JSON tal como
vinieron del Excel. Lo que cambia son las *entradas* --fecha de valorización y
base-- para que el motor llegue a esos mismos montos. `VVP-17` ya quedó
revalorizado en `dev` por la prueba que encontró esto, así que acá se restituye;
en producción, donde nadie editó nada, escribe lo que ya hay.

`test_valorizacion_historica.py` es el resguardo: exige que los 19 hitos
reproduzcan su plata al pasar por el motor, con `VVP-2` como la única excepción y
nombrada. Sin esa prueba esto vuelve a pasar.
"""
import json
from decimal import Decimal
from pathlib import Path

from alembic import op
import sqlalchemy as sa

revision = "f5a92c3d81e6"
down_revision = "e3b8c15d7a42"
branch_labels = None
depends_on = None

DATOS = Path(__file__).resolve().parent.parent / "datos" / "historicos.json"
CENTAVO = Decimal("0.01")

# Las que venían en la planilla. Se reponen tal cual, sin interpretarlas.
DEL_ORIGEN = {
    ("VVP-1", None): "2025-12-10",
    ("VVP-2", None): "2025-12-10",
    ("VVP-3", "ESCRITURA"): "2026-02-28",
    ("VVP-16", None): "2026-06-15",
    ("VVP-18", None): "2026-05-18",
    ("VVP-19", None): "2026-06-01",
}

# Los dos abiertos, que no traían fecha: la planilla los valorizaba con la UF del
# día en que se exportaba. Se fijan al 20-08-2026 --la UF que quedó guardada-- para
# preservar el monto que había. Ver el docstring: falta decidir la regla.
DEDUCIDAS = {
    ("VVP-15", None): "2026-08-20",
    ("VVP-17", None): "2026-08-20",
}

VALORIZACIONES = {**DEL_ORIGEN, **DEDUCIDAS}

# (negocio, nombre) -> (base en pesos, por qué no sale de la UF).
BASES_A_MANO = {
    ("VVP-3", "PROMESA"): (
        Decimal("241755513.61"),
        "Valor traído del Excel. La UF que usó la planilla (39.707,30) no "
        "corresponde a ningún día de la serie --la más cercana difiere en 1,23-- "
        "así que el monto se afirma en vez de derivarse. La planilla anotaba como "
        "fecha de valorización el 26-12-2026, que es posterior a la promesa "
        "(16-12-2025) y parece un año mal tecleado; se dejó sin fecha porque "
        "todavía no existe UF para ese día y guardar el hito habría fallado.",
    ),
    ("VVP-16", None): (
        Decimal("43025295"),
        "Valor traído del Excel. La planilla calculó la comisión sobre este monto, "
        "que equivale a una UF de 40.976,47 y no a la de 40.779,55 que ella misma "
        "anotaba para el 15-06-2026: ninguna fecha de la serie llega a ese valor. "
        "El monto se afirma en vez de derivarse.",
    ),
}

# La fila que usó dos bases a la vez: ningún monto suyo se toca. Ver el docstring.
IRRECONCILIABLES = {("VVP-2", None)}

DEL_EXCEL = (
    "comision_broker", "rebate_concentrador", "comision_vp_bruta",
    "comision_equipo", "comision_tercero", "comision_real_vp",
)

# Qué lado cobra cada modelo. Es la regla de `_reparto` en app/services/
# comisiones.py, repetida acá porque una migración no importa código de la app:
# el día que el servicio cambie, esta migración ya corrió y no debe cambiar.
LADOS_POR_MODELO = {
    "MERCADO_PRIMARIO": ("pct_lado_vendedor",),
    "SECUNDARIO_CONCENTRADORES": ("pct_lado_comprador",),
    "SECUNDARIO_AGENCIA": ("pct_lado_vendedor", "pct_lado_comprador"),
}


def upgrade() -> None:
    con = op.get_bind()
    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    porclave = {(h["negocio"], h["nombre"]): h for h in datos["hitos"]}

    ufs = {
        str(f): Decimal(str(v))
        for f, v in con.execute(sa.text("SELECT fecha, valor FROM uf_diaria")).all()
    }
    filas = {
        (cod, nom): (hid, modelo)
        for hid, cod, nom, modelo in con.execute(
            sa.text(
                "SELECT h.id, n.codigo, h.nombre, n.modelo FROM negocio_hitos h "
                "JOIN negocios n ON n.id = h.negocio_id"
            )
        ).all()
    }

    tocados = 0
    for clave in sorted(porclave, key=lambda k: (k[0], k[1] or "")):
        fiel = porclave[clave]
        etiqueta = f"{clave[0]} {clave[1] or ''}".strip()
        if clave not in filas:
            print(f"  {etiqueta}: no existe en esta base, se salta")
            continue
        hid, modelo = filas[clave]

        fecha_val = VALORIZACIONES.get(clave)

        if clave in IRRECONCILIABLES:
            # Solo la fecha: estabiliza su UF sin mover un peso.
            con.execute(
                sa.text(
                    "UPDATE negocio_hitos SET fecha_valorizacion = :f WHERE id = :id"
                ),
                {"f": fecha_val, "id": hid},
            )
            tocados += 1
            print(f"  {etiqueta}: solo fecha ({fecha_val}); sus montos no cuadran y no se tocan")
            continue

        campos = {c: fiel[c] for c in DEL_EXCEL}
        campos["id"] = hid
        campos["fecha_valorizacion"] = fecha_val
        referencia = fecha_val or fiel["fecha_inicio"]

        # La misma regla del motor, escrita acá: sin esto la fila queda
        # afirmando una UF que su propia fecha no produce.
        if fiel["moneda"] == "UF":
            uf = ufs.get(referencia)
            if uf is None:
                print(f"  {etiqueta}: no hay UF del {referencia}, se salta")
                continue
            campos["uf_snapshot"] = uf
            campos["valor_clp_calculado"] = (
                Decimal(str(fiel["valor_negocio"])) * uf
            ).quantize(CENTAVO)
        else:
            campos["uf_snapshot"] = None
            campos["valor_clp_calculado"] = fiel["valor_negocio"]

        manual = BASES_A_MANO.get(clave)
        if manual is None:
            campos["valor_clp_manual"] = None
            campos["motivo_valor_manual"] = None
            base = Decimal(str(campos["valor_clp_calculado"]))
        else:
            base, campos["motivo_valor_manual"] = manual
            campos["valor_clp_manual"] = base

        # El modelo decide qué lado se cobra. Sumar los dos duplicaba el total:
        # la planilla puebla columnas que el modelo no usa.
        lados = LADOS_POR_MODELO.get(str(modelo))
        if lados is None:
            print(f"  {etiqueta}: modelo '{modelo}' desconocido, se salta")
            continue
        tasas = sum((Decimal(str(fiel[c] or 0)) for c in lados), Decimal(0))
        campos["comision_total"] = (base * tasas).quantize(CENTAVO)

        asignaciones = ", ".join(f"{c} = :{c}" for c in campos if c != "id")
        con.execute(
            sa.text(f"UPDATE negocio_hitos SET {asignaciones} WHERE id = :id"), campos
        )
        tocados += 1
        detalle = f"valoriza al {referencia}"
        if fecha_val is None:
            detalle += " (su fecha de inicio)"
        if manual is not None:
            detalle += f", base a mano {base}"
        print(f"  {etiqueta}: {detalle}")

    print(f"  -- {tocados} hitos quedaron reproducibles")


def downgrade() -> None:
    """No revierte nada, y es a propósito.

    La primera versión de esta migración bajaba poniendo `fecha_valorizacion` en
    nulo en todas las filas. Eso **borró en `dev` las seis fechas que sí venían de
    la planilla** --las de `DEL_ORIGEN`-- porque las confundió con las que esta
    migración escribe. Se recuperaron del export versionado, pero deja clara la
    lección: una migración de datos que "revierte" a un valor supuesto destruye el
    dato real que había.

    Revertir de verdad exigiría guardar el estado anterior fila por fila. No vale
    la pena: el estado al que se volvería es precisamente el defecto que esto
    arregla --guardar un hito le movía la plata-- y `upgrade` es idempotente, así
    que volver a subir siempre deja lo mismo.
    """
    pass
