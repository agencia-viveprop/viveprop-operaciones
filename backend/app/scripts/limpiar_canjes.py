"""Deja vigentes solo los canjes de una lista y cancela todo el resto.

Pedido el 2026-08-21: en Dataprop quedan seis solicitudes vivas y la base
arrastra 225 activas, así que la app muestra como pendiente trabajo que no
existe. Esto la alinea con la realidad.

**Cancela todo lo que no esté en la lista, incluidos los 31 que tienen etapa
CERRADO.** Se advirtió que marcar como cancelado algo cuya etapa dice que se
concretó pierde la distinción entre "se cayó" y "se concluyó", y la decisión fue
cancelarlos igual. **La etapa no se toca**, así que esa información sigue
guardada y el cambio es reversible: los cancelados por esta limpieza son los que
tienen un movimiento con el comentario de abajo.

**Va por el mismo camino que la app.** Cancelar en la app es registrar un
movimiento `CANCELACION`, que pone el estado y marca `gestionado_en_app`. Acá se
hace lo mismo, en una sola transacción en vez de 221: si algo falla a mitad de
camino no queda media limpieza aplicada. Por eso no se llama a
`crear_movimiento_canje`, que hace `commit` por llamada.

**El movimiento no es decoración.** Sin él, alguien que abra el canje #150 en
seis meses ve CANCELADO sin ninguna explicación de por qué. Con él, la línea de
tiempo dice qué pasó y cuándo.

**La limpieza sobrevive a las importaciones.** El importador de Dataprop nunca
toca `estado` ni `etapa`, y además salta los canjes con `gestionado_en_app`. Así
que volver a subir un .xlsx viejo no revive lo cancelado.

**Dos transportes, la misma decisión.** Contra la base directo (`DATABASE_URL`)
o contra la API de un despliegue con una cookie de sesión. La segunda existe
porque para tocar producción una cookie es una credencial mejor que el string de
conexión: vence, se revoca cerrando sesión, y no da más permisos que los del
usuario. El costo es que va canje por canje, así que se puede cortar a medias --
por eso saltea los que ya están cancelados y se puede volver a correr.

Uso:

    python -m app.scripts.limpiar_canjes                 # simulacro contra la base
    python -m app.scripts.limpiar_canjes --aplicar       # escribe en la base
    python -m app.scripts.limpiar_canjes 334 344 --aplicar

    # contra un despliegue, con la cookie session_id del navegador
    python -m app.scripts.limpiar_canjes --api https://viveprop-operaciones.onrender.com         --cookie 53686d2a-... --aplicar
"""
import argparse
import sys
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.canje import Canje, CanjeEstado
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.usuario import RolUsuario, Usuario

# Las solicitudes que siguen vivas en Dataprop al 2026-08-21.
VIGENTES_POR_DEFECTO = (334, 344, 359, 360, 364, 367)

TIPO = "CANCELACION"
COMENTARIO = (
    "Cancelado en la limpieza del 2026-08-21: no estaba entre las solicitudes "
    "vigentes en Dataprop."
)


def _informe(db: Session, vigentes: set[int]) -> list[Canje]:
    """Imprime qué se cancelaría y devuelve la lista."""
    activos = db.execute(
        select(Canje).where(Canje.estado == CanjeEstado.ACTIVO).order_by(Canje.id)
    ).scalars().all()
    a_cancelar = [c for c in activos if c.id not in vigentes]

    print(f"canjes en la base: {db.query(Canje).count()}")
    print(f"activos hoy:       {len(activos)}")
    print(f"se cancelarian:    {len(a_cancelar)}")
    print(f"quedarian activos: {len(activos) - len(a_cancelar)}")

    print("\npor etapa:")
    for etapa, n in Counter(c.etapa.value for c in a_cancelar).most_common():
        print(f"   {etapa:<22} {n}")

    print("\nlos que quedan vigentes:")
    for cid in sorted(vigentes):
        canje = db.get(Canje, cid)
        if canje is None:
            print(f"   #{cid}: NO EXISTE en la base -- hay que importarlo de Dataprop")
        else:
            print(f"   #{cid}: {canje.etapa.value:<20} {canje.corredor_solicitante_nombre or ''}")

    return a_cancelar


def _cancelar(db: Session, canjes: list[Canje], autor_id: int | None, ahora: datetime) -> int:
    tipo = db.get(TipoMovimiento, TIPO)
    if tipo is None or tipo.entity_type != EntityType.canje:
        raise SystemExit(f"No existe el tipo de movimiento '{TIPO}' para canjes.")

    for canje in canjes:
        db.add(Movimiento(
            entity_type=EntityType.canje,
            entity_id=canje.id,
            tipo_movimiento=tipo.codigo,
            # Nulo en CANCELACION: la etapa se conserva a propósito, así que
            # despues se puede saber en qué punto estaba cada uno.
            etapa_resultante=tipo.etapa_resultante,
            autor_id=autor_id,
            comentario=COMENTARIO,
            fecha=ahora,
        ))
        canje.estado = CanjeEstado.CANCELADO
        # Lo mismo que hace la app: sin esto, una importación posterior volvería
        # a pisar los datos del canje.
        canje.gestionado_en_app = True

    db.commit()
    return len(canjes)


