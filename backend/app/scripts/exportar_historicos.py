"""Exporta los datos históricos a un JSON para que una migración los cargue.

**Por qué existe.** Los 18 negocios, sus hitos y obligaciones, y los 384
movimientos del seguimiento de canjes se cargaron con scripts contra `dev` y
nunca llegaron a producción, así que allá la pantalla de Negocios está vacía y
nueve sprints de funcionalidad no tienen nada que mostrar. Una migración los
carga sola en el deploy, sin depender de que alguien tenga la credencial de la
base a mano.

**Los datos van en un archivo aparte, no dentro de la migración.** Meter 550
filas de negocios reales en el cuerpo de una migración la vuelve ilegible y
mezcla dos cosas distintas: el paso de carga y los datos que carga. Con el JSON
afuera, los datos se revisan como cualquier otro archivo.

**Todas las referencias van por código, no por id.** `alianza_id`,
`tipo_operacion_id`, `estado_id` y compañía son seriales que asignó la migración
de catálogos. Corrieron igual en las dos bases y con el mismo orden, así que los
ids *deberían* coincidir -- pero "deberían" no alcanza cuando el resultado sería
un negocio atribuido a la alianza equivocada, en silencio. Exportando el código y
resolviéndolo al insertar, ese modo de falla no existe.

**No se exportan los movimientos de la limpieza de canjes.** Producción ya tiene
los suyos, generados por la migración `a4e81b6f30c9` sobre sus propios datos;
traer los de `dev` los duplicaría.

Uso:

    python -m app.scripts.exportar_historicos
"""
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.db import engine

DESTINO = Path(__file__).resolve().parent.parent.parent / "alembic" / "datos" / "historicos.json"

MARCA_LIMPIEZA = "Cancelado en la limpieza%"


def _valor(v):
    """JSON no sabe de Decimal ni de fechas; se guardan como texto exacto."""
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def _filas(conexion, sql: str, **params) -> list[dict]:
    resultado = conexion.execute(text(sql), params)
    columnas = list(resultado.keys())
    return [
        {c: _valor(v) for c, v in zip(columnas, fila)}
        for fila in resultado.all()
    ]


def main() -> None:
    with engine.connect() as c:
        propiedades = _filas(c, """
            SELECT p.direccion, p.unidad, p.comuna,
                   tp.codigo AS tipo_propiedad, ep.codigo AS estado_propiedad
            FROM propiedades p
            LEFT JOIN catalogos tp ON tp.id = p.tipo_propiedad_id
            LEFT JOIN catalogos ep ON ep.id = p.estado_propiedad_id
            ORDER BY p.id
        """)

        negocios = _filas(c, """
            SELECT n.codigo, n.modelo, n.etapa,
                   p.direccion, p.unidad, p.comuna,
                   a.codigo AS alianza, o.codigo AS tipo_operacion,
                   n.vendedor_arrendador, n.comprador_arrendatario, n.corredor_agente,
                   n.notas, n.observaciones
            FROM negocios n
            JOIN propiedades p ON p.id = n.propiedad_id
            LEFT JOIN catalogos a ON a.id = n.alianza_id
            LEFT JOIN catalogos o ON o.id = n.tipo_operacion_id
            ORDER BY n.codigo
        """)

        hitos = _filas(c, """
            SELECT n.codigo AS negocio, h.nombre, h.fecha_inicio, h.fecha_cierre, h.estado,
                   h.valor_negocio, h.moneda, h.fecha_valorizacion, h.uf_snapshot,
                   h.valor_clp_calculado, h.valor_clp_manual, h.motivo_valor_manual,
                   h.pct_lado_vendedor, h.pct_lado_comprador, h.pct_rebate_concentrador,
                   h.pct_broker_vendedor, h.pct_broker_comprador,
                   h.pct_vp_vendedor, h.pct_vp_comprador,
                   h.pct_equipo, h.pct_tercero, h.nombre_tercero,
                   h.comision_total, h.comision_broker, h.rebate_concentrador,
                   h.comision_vp_bruta, h.comision_equipo, h.comision_tercero,
                   h.comision_real_vp,
                   mp.codigo AS motivo_perdida, h.motivo_perdida_detalle
            FROM negocio_hitos h
            JOIN negocios n ON n.id = h.negocio_id
            LEFT JOIN catalogos mp ON mp.id = h.motivo_perdida_id
            ORDER BY n.codigo, h.id
        """)

        obligaciones = _filas(c, """
            SELECT n.codigo AS negocio, h.nombre AS hito, o.tipo,
                   e.codigo AS estado, o.monto, o.fecha
            FROM negocio_obligaciones o
            JOIN negocio_hitos h ON h.id = o.hito_id
            JOIN negocios n ON n.id = h.negocio_id
            LEFT JOIN catalogos e ON e.id = o.estado_id
            ORDER BY n.codigo, h.id, o.id
        """)

        movimientos = _filas(c, """
            SELECT entity_id, tipo_movimiento, etapa_resultante, fecha, autor_id, comentario
            FROM movimientos
            WHERE entity_type = 'canje'
              AND (comentario IS NULL OR comentario NOT LIKE :marca)
            ORDER BY entity_id, fecha, id
        """, marca=MARCA_LIMPIEZA)

    datos = {
        "_nota": (
            "Generado por app/scripts/exportar_historicos.py desde la rama dev. "
            "Lo carga la migración de datos históricos. Las referencias a catálogos "
            "van por código, no por id."
        ),
        "propiedades": propiedades,
        "negocios": negocios,
        "hitos": hitos,
        "obligaciones": obligaciones,
        "movimientos_canje": movimientos,
    }

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps(datos, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    print(f"escrito: {DESTINO}")
    for clave in ("propiedades", "negocios", "hitos", "obligaciones", "movimientos_canje"):
        print(f"   {clave:<20} {len(datos[clave])}")
    print(f"   tamaño               {DESTINO.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
