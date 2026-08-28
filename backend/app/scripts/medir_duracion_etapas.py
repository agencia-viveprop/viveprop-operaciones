"""Cuanto se puede medir hoy de la duracion por etapa de los canjes, en produccion.

Solo lectura. Lee la credencial de `.env.real.bak` por su cuenta, asi que se corre
sin preparar variables de entorno:

    cd C:\\AI\\viveprop-operaciones\\backend
    .\\.venv\\Scripts\\python.exe medir_etapas_prod.py

Salida en ASCII a proposito: la consola de Windows rompe los acentos y las vinetas.
"""
import os
import pathlib
import re
import sys
from collections import defaultdict

from dotenv import load_dotenv

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

# La conexion se puede pasar por variable de entorno. Sin eso lee `.env`, que es
# la base de desarrollo: nadie corre un diagnostico contra produccion por
# accidente.
if not os.environ.get("DATABASE_URL"):
    load_dotenv(RAIZ / ".env")

from sqlalchemy import create_engine, text  # noqa: E402

motor = create_engine(os.environ["DATABASE_URL"])

with motor.connect() as cx:
    endpoint = re.search(r"@([^./]+)", os.environ["DATABASE_URL"]).group(1)
    print(f"base: {endpoint}")

    total = cx.execute(text("select count(*) from canjes")).scalar()
    movs = cx.execute(text("select count(*) from movimientos where entity_type='canje'")).scalar()
    con_etapa = cx.execute(text(
        "select count(*) from movimientos where entity_type='canje' and etapa_resultante is not null"
    )).scalar()
    con_transicion = cx.execute(text(
        "select count(distinct entity_id) from movimientos "
        "where entity_type='canje' and etapa_resultante is not null"
    )).scalar()
    print(f"canjes: {total} | movimientos de canje: {movs}")
    print(f"movimientos con etapa registrada: {con_etapa} | canjes que tienen alguna: {con_transicion}")

    print("\netapas registradas (a donde quedo el canje):")
    for etapa, cuantos, canjes in cx.execute(text(
        "select etapa_resultante, count(*), count(distinct entity_id) "
        "from movimientos where entity_type='canje' and etapa_resultante is not null "
        "group by 1 order by 2 desc"
    )):
        print(f"    {etapa:<20} {cuantos:>4} movimientos en {canjes:>3} canjes")

    # Un tramo cerrado mide "cuanto estuvo en" una etapa: desde el PRIMER
    # movimiento que la dejo ahi hasta el que la cambio. Los movimientos seguidos
    # con la misma etapa no son transiciones: cada tipo estampa su etapa.
    filas = cx.execute(text(
        "select entity_id, etapa_resultante, fecha from movimientos "
        "where entity_type='canje' and etapa_resultante is not null "
        "order by entity_id, fecha, id"
    )).all()

    tramos = defaultdict(list)
    canje_actual, etapa_actual, desde = None, None, None
    for eid, etapa, fecha in filas:
        if eid != canje_actual:
            canje_actual, etapa_actual, desde = eid, etapa, fecha
            continue
        if etapa != etapa_actual:
            tramos[etapa_actual].append(((fecha - desde).days, eid))
            etapa_actual, desde = etapa, fecha

    print("\ntramos cerrados (paso de una etapa a la siguiente):")
    if not tramos:
        print("    ninguno todavia: hace falta que un canje cambie de etapa dos veces")
    for etapa, datos in sorted(tramos.items(), key=lambda kv: -len(kv[1])):
        dias = sorted(d for d, _ in datos)
        mediana = dias[len(dias) // 2]
        promedio = round(sum(dias) / len(dias), 1)
        print(f"    {etapa:<20} {len(dias):>3} tramos | mediana {mediana:>3}d | "
              f"promedio {promedio:>5}d | de {min(dias)} a {max(dias)}d")
        print(f"        canjes: {sorted({eid for _, eid in datos})}")

    print("\nlos abiertos: cuanto llevan en su etapa actual")
    for cid, etapa, desde_fecha, dias in cx.execute(text(
        """
        select c.id, c.etapa, max(m.fecha)::date, (current_date - max(m.fecha)::date)
        from canjes c
        join movimientos m on m.entity_type='canje' and m.entity_id = c.id
                          and m.etapa_resultante is not null
        where c.estado='ACTIVO' and c.etapa <> 'CERRADO'
        group by c.id, c.etapa order by 4 desc
        """
    )):
        print(f"    #{cid:<5} {etapa:<20} desde {desde_fecha} | {dias}d")

    sin = cx.execute(text(
        """
        select count(*) from canjes c
        where c.estado='ACTIVO' and c.etapa <> 'CERRADO'
          and not exists (select 1 from movimientos m
                          where m.entity_type='canje' and m.entity_id=c.id
                            and m.etapa_resultante is not null)
        """
    )).scalar()
    print(f"    y {sin} abiertos sin ninguna etapa registrada")
