"""Borra definitivamente los canjes anteriores al corte histórico.

Pedido el 2026-08-31: *«necesito eliminar definitivamente de la app y su base de
datos, todos los canjes con fecha de solicitud o creación menores a junio 2025»*.

**Esto no se puede deshacer.** No es como la limpieza de `limpiar_canjes.py`, que
cancela y deja la línea de tiempo: acá el canje sale de la base con sus
movimientos y sus obligaciones. Por eso el simulacro es el modo por defecto y
escribir pide `--aplicar`.

**Antes de correrlo con `--aplicar` conviene tener respaldo.** Neon guarda
restauración a un punto en el tiempo y permite crear una rama del estado actual;
una rama antes del borrado es la diferencia entre un error recuperable y uno
definitivo.

**El corte no vive acá**: está en `app.services.limpieza_canjes.CORTE_HISTORICO`,
que es el mismo que usa la importación para no volver a crear lo borrado. Si el
corte viviera en este script, la próxima carga del export de Dataprop repondría
todo y el borrado duraría hasta entonces.

**Dos transportes, la misma decisión**, igual que `limpiar_canjes.py`:

- contra la base (`DATABASE_URL`), en una sola transacción: si algo falla no
  queda medio borrado aplicado;
- contra la API de un despliegue con una cookie de sesión, que va canje por canje
  y se puede cortar a la mitad --por eso se puede volver a correr--. Existe
  porque para tocar producción una cookie es una credencial mejor que el string
  de conexión: vence, se revoca cerrando sesión y no da más permisos que los de
  su usuario. El endpoint pide rol admin.

Uso:

    python -m app.scripts.borrar_canjes_antiguos                    # simulacro
    python -m app.scripts.borrar_canjes_antiguos --aplicar          # borra
    python -m app.scripts.borrar_canjes_antiguos --corte 2025-01-01

    # contra un despliegue, con la cookie session_id del navegador
    python -m app.scripts.borrar_canjes_antiguos \\
        --api https://viveprop-operaciones.onrender.com \\
        --cookie 53686d2a-... --aplicar
"""
import argparse
import sys
from collections import Counter
from datetime import date

from app.db import SessionLocal
from app.services.limpieza_canjes import (
    CORTE_HISTORICO,
    borrar_canje,
    canjes_anteriores_al_corte,
)


def _resumen(canjes) -> str:
    por_anio = Counter(
        (c.fecha_solicitud or c.creado_en).year for c in canjes
    )
    por_estado = Counter(c.estado.value for c in canjes)
    return (
        f"  por año   : {dict(sorted(por_anio.items()))}\n"
        f"  por estado: {dict(por_estado)}"
    )


def _avisos(canjes) -> list[str]:
    """Lo que conviene mirar dos veces antes de borrar.

    Un canje **activo** o **gestionado en la app** es trabajo vivo o trabajo que
    alguien hizo. El corte los alcanza igual --se pidió «todos»-- pero el
    simulacro tiene que decirlo en voz alta para que la decisión sea informada.
    """
    avisos = []
    activos = [c.id for c in canjes if c.estado.value == "ACTIVO"]
    if activos:
        avisos.append(f"  !! {len(activos)} están ACTIVOS: {activos[:20]}")
    gestionados = [c.id for c in canjes if c.gestionado_en_app]
    if gestionados:
        avisos.append(
            f"  !! {len(gestionados)} tienen gestión registrada en la app"
            f" (se borra con ellos): {gestionados[:20]}"
        )
    return avisos


def contra_la_base(corte: date, aplicar: bool) -> int:
    db = SessionLocal()
    try:
        canjes = canjes_anteriores_al_corte(db, corte)
        if not canjes:
            print(f"No hay canjes anteriores a {corte}. Nada que borrar.")
            return 0

        print(f"Canjes anteriores a {corte}: {len(canjes)}")
        print(_resumen(canjes))
        for aviso in _avisos(canjes):
            print(aviso)

        if not aplicar:
            print("\nSimulacro. Nada se borró. Agregá --aplicar para escribir.")
            return 0

        movimientos = obligaciones = 0
        for canje in canjes:
            m, o = borrar_canje(db, canje)
            movimientos += m
            obligaciones += o
        db.commit()
        print(
            f"\nBorrados {len(canjes)} canjes, {movimientos} movimientos"
            f" y {obligaciones} obligaciones."
        )
        return 0
    finally:
        db.close()


def contra_la_api(base: str, cookie: str, corte: date, aplicar: bool) -> int:
    """Va canje por canje contra `DELETE /api/canjes/{id}`.

    Lista con el filtro del listado y descarta en el cliente: el endpoint de
    listado no filtra por fecha, y agregarle un filtro solo para esto sería
    ensanchar la API pública por una limpieza de una vez.
    """
    import json
    import urllib.error
    import urllib.request

    def pedir(metodo: str, ruta: str):
        req = urllib.request.Request(
            f"{base.rstrip('/')}{ruta}",
            method=metodo,
            headers={"Cookie": f"session_id={cookie}"},
        )
        with urllib.request.urlopen(req) as res:
            cuerpo = res.read()
            return json.loads(cuerpo) if cuerpo else None

    try:
        # El listado no pagina ni acepta un tope, así que trae todo lo que la app
        # muestra; el corte se aplica acá.
        filas = pedir("GET", "/api/canjes")
    except urllib.error.HTTPError as exc:
        print(f"No se pudo listar: {exc.code} {exc.reason}", file=sys.stderr)
        return 1

    limite = corte.isoformat()
    objetivo = [
        f for f in filas if (f.get("fecha_solicitud") or "")[:10] < limite
    ]
    print(f"Canjes anteriores a {corte} en el despliegue: {len(objetivo)}")
    if not objetivo:
        return 0
    print(f"  ids: {[f['id'] for f in objetivo][:30]}{' ...' if len(objetivo) > 30 else ''}")

    if not aplicar:
        print("\nSimulacro. Nada se borró. Agregá --aplicar para escribir.")
        return 0

    borrados, fallidos = 0, []
    for fila in objetivo:
        try:
            pedir("DELETE", f"/api/canjes/{fila['id']}")
            borrados += 1
        except urllib.error.HTTPError as exc:
            fallidos.append(f"#{fila['id']}: {exc.code} {exc.reason}")

    print(f"\nBorrados {borrados} de {len(objetivo)}.")
    for f in fallidos:
        print(f"  falló {f}", file=sys.stderr)
    return 1 if fallidos else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="escribe; sin esto es simulacro")
    parser.add_argument(
        "--corte",
        type=lambda s: date.fromisoformat(s),
        default=CORTE_HISTORICO,
        help=f"borra los anteriores a esta fecha (por defecto {CORTE_HISTORICO})",
    )
    parser.add_argument("--api", help="URL del despliegue, para ir por la API")
    parser.add_argument("--cookie", help="valor de session_id, con --api")
    args = parser.parse_args()

    if args.api:
        if not args.cookie:
            print("--api necesita --cookie", file=sys.stderr)
            return 2
        return contra_la_api(args.api, args.cookie, args.corte, args.aplicar)
    return contra_la_base(args.corte, args.aplicar)


if __name__ == "__main__":
    raise SystemExit(main())
