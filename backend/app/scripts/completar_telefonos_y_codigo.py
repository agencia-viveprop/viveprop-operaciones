"""Backfill único: pone `TELEFONO_CORREDOR_*` y `CODIGO_PROPIEDAD` en los
canjes que ya existían antes de que Dataprop agregara esas tres columnas.

**Por qué hace falta un script aparte.** La carga normal (`importar_canjes`)
ignora entero cualquier canje marcado `gestionado_en_app` (`D-096`), y la
mayoría de los canjes activos ya están en ese estado. Esos nunca reciben las
columnas nuevas por la vía normal, así que sin esto quedarían sin teléfono ni
código de propiedad para siempre.

**Por qué es seguro tocar también a los gestionados.** Las tres columnas son
nuevas: ningún canje pudo tener un valor puesto a mano en ellas, gestionado o
no, porque hasta este deploy la columna no existía en el esquema. No hay
ninguna edición humana que este script pueda pisar.

**Solo toca esas tres columnas.** No `estado`, no `etapa`, no nombre ni
correo del corredor, no fecha de cierre, nada más --ni siquiera en los
canjes no gestionados, donde la carga normal sí los actualizaría--. Es
deliberadamente más angosto que `importar_canjes` porque el único objetivo es
rellenar lo que antes no existía, sin repetir el resto de esa lógica ni sus
efectos secundarios.

**No escribe salvo que se lo pidan**, mismo criterio que
`aplicar_monedas_canjes`: sin `--aplicar` hace una pasada en seco y dice qué
cambiaría. Es el default porque esto corre contra producción.

Se corre desde `backend/`, pasándole el mismo .xlsx que se sube en «Importar
Canjes» (el export real de Dataprop, con las 19 columnas):

    python -m app.scripts.completar_telefonos_y_codigo ruta/al/archivo.xlsx
    python -m app.scripts.completar_telefonos_y_codigo ruta/al/archivo.xlsx --aplicar
"""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import openpyxl
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parent.parent.parent

# Mismo alias que usa `importar_canjes`, pero acá solo se leen los que hacen falta.
COL_ID = "ID_CANJE"
COL_TELEFONO_SOLICITANTE = "TELEFONO_CORREDOR_SOLICITANTE"
COL_TELEFONO_PROPIETARIO = "TELEFONO_CORREDOR_PROPIETARIO"
COL_CODIGO_PROPIEDAD = "CODIGO_PROPIEDAD"
COLUMNAS = (COL_ID, COL_TELEFONO_SOLICITANTE, COL_TELEFONO_PROPIETARIO, COL_CODIGO_PROPIEDAD)


@dataclass(frozen=True)
class FilaArchivo:
    canje_id: int
    telefono_solicitante: str | None
    telefono_propietario: str | None
    codigo_propiedad: str | None


@dataclass
class Plan:
    # canje_id, campo, de, a
    cambios: list[tuple[int, str, str | None, str | None]]
    ya_estaban: int = 0
    inexistentes: list[int] = None

    def __post_init__(self):
        self.inexistentes = self.inexistentes or []


def _texto(valor) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def leer_archivo(ruta: Path) -> list[FilaArchivo]:
    libro = openpyxl.load_workbook(ruta, data_only=True)
    hoja = libro.worksheets[0]

    encabezados = [c.value for c in hoja[1]]
    headers = {nombre: i for i, nombre in enumerate(encabezados) if nombre}
    faltantes = [c for c in COLUMNAS if c not in headers]
    if faltantes:
        raise SystemExit(f"Faltan columnas en el archivo: {', '.join(faltantes)}")

    filas = []
    for num_fila in range(2, hoja.max_row + 1):
        fila = tuple(c.value for c in hoja[num_fila])
        if all(v is None for v in fila):
            continue
        canje_id = fila[headers[COL_ID]]
        if canje_id is None or canje_id == "":
            continue
        filas.append(
            FilaArchivo(
                canje_id=int(float(canje_id)),
                telefono_solicitante=_texto(fila[headers[COL_TELEFONO_SOLICITANTE]]),
                telefono_propietario=_texto(fila[headers[COL_TELEFONO_PROPIETARIO]]),
                codigo_propiedad=_texto(fila[headers[COL_CODIGO_PROPIEDAD]]),
            )
        )
    return filas