# ------------------------------------------------------- contra la API


def _por_api(base: str, cookie: str, vigentes: set[int], aplicar: bool) -> None:
    """Lo mismo pero contra un despliegue, usando su propia API.

    Cada cancelación es un POST de movimiento: el mismo endpoint que usa el botón
    de la app, así que no hay forma de que esto haga algo que la app no haría.
    """
    import httpx

    base = base.rstrip("/")
    with httpx.Client(cookies={"session_id": cookie}, timeout=30.0) as cliente:
        respuesta = cliente.get(f"{base}/api/canjes")
        if respuesta.status_code == 401:
            raise SystemExit("La cookie no sirve o venció. Volvé a copiarla del navegador.")
        respuesta.raise_for_status()
        canjes = respuesta.json()

    activos = [c for c in canjes if c["estado"] == "ACTIVO"]
    a_cancelar = [c for c in activos if c["id"] not in vigentes]

    print(f"canjes en {base}: {len(canjes)}")
    print(f"activos hoy:       {len(activos)}")
    print(f"se cancelarian:    {len(a_cancelar)}")
    print("\npor etapa:")
    for etapa, n in Counter(c["etapa"] for c in a_cancelar).most_common():
        print(f"   {etapa:<22} {n}")

    print("\nlos que quedan vigentes:")
    presentes = {c["id"] for c in canjes}
    for cid in sorted(vigentes):
        if cid not in presentes:
            print(f"   #{cid}: NO EXISTE alla -- hay que importarlo de Dataprop")
        else:
            c = next(x for x in canjes if x["id"] == cid)
            print(f"   #{cid}: {c['etapa']:<20} {c.get('corredor_solicitante_nombre') or ''}")

    if not aplicar:
        print("\n[simulacro] no se escribió nada. Agregá --aplicar para hacerlo.")
        return

    fallidos: list[tuple[int, str]] = []
    with httpx.Client(cookies={"session_id": cookie}, timeout=30.0) as cliente:
        for i, canje in enumerate(a_cancelar, start=1):
            r = cliente.post(
                f"{base}/api/canjes/{canje['id']}/movimientos",
                json={"tipo_movimiento": TIPO, "comentario": COMENTARIO},
            )
            if r.status_code >= 400:
                fallidos.append((canje["id"], f"{r.status_code} {r.text[:120]}"))
            if i % 25 == 0:
                print(f"   {i}/{len(a_cancelar)}...")

    print(f"\nlisto: {len(a_cancelar) - len(fallidos)} cancelados, {len(fallidos)} con error.")
    for cid, motivo in fallidos[:10]:
        print(f"   #{cid}: {motivo}", file=sys.stderr)
    if fallidos:
        print("   volver a correr el script retoma solo lo que quedó activo.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vigentes", nargs="*", type=int,
                        help=f"IDs que quedan vigentes (por defecto {list(VIGENTES_POR_DEFECTO)})")
    parser.add_argument("--aplicar", action="store_true",
                        help="Escribe los cambios. Sin esto solo simula.")
    parser.add_argument("--api", help="URL del despliegue, para ir por la API en vez de la base.")
    parser.add_argument("--cookie", help="Valor de la cookie session_id. Va con --api.")
    args = parser.parse_args()

    vigentes = set(args.vigentes or VIGENTES_POR_DEFECTO)

    if args.api or args.cookie:
        if not (args.api and args.cookie):
            raise SystemExit("--api y --cookie van juntos.")
        print(f"vigentes segun la lista: {sorted(vigentes)}\n")
        _por_api(args.api, args.cookie, vigentes, args.aplicar)
        return

    with SessionLocal() as db:
        print(f"vigentes segun la lista: {sorted(vigentes)}\n")
        a_cancelar = _informe(db, vigentes)

        if not args.aplicar:
            print("\n[simulacro] no se escribió nada. Agregá --aplicar para hacerlo.")
            return

        if not a_cancelar:
            print("\nNo hay nada que cancelar.")
            return

        autor = db.execute(
            select(Usuario).where(Usuario.rol == RolUsuario.admin).order_by(Usuario.id)
        ).scalars().first()
        ahora = datetime.now(timezone.utc)

        n = _cancelar(db, a_cancelar, autor.id if autor else None, ahora)
        print(f"\nlisto: {n} canjes cancelados, con su movimiento en la línea de tiempo.")

        quedan = db.execute(
            select(Canje.id).where(Canje.estado == CanjeEstado.ACTIVO)
        ).scalars().all()
        print(f"activos que quedan: {sorted(quedan)}")
        esperados = sorted(cid for cid in vigentes if db.get(Canje, cid) is not None)
        if sorted(quedan) != esperados:
            print(f"  OJO: se esperaba {esperados}. Revisar.", file=sys.stderr)


if __name__ == "__main__":
    main()