def planificar(filas: list[FilaArchivo], actual: dict[int, tuple]) -> Plan:
    """Qué cambiar, sin tocar la base. `actual[id]` es
    (telefono_solicitante, telefono_propietario, codigo_propiedad) tal como
    están hoy. Un ID repetido en el archivo se resuelve con el último --mismo
    criterio que la carga normal--, porque se recorre en orden y cada `dict`
    de comparación usa el valor más reciente ya aplicado en el plan.
    """
    plan = Plan(cambios=[])
    vistos: dict[int, FilaArchivo] = {}
    for f in filas:
        vistos[f.canje_id] = f

    for canje_id, f in vistos.items():
        if canje_id not in actual:
            plan.inexistentes.append(canje_id)
            continue

        hoy_sol, hoy_prop, hoy_cod = actual[canje_id]
        cambio_para_este = False
        if hoy_sol != f.telefono_solicitante:
            plan.cambios.append((canje_id, "telefono_solicitante", hoy_sol, f.telefono_solicitante))
            cambio_para_este = True
        if hoy_prop != f.telefono_propietario:
            plan.cambios.append((canje_id, "telefono_propietario", hoy_prop, f.telefono_propietario))
            cambio_para_este = True
        if hoy_cod != f.codigo_propiedad:
            plan.cambios.append((canje_id, "codigo_propiedad", hoy_cod, f.codigo_propiedad))
            cambio_para_este = True
        if not cambio_para_este:
            plan.ya_estaban += 1

    return plan


def main() -> None:
    argumentos = [a for a in sys.argv[1:] if a != "--aplicar"]
    if not argumentos:
        raise SystemExit("Uso: python -m app.scripts.completar_telefonos_y_codigo <archivo.xlsx> [--aplicar]")
    archivo = Path(argumentos[0])
    if not archivo.exists():
        raise SystemExit(f"No existe el archivo: {archivo}")

    aplicar = "--aplicar" in sys.argv
    if not os.environ.get("DATABASE_URL"):
        load_dotenv(RAIZ / ".env")

    destino = os.environ["DATABASE_URL"].split("@")[-1].split("/")[0]
    print(f"archivo : {archivo}")
    print(f"base    : {destino}")
    print(f"modo    : {'APLICAR (escribe)' if aplicar else 'en seco (no escribe)'}")
    print()

    filas = leer_archivo(archivo)
    engine = create_engine(os.environ["DATABASE_URL"])
    with engine.begin() as c:
        actual = {
            id_: (tel_sol, tel_prop, cod)
            for id_, tel_sol, tel_prop, cod in c.execute(
                text(
                    "select id, corredor_solicitante_telefono, "
                    "corredor_propietario_telefono, codigo_propiedad from canjes"
                )
            ).all()
        }

        plan = planificar(filas, actual)

        canjes_a_cambiar = {c[0] for c in plan.cambios}
        print(f"filas en el archivo : {len(filas)}")
        print(f"  canjes a cambiar  : {len(canjes_a_cambiar)}")
        print(f"  ya estaban al día : {plan.ya_estaban}")
        print(f"  no existen en la app: {len(plan.inexistentes)}")
        if plan.inexistentes:
            print(f"      {', '.join(str(i) for i in sorted(plan.inexistentes)[:20])}"
                  + (" ..." if len(plan.inexistentes) > 20 else ""))
        print()

        for canje_id, campo, de, a in plan.cambios:
            print(f"  canje {canje_id:<10} {campo:<22} {de or '—':<20} -> {a or '—'}")

        if not aplicar:
            print()
            print("Nada se escribió. Para aplicar: --aplicar")
            return

        columna_por_campo = {
            "telefono_solicitante": "corredor_solicitante_telefono",
            "telefono_propietario": "corredor_propietario_telefono",
            "codigo_propiedad": "codigo_propiedad",
        }
        for canje_id, campo, _, a in plan.cambios:
            columna = columna_por_campo[campo]
            c.execute(text(f"update canjes set {columna} = :v where id = :id"), {"v": a, "id": canje_id})

        print()
        print(f"{len(canjes_a_cambiar)} canjes actualizados.")


if __name__ == "__main__":
    main()
